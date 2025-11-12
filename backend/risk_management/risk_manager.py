"""Risk management for safe trading"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
from ..mt5_connector import MT5Connector, Position

logger = logging.getLogger(__name__)


class RiskManager:
    """
    Risk management system to protect account
    - Position sizing
    - Max positions limit
    - Daily loss limit
    - Max drawdown protection
    - Risk per trade
    """

    def __init__(
        self,
        mt5_connector: MT5Connector,
        max_positions: int = 3,
        risk_per_trade: float = 0.02,  # 2%
        max_daily_loss: float = 0.05,  # 5%
        max_drawdown: float = 0.15,  # 15%
    ):
        """
        Initialize risk manager

        Args:
            mt5_connector: MT5 connector
            max_positions: Maximum concurrent positions
            risk_per_trade: Risk per trade as fraction of balance
            max_daily_loss: Maximum daily loss as fraction
            max_drawdown: Maximum drawdown as fraction
        """
        self.mt5 = mt5_connector
        self.max_positions = max_positions
        self.risk_per_trade = risk_per_trade
        self.max_daily_loss = max_daily_loss
        self.max_drawdown = max_drawdown

        self.daily_start_balance = None
        self.daily_reset_time = None
        self.peak_balance = None
        self.trades_today = []

    def can_open_trade(self, symbol: str) -> bool:
        """
        Check if we can open a new trade

        Args:
            symbol: Trading symbol

        Returns:
            True if safe to trade
        """
        # Check connection
        if not self.mt5.is_connected():
            logger.error("MT5 not connected")
            return False

        # Update daily tracking
        self._update_daily_tracking()

        # Check max positions
        positions = self.mt5.get_open_positions()
        if len(positions) >= self.max_positions:
            logger.info(f"Max positions reached: {len(positions)}/{self.max_positions}")
            return False

        # Check if already have position in this symbol
        for pos in positions:
            if pos.symbol == symbol:
                logger.info(f"Already have position in {symbol}")
                return False

        # Check daily loss limit
        if not self._check_daily_loss_limit():
            logger.warning("Daily loss limit reached")
            return False

        # Check max drawdown
        if not self._check_max_drawdown():
            logger.warning("Max drawdown reached")
            return False

        # Check market hours
        if not self._check_market_hours():
            logger.info("Outside trading hours")
            return False

        return True

    def calculate_position_size(
        self,
        symbol: str,
        entry_price: float,
        stop_loss: float
    ) -> float:
        """
        Calculate position size based on risk

        Args:
            symbol: Trading symbol
            entry_price: Entry price
            stop_loss: Stop loss price

        Returns:
            Position size in lots
        """
        account_info = self.mt5.get_account_info()
        if account_info is None:
            logger.error("Failed to get account info")
            return 0.01  # Minimum lot size

        # Calculate risk amount in account currency
        risk_amount = account_info.balance * self.risk_per_trade

        # Calculate pip value and risk in pips
        if stop_loss == 0:
            return 0.01

        risk_pips = abs(entry_price - stop_loss)

        # For forex, typically 1 pip = 0.0001 for most pairs
        # Position size = Risk Amount / (Risk in Pips * Pip Value)
        # Simplified: assuming pip value of 10 for standard lot

        # Get symbol info for accurate calculation
        if hasattr(self.mt5, 'symbol_info'):
            # This would use MT5's symbol info
            pass

        # Simplified calculation
        # Risk per pip = risk_amount / risk_pips
        # Lot size = risk_amount / (risk_pips * contract_size)

        # For EURUSD, 1 standard lot = $100,000
        # 1 pip (0.0001) = $10 for 1 standard lot
        pip_value_per_lot = 10  # For standard lot
        lots = risk_amount / (risk_pips * pip_value_per_lot * 10000)

        # Round to 2 decimal places and enforce limits
        lots = round(lots, 2)
        lots = max(0.01, min(lots, 10.0))  # Min 0.01, max 10.0

        logger.info(
            f"Position size for {symbol}: {lots} lots "
            f"(risk: {risk_amount:.2f} {account_info.currency})"
        )

        return lots

    def _update_daily_tracking(self):
        """Update daily tracking variables"""
        now = datetime.now()

        # Reset daily tracking if new day
        if (self.daily_reset_time is None or
            now.date() > self.daily_reset_time.date()):
            account_info = self.mt5.get_account_info()
            if account_info:
                self.daily_start_balance = account_info.balance
                self.daily_reset_time = now
                self.trades_today = []
                logger.info(f"Daily tracking reset. Start balance: {self.daily_start_balance}")

        # Update peak balance for drawdown tracking
        if account_info := self.mt5.get_account_info():
            if self.peak_balance is None or account_info.balance > self.peak_balance:
                self.peak_balance = account_info.balance

    def _check_daily_loss_limit(self) -> bool:
        """Check if daily loss limit is reached"""
        account_info = self.mt5.get_account_info()
        if not account_info or not self.daily_start_balance:
            return True

        daily_loss = self.daily_start_balance - account_info.balance
        max_loss = self.daily_start_balance * self.max_daily_loss

        if daily_loss >= max_loss:
            logger.warning(
                f"Daily loss limit reached: {daily_loss:.2f} >= {max_loss:.2f}"
            )
            return False

        return True

    def _check_max_drawdown(self) -> bool:
        """Check if max drawdown is reached"""
        account_info = self.mt5.get_account_info()
        if not account_info or not self.peak_balance:
            return True

        drawdown = (self.peak_balance - account_info.balance) / self.peak_balance

        if drawdown >= self.max_drawdown:
            logger.warning(
                f"Max drawdown reached: {drawdown:.2%} >= {self.max_drawdown:.2%}"
            )
            return False

        return True

    def _check_market_hours(self) -> bool:
        """Check if within good trading hours"""
        # Forex is 24/5, but avoid low liquidity periods
        now = datetime.utcnow()

        # Skip weekends
        if now.weekday() >= 5:
            return False

        # Avoid Friday after 20:00 UTC (weekend approaching)
        if now.weekday() == 4 and now.hour >= 20:
            return False

        # Avoid Sunday before 22:00 UTC (market just opening)
        if now.weekday() == 6 and now.hour < 22:
            return False

        return True

    def get_risk_summary(self) -> Dict:
        """
        Get current risk metrics

        Returns:
            Dictionary with risk information
        """
        account_info = self.mt5.get_account_info()
        positions = self.mt5.get_open_positions()

        summary = {
            'timestamp': datetime.now().isoformat(),
            'open_positions': len(positions),
            'max_positions': self.max_positions,
            'total_exposure': 0.0,
            'daily_pnl': 0.0,
            'daily_pnl_percent': 0.0,
            'current_drawdown': 0.0,
            'can_trade': False
        }

        if account_info:
            summary['balance'] = account_info.balance
            summary['equity'] = account_info.equity
            summary['free_margin'] = account_info.free_margin

            # Calculate total exposure
            summary['total_exposure'] = sum(
                pos.volume * pos.entry_price for pos in positions
            )

            # Calculate daily P&L
            if self.daily_start_balance:
                summary['daily_pnl'] = account_info.balance - self.daily_start_balance
                summary['daily_pnl_percent'] = (
                    summary['daily_pnl'] / self.daily_start_balance * 100
                )

            # Calculate drawdown
            if self.peak_balance:
                summary['current_drawdown'] = (
                    (self.peak_balance - account_info.balance) / self.peak_balance * 100
                )

            # Check if can trade
            summary['can_trade'] = (
                len(positions) < self.max_positions and
                self._check_daily_loss_limit() and
                self._check_max_drawdown()
            )

        return summary
