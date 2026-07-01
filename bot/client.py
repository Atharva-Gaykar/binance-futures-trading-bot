"""
Binance Futures Testnet client wrapper.
Handles authentication and raw API calls, isolated from order logic and CLI.
"""

import os
from typing import Optional

from binance.client import Client
from binance.exceptions import BinanceAPIException, BinanceRequestException
from dotenv import load_dotenv

from bot.logging_config import logger

load_dotenv()


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
            # Point the underlying session at the Futures Testnet base URL
            self.client.FUTURES_URL = "https://testnet.binancefuture.com/fapi"
            logger.info("Binance Futures Testnet client initialized successfully")
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
        Places a raw order on Binance Futures Testnet. Returns the raw API
        response dict. Raises on API or network failure — caller handles that.
        """
        params = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": quantity,
        }

        if price is not None:
            params["price"] = price
        if stop_price is not None:
            params["stopPrice"] = stop_price
        if order_type in ("LIMIT", "STOP"):
            params["timeInForce"] = time_in_force

        logger.info(f"Sending order request to Binance: {params}")

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