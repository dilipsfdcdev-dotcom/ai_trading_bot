"""MT5 Connector - Main interface for MetaTrader 5 operations"""
import MetaTrader5 as mt5
from datetime import datetime, timedelta
from typing import List, Optional, Dict
import pandas as pd
import logging
from .models import (
    Trade, Position, TickData, OrderType, TradeStatus,
    AccountInfo, TimeFrame, MarketData
)

logger = logging.getLogger(__name__)


class MT5Connector:
    """
    MetaTrader 5 Connector for automated trading
    Handles all MT5 operations: connection, data retrieval, and trade execution
    """

    def __init__(self, login: int, password: str, server: str, path: Optional[str] = None):
        """
        Initialize MT5 connector

        Args:
            login: MT5 account login
            password: MT5 account password
            server: MT5 server name
            path: Path to MT5 terminal (optional, auto-detect on Windows)
        """
        self.login = login
        self.password = password
        self.server = server
        self.path = path
        self.connected = False

    def connect(self) -> bool:
        """
        Connect to MT5 terminal

        Returns:
            bool: True if connected successfully
        """
        try:
            # Initialize MT5
            if self.path:
                if not mt5.initialize(path=self.path):
                    logger.error(f"MT5 initialize failed: {mt5.last_error()}")
                    return False
            else:
                if not mt5.initialize():
                    logger.error(f"MT5 initialize failed: {mt5.last_error()}")
                    return False

            # Login to account
            if not mt5.login(self.login, password=self.password, server=self.server):
                logger.error(f"MT5 login failed: {mt5.last_error()}")
                mt5.shutdown()
                return False

            self.connected = True
            logger.info(f"Connected to MT5: {self.server}, Account: {self.login}")
            return True

        except Exception as e:
            logger.error(f"MT5 connection error: {str(e)}")
            return False

    def disconnect(self):
        """Disconnect from MT5"""
        if self.connected:
            mt5.shutdown()
            self.connected = False
            logger.info("Disconnected from MT5")

    def is_connected(self) -> bool:
        """Check if connected to MT5"""
        return self.connected and mt5.terminal_info() is not None

    def get_account_info(self) -> Optional[AccountInfo]:
        """
        Get current account information

        Returns:
            AccountInfo: Account details or None if error
        """
        if not self.is_connected():
            logger.error("Not connected to MT5")
            return None

        try:
            info = mt5.account_info()
            if info is None:
                return None

            return AccountInfo(
                balance=info.balance,
                equity=info.equity,
                margin=info.margin,
                free_margin=info.margin_free,
                margin_level=info.margin_level if info.margin > 0 else 0,
                profit=info.profit,
                currency=info.currency,
                leverage=info.leverage,
                name=info.name,
                server=info.server
            )
        except Exception as e:
            logger.error(f"Error getting account info: {str(e)}")
            return None

    def get_tick_data(self, symbol: str) -> Optional[TickData]:
        """
        Get current tick data for symbol

        Args:
            symbol: Trading symbol (e.g., 'EURUSD')

        Returns:
            TickData: Current tick or None if error
        """
        if not self.is_connected():
            logger.error("Not connected to MT5")
            return None

        try:
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                logger.error(f"Failed to get tick for {symbol}")
                return None

            return TickData(
                symbol=symbol,
                bid=tick.bid,
                ask=tick.ask,
                last=tick.last,
                volume=tick.volume,
                time=datetime.fromtimestamp(tick.time),
                spread=(tick.ask - tick.bid)
            )
        except Exception as e:
            logger.error(f"Error getting tick data: {str(e)}")
            return None

    def get_market_data(
        self,
        symbol: str,
        timeframe: TimeFrame,
        count: int = 1000
    ) -> Optional[pd.DataFrame]:
        """
        Get historical market data (OHLCV)

        Args:
            symbol: Trading symbol
            timeframe: Timeframe (M1, M5, H1, etc.)
            count: Number of bars to retrieve

        Returns:
            DataFrame: Market data with OHLCV columns
        """
        if not self.is_connected():
            logger.error("Not connected to MT5")
            return None

        try:
            # Map timeframe to MT5 constant
            tf_map = {
                TimeFrame.M1: mt5.TIMEFRAME_M1,
                TimeFrame.M5: mt5.TIMEFRAME_M5,
                TimeFrame.M15: mt5.TIMEFRAME_M15,
                TimeFrame.M30: mt5.TIMEFRAME_M30,
                TimeFrame.H1: mt5.TIMEFRAME_H1,
                TimeFrame.H4: mt5.TIMEFRAME_H4,
                TimeFrame.D1: mt5.TIMEFRAME_D1,
                TimeFrame.W1: mt5.TIMEFRAME_W1
            }

            mt5_timeframe = tf_map.get(timeframe, mt5.TIMEFRAME_H1)

            # Get rates
            rates = mt5.copy_rates_from_pos(symbol, mt5_timeframe, 0, count)
            if rates is None or len(rates) == 0:
                logger.error(f"Failed to get rates for {symbol}")
                return None

            # Convert to DataFrame
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            df.set_index('time', inplace=True)

            return df

        except Exception as e:
            logger.error(f"Error getting market data: {str(e)}")
            return None

    def open_trade(
        self,
        symbol: str,
        order_type: OrderType,
        volume: float,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        comment: str = "",
        magic_number: int = 12345
    ) -> Optional[Trade]:
        """
        Open a new trade

        Args:
            symbol: Trading symbol
            order_type: Buy or Sell
            volume: Trade volume (lots)
            stop_loss: Stop loss price (optional)
            take_profit: Take profit price (optional)
            comment: Trade comment
            magic_number: Magic number for identification

        Returns:
            Trade: Executed trade or None if failed
        """
        if not self.is_connected():
            logger.error("Not connected to MT5")
            return None

        try:
            # Get symbol info
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                logger.error(f"Symbol {symbol} not found")
                return None

            # Check if symbol is available
            if not symbol_info.visible:
                if not mt5.symbol_select(symbol, True):
                    logger.error(f"Failed to select symbol {symbol}")
                    return None

            # Get current price
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                logger.error(f"Failed to get tick for {symbol}")
                return None

            # Determine order type and price
            if order_type == OrderType.BUY:
                price = tick.ask
                mt5_order_type = mt5.ORDER_TYPE_BUY
            elif order_type == OrderType.SELL:
                price = tick.bid
                mt5_order_type = mt5.ORDER_TYPE_SELL
            else:
                logger.error(f"Unsupported order type: {order_type}")
                return None

            # Prepare request
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": volume,
                "type": mt5_order_type,
                "price": price,
                "deviation": 20,
                "magic": magic_number,
                "comment": comment,
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }

            # Add SL/TP if provided
            if stop_loss:
                request["sl"] = stop_loss
            if take_profit:
                request["tp"] = take_profit

            # Send order
            result = mt5.order_send(request)
            if result is None:
                logger.error(f"Order send failed: {mt5.last_error()}")
                return None

            if result.retcode != mt5.TRADE_RETCODE_DONE:
                logger.error(f"Order failed: {result.comment}")
                return None

            # Create trade object
            trade = Trade(
                ticket=result.order,
                symbol=symbol,
                order_type=order_type,
                volume=volume,
                entry_price=result.price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                comment=comment,
                magic_number=magic_number,
                status=TradeStatus.OPEN,
                open_time=datetime.now()
            )

            logger.info(f"Trade opened: {trade.ticket} - {symbol} {order_type.value} {volume} @ {result.price}")
            return trade

        except Exception as e:
            logger.error(f"Error opening trade: {str(e)}")
            return None

    def close_trade(self, ticket: int) -> bool:
        """
        Close an open position

        Args:
            ticket: Position ticket number

        Returns:
            bool: True if closed successfully
        """
        if not self.is_connected():
            logger.error("Not connected to MT5")
            return False

        try:
            # Get position info
            position = mt5.positions_get(ticket=ticket)
            if position is None or len(position) == 0:
                logger.error(f"Position {ticket} not found")
                return False

            position = position[0]

            # Determine close order type
            if position.type == mt5.ORDER_TYPE_BUY:
                order_type = mt5.ORDER_TYPE_SELL
                price = mt5.symbol_info_tick(position.symbol).bid
            else:
                order_type = mt5.ORDER_TYPE_BUY
                price = mt5.symbol_info_tick(position.symbol).ask

            # Prepare close request
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": position.symbol,
                "volume": position.volume,
                "type": order_type,
                "position": ticket,
                "price": price,
                "deviation": 20,
                "magic": position.magic,
                "comment": "Close position",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }

            # Send close order
            result = mt5.order_send(request)
            if result is None:
                logger.error(f"Close order failed: {mt5.last_error()}")
                return False

            if result.retcode != mt5.TRADE_RETCODE_DONE:
                logger.error(f"Close failed: {result.comment}")
                return False

            logger.info(f"Position {ticket} closed successfully")
            return True

        except Exception as e:
            logger.error(f"Error closing trade: {str(e)}")
            return False

    def get_open_positions(self) -> List[Position]:
        """
        Get all open positions

        Returns:
            List[Position]: List of open positions
        """
        if not self.is_connected():
            logger.error("Not connected to MT5")
            return []

        try:
            positions = mt5.positions_get()
            if positions is None:
                return []

            result = []
            for pos in positions:
                # Get current price
                tick = mt5.symbol_info_tick(pos.symbol)
                if tick is None:
                    continue

                order_type = OrderType.BUY if pos.type == mt5.ORDER_TYPE_BUY else OrderType.SELL
                current_price = tick.bid if pos.type == mt5.ORDER_TYPE_BUY else tick.ask

                position = Position(
                    ticket=pos.ticket,
                    symbol=pos.symbol,
                    order_type=order_type,
                    volume=pos.volume,
                    entry_price=pos.price_open,
                    current_price=current_price,
                    stop_loss=pos.sl if pos.sl != 0 else None,
                    take_profit=pos.tp if pos.tp != 0 else None,
                    profit=pos.profit,
                    swap=pos.swap,
                    commission=pos.commission,
                    open_time=datetime.fromtimestamp(pos.time),
                    comment=pos.comment
                )
                result.append(position)

            return result

        except Exception as e:
            logger.error(f"Error getting positions: {str(e)}")
            return []

    def modify_position(
        self,
        ticket: int,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None
    ) -> bool:
        """
        Modify SL/TP of existing position

        Args:
            ticket: Position ticket
            stop_loss: New stop loss (None to keep current)
            take_profit: New take profit (None to keep current)

        Returns:
            bool: True if modified successfully
        """
        if not self.is_connected():
            logger.error("Not connected to MT5")
            return False

        try:
            position = mt5.positions_get(ticket=ticket)
            if position is None or len(position) == 0:
                logger.error(f"Position {ticket} not found")
                return False

            position = position[0]

            request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "symbol": position.symbol,
                "position": ticket,
                "sl": stop_loss if stop_loss else position.sl,
                "tp": take_profit if take_profit else position.tp,
            }

            result = mt5.order_send(request)
            if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
                logger.error(f"Modify failed: {result.comment if result else mt5.last_error()}")
                return False

            logger.info(f"Position {ticket} modified successfully")
            return True

        except Exception as e:
            logger.error(f"Error modifying position: {str(e)}")
            return False
