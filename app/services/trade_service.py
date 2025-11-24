from binance import AsyncClient
from binance.enums import (
    FUTURE_ORDER_TYPE_MARKET,
    ORDER_TYPE_LIMIT,
    TIME_IN_FORCE_GTC,
    SIDE_BUY,
    SIDE_SELL,
    ORDER_TYPE_STOP_LOSS_LIMIT,
)
import binance
# from loguru import Logger

from app.core.config import settings


class TradeService:
    def __init__(
        self,
        logger,
        testnet: bool = settings.TESTNET,
        api_key: str = settings.API_KEY,
        secret_key: str = settings.SECRET_KEY,
    ):
        self.logger = logger
        self.testnet: bool = testnet
        self.api_key: str = api_key
        self.secret_key: str = secret_key
        self.client = None

    async def __aenter__(self):
        if self.testnet:
            self.client = await AsyncClient.create(
                self.api_key, self.secret_key, testnet=True
            )
            self.logger.info("Connected to Binance Futures TESTNET")
        else:
            self.client = await AsyncClient.create(self.api_key, self.secret_key)
            self.logger.warning("Connected to REAL Binance Futures - USE WITH CAUTION")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.close_connection()
        self.logger.info("Connection Closed")

    async def place_futures_market_order(self, symbol: str, side: str, quantity: float):
        """
        Place a MARKET order (executes immediately at current price)

        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            side: 'BUY' or 'SELL'
            quantity: Amount to trade (e.g., 0.001 BTC)

        Returns:
            Order response dict
        """
        try:
            if side not in [SIDE_BUY, SIDE_SELL]:
                raise ValueError(f"Invalid SIDE: {side}. Must be 'BUY' or 'SELL'")

            self.logger.info(f"Placing MARKET {side} order: {quantity} {symbol}")

            order = await self.client.futures_create_order(
                symbol=symbol,
                side=side,  # 'BUY' or 'SELL'
                type=FUTURE_ORDER_TYPE_MARKET,
                quantity=quantity,
            )

            self.logger.bind(trade=True).info(
                f"MARKET {side} | {symbol} | Qty: {quantity} | "
                f"Order ID: {order['orderId']} | Status: {order['status']}"
            )

            return order

        except Exception as e:
            self.logger.error(f"Market order failed: {e}")
            raise

    async def place_futures_limit_order(
        self, symbol: str, side: binance.enums, quantity: float, price: float
    ):
        """
        Place a LIMIT order (execute at specified price of better)

        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            side: 'BUY' or 'SELL'
            quantity: Amount to trade (e.g., 0.001 BTC)
            price: Limit Price (e.g., 1000.00)

        Returns:
            Order response dict
        """
        try:
            if side not in [SIDE_BUY, SIDE_SELL]:
                raise ValueError(f"Invalid SIDE: {side}. Must be 'BUY' or 'SELL'")

            self.logger.info(
                f"Placing LIMIT {side} order: {quantity} {symbol} at {price}"
            )
            order = await self.client.futures_create_order(
                symbol=symbol,
                side=side,
                type=ORDER_TYPE_LIMIT,
                timeInForce=TIME_IN_FORCE_GTC,  # Good Till Canceled
                quantity=quantity,
                price=price,
            )

            self.logger.bind(trade=True).info(
                f"LIMIT {side} | {symbol} | Qty: {quantity} | Price: ${price} | "
                f"Order ID: {order['orderId']} | Status: {order['status']}"
            )

            return order

        except Exception as e:
            self.logger.error(f"Limit order failed: {e}")
            raise

    async def place_stop_limit_order(
        self, symbol: str, side: str, quantity: float, price: float, stop_price: float
    ):
        """
        Place a STOP_LIMIT order

        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            side: 'BUY' or 'SELL'
            quantity: Amount to trade (e.g., 0.001 BTC)
            price: Max Price to Pay
            stop_price: Trigger Price

        Returns:
            Order response dict
        """
        try:
            if side not in [SIDE_BUY, SIDE_SELL]:
                raise ValueError(f"Invalid SIDE: {side}. Must be 'BUY' or 'SELL'")

            self.logger.info(
                f"Placing STOP_LIMIT {side} order: {quantity} {symbol} at {price} and stop price at {stop_price}"
            )

            order = await self.client.create_order(
                symbol=symbol,
                side=side,  # 'BUY' or 'SELL'
                type=ORDER_TYPE_STOP_LOSS_LIMIT,
                quantity=quantity,
                price=price,
                stopPrice=stop_price,
            )

            self.logger.bind(trade=True).info(
                f"STOP_LIMIT {side} | {symbol} | Qty: {quantity} | "
                f"Price: {price} | Stop Price : {stop_price}"
                f"Order ID: {order['orderId']} | Status: {order['status']}"
            )

            return order

        except Exception as e:
            self.logger.error(f"Market order failed: {e}")
            raise

    async def get_current_price(self, symbol):
        """Get current market price for a symbol"""
        try:
            ticker = await self.client.futures_symbol_ticker(symbol=symbol)
            price = float(ticker["price"])
            self.logger.info(f"Current price for {symbol}: ${price}")
            return price
        except Exception as e:
            self.logger.error(f"Failed to get price: {e}")
            raise

    async def get_account_balance(self):
        """Get futures account balance"""
        try:
            account = await self.client.futures_account()
            balance = float(account["totalWalletBalance"])
            self.logger.info(f"Account balance: ${balance:.2f} USDT")
            return balance
        except Exception as e:
            self.logger.error(f"Failed to get balance: {e}")
            raise

    async def cancel_order(self, symbol, order_id):
        """Cancel an open order"""
        try:
            result = await self.client.futures_cancel_order(
                symbol=symbol, orderId=order_id
            )
            self.logger.info(f"Order {order_id} canceled successfully")
            return result
        except Exception as e:
            self.logger.error(f"Failed to cancel order: {e}")
            raise

    async def get_open_orders(self, symbol=None):
        """Get all open orders"""
        try:
            orders = await self.client.futures_get_open_orders(symbol=symbol)
            self.logger.info(f"Found {len(orders)} open orders")
            return orders
        except Exception as e:
            self.logger.error(f"Failed to get open orders: {e}")
            raise

    async def get_position_info(self, symbol=None):
        """Get current position information"""
        try:
            positions = await self.client.futures_position_information(symbol=symbol)
            self.logger.info(
                f"Position info retrieved for {symbol if symbol else 'all symbols'}"
            )
            return positions
        except Exception as e:
            self.logger.error(f"Failed to get position info: {e}")
            raise
