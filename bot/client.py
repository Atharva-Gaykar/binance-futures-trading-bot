"""
Binance Futures Testnet client wrapper.Handles authentication and raw API calls, isolated from order logic and CLI.
"""

import os
import time
from typing import Optional

from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceRequestException
from dotenv import load_dotenv

from bot.logging_config import logger

load_dotenv()

testnet_base_url = os.getenv(
    "BINANCE_TESTNET_BASE_URL", "https://testnet.binancefuture.com/fapi"
)


class BinanceFuturesClient:
    """
    Thin wrapper around python-binance's Client, scoped to Futures Testnet
    (USDT-M). Responsible only for auth + raw order placement — no business
    logic, no validation (that lives in validators.py / orders.py).
    """

    def __init__(self):
        api_key = os.getenv("BINANCE_API_KEY")
        api_secret = os.getenv("BINANCE_API_SECRET")

        if not api_key or not api_secret:
            logger.error("Missing BINANCE_API_KEY or BINANCE_API_SECRET in environment")
            raise EnvironmentError(
                "BINANCE_API_KEY and BINANCE_API_SECRET must be set in .env"
            )

        try:
            self.client = Client(api_key, api_secret, testnet=True)
            self.client.FUTURES_URL = testnet_base_url

            # Correct for local clock drift vs Binance server time
            server_time = self.client.futures_time()["serverTime"]
            local_time = int(time.time() * 1000)
            self.client.timestamp_offset = server_time - local_time

            logger.info(
                f"Binance Futures Testnet client initialized successfully "
                f"(timestamp_offset={self.client.timestamp_offset}ms)"
            )
        except Exception as e:
            logger.error(f"Failed to initialize Binance client: {e}")
            raise

    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: Optional[float] = None,
        stop_price: Optional[float] = None,
        time_in_force: str = "GTC",
    ) -> dict:
        """
        Places a raw order on Binance Futures Testnet. Routes conditional
        stop orders (STOP, STOP_MARKET, TAKE_PROFIT, TAKE_PROFIT_MARKET) to
        the Algo Order endpoint, per Binance's mandatory migration. MARKET
        and LIMIT orders stay on the standard order endpoint.
        """
        is_algo_order = order_type in (
            "STOP", "STOP_MARKET", "TAKE_PROFIT", "TAKE_PROFIT_MARKET"
        )

        if is_algo_order:
            params = {
                "symbol": symbol,
                "side": side,
                "type": order_type,
                "quantity": quantity,
                "triggerPrice": stop_price,
            }
            if price is not None:
                params["price"] = price
            if order_type == "STOP":
                params["timeInForce"] = time_in_force

            logger.info(f"Sending Conditional ALGO order request to Binance: {params}")

            try:
                response = self.client.futures_create_algo_order(**params)
                logger.info(f"Algo order response received: {response}")
                return response

            except BinanceAPIException as e:
                logger.error(f"Binance Algo API error: {e.status_code} - {e.message}")
                raise

            except BinanceRequestException as e:
                logger.error(f"Binance Algo request error: {e}")
                raise

            except Exception as e:
                logger.error(f"Unexpected error while placing algo order: {e}")
                raise

        else:
            params = {
                "symbol": symbol,
                "side": side,
                "type": order_type,
                "quantity": quantity,
            }
            if price is not None:
                params["price"] = price
            if order_type == "LIMIT":
                params["timeInForce"] = time_in_force

            logger.info(f"Sending Standard order request to Binance: {params}")

            try:
                response = self.client.futures_create_order(**params)
                logger.info(f"Order response received: {response}")
                return response

            except BinanceAPIException as e:
                logger.error(f"Binance API error: {e.status_code} - {e.message}")
                raise

            except BinanceRequestException as e:
                logger.error(f"Binance request error (network/malformed request): {e}")
                raise

            except Exception as e:
                logger.error(f"Unexpected error while placing order: {e}")
                raise

    def get_order_status(self, symbol: str, order_id: int) -> dict:
        """
        Queries the current status of a previously placed order.
        Useful for confirming fill status after MARKET orders.
        """
        logger.info(f"Querying order status: symbol={symbol}, orderId={order_id}")
        try:
            response = self.client.futures_get_order(symbol=symbol, orderId=order_id)
            logger.info(f"Order status response: {response}")
            return response
        except (BinanceAPIException, BinanceRequestException) as e:
            logger.error(f"Failed to query order status: {e}")
            raise