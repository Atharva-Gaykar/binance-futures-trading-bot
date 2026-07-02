"""
CLI entry point for the Binance Futures Testnet trading bot.
Usage:
    python cli.py place-order --symbol BTCUSDT --side BUY --order-type MARKET --quantity 0.01
    python cli.py place-order --symbol BTCUSDT --side SELL --order-type LIMIT --quantity 0.01 --price 60000
    python cli.py place-order --symbol BTCUSDT --side BUY --order-type STOP_LIMIT --quantity 0.01 --price 60000 --stop-price 59500
"""

from typing import Optional
import typer
from pydantic import ValidationError
from bot.logging_config import logger
from bot.orders import OrderExecutionError, place_order
from bot.validators import OrderRequest, OrderSide, OrderType

app = typer.Typer(help="Simplified Trading Bot for Binance Futures Testnet (USDT-M)")

@app.callback()
def callback():
    """
    Binance Futures Testnet Trading Bot CLI.
    """
    pass


@app.command("place-order")
def place_order_command(
    symbol: str = typer.Option(..., "--symbol", help="Trading pair, e.g. BTCUSDT"),
    side: OrderSide = typer.Option(..., "--side", help="BUY or SELL"),
    order_type: OrderType = typer.Option(
        ..., "--order-type", help="MARKET, LIMIT, or STOP_LIMIT"
    ),
    quantity: float = typer.Option(..., "--quantity", help="Order quantity"),
    price: Optional[float] = typer.Option(
        None, "--price", help="Required for LIMIT and STOP_LIMIT orders"
    ),
    stop_price: Optional[float] = typer.Option(
        None, "--stop-price", help="Required for STOP_LIMIT orders"
    ),
):
    """
    Validate input and place an order on Binance Futures Testnet.
    """
    try:
        order = OrderRequest(
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
            stop_price=stop_price,
        )
    except ValidationError as e:
        typer.echo("Invalid input:")
        for err in e.errors():
            typer.echo(f"  - {err['msg']}")
        logger.error(f"Input validation failed: {e.errors()}")
        raise typer.Exit(code=1)

    try:
        place_order(order)
    except OrderExecutionError:
        # already logged and printed inside orders.py
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()