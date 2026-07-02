"""Order placement logic — bridges validated input (validators.py) to the
Binance client (client.py). Formats request/response summaries for CLI output.
"""
import time
from binance.exceptions import BinanceAPIException, BinanceRequestException
from bot.client import BinanceFuturesClient
from bot.logging_config import logger
from bot.validators import OrderRequest, OrderType

# Maps our internal OrderType enum to the exact order type string
# Binance Futures API expects in the REST payload.
BINANCE_ORDER_TYPE_MAP = {
    OrderType.MARKET: "MARKET",
    OrderType.LIMIT: "LIMIT",
    OrderType.STOP_LIMIT: "STOP",  # Binance Futures uses "STOP" for stop-limit
}


class OrderExecutionError(Exception):
    """Raised when an order fails to execute, wraps the underlying cause."""
    pass


def print_request_summary(order: OrderRequest) -> None:
    print("\n--- Order Request Summary ---")
    print(f"Symbol      : {order.symbol}")
    print(f"Side        : {order.side.value}")
    print(f"Type        : {order.order_type.value}")
    print(f"Quantity    : {order.quantity}")
    if order.price is not None:
        print(f"Price       : {order.price}")
    if order.stop_price is not None:
        print(f"Stop Price  : {order.stop_price}")
    print("------------------------------\n")


def print_response_summary(response: dict) -> None:
    print("--- Order Response ---")

    # Algo orders (STOP/STOP_MARKET/etc.) use algoId/algoStatus instead of orderId/status
    order_id = response.get("orderId", response.get("algoId"))
    status = response.get("status", response.get("algoStatus"))

    print(f"Order ID     : {order_id}")
    print(f"Status       : {status}")

    executed_qty = response.get("executedQty")
    if executed_qty is not None:
        print(f"Executed Qty : {executed_qty}")

    avg_price = response.get("avgPrice")
    if avg_price is not None:
        print(f"Avg Price    : {avg_price}")

    print("----------------------\n")


def place_order(order: OrderRequest) -> dict:
    """
    Takes a validated OrderRequest, places it via the Binance client,
    prints request/response summaries, and returns the raw response.
    Raises OrderExecutionError on failure.
    """
    print_request_summary(order)
    logger.info(f"Placing {order.order_type.value} order: {order.model_dump()}")

    client = BinanceFuturesClient()
    binance_order_type = BINANCE_ORDER_TYPE_MAP[order.order_type]

    try:
        response = client.place_order(
            symbol=order.symbol,
            side=order.side.value,
            order_type=binance_order_type,
            quantity=order.quantity,
            price=order.price,
            stop_price=order.stop_price,
        )

        if order.order_type == OrderType.MARKET:
            # For MARKET orders, wait a moment and query the order status to get fill details
            time.sleep(1)  # brief pause to allow Binance to process the order
            order_id = response.get("orderId")
            if order_id is not None:
                response = client.get_order_status(symbol=order.symbol, order_id=order_id)

        print_response_summary(response)
        print(f"SUCCESS: {order.order_type.value} order placed for {order.symbol}\n")
        logger.info(f"Order placed successfully: orderId={response.get('orderId', response.get('algoId'))}")

        return response

    except BinanceAPIException as e:
        print(f"FAILED: Binance rejected the order — {e.message}\n")
        logger.error(f"Order failed (API error): {e.status_code} - {e.message}")
        raise OrderExecutionError(f"Binance API error: {e.message}") from e

    except BinanceRequestException as e:
        print(f"FAILED: Network/request error — {e}\n")
        logger.error(f"Order failed (request error): {e}")
        raise OrderExecutionError(f"Request error: {e}") from e

    except Exception as e:
        print(f"FAILED: Unexpected error — {e}\n")
        logger.error(f"Order failed (unexpected error): {e}")
        raise OrderExecutionError(f"Unexpected error: {e}") from e