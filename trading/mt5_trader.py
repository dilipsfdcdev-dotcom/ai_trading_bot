import MetaTrader5 as mt5
import logging

class MT5Trader:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.connected = False
        
    def connect(self):
        """Connect to MT5"""
        if not mt5.initialize():
            return False
            
        if mt5.login(self.config.MT5_LOGIN, self.config.MT5_PASSWORD, self.config.MT5_SERVER):
            self.connected = True
            self.logger.info("✅ MT5 trading connection established")
            return True
        return False
    
    def place_order(self, symbol, action, volume=0.01):
        """Place a trading order"""
        if not self.connected:
            self.logger.error("❌ MT5 not connected")
            return False
        
        # Get current price
        tick = mt5.symbol_info_tick(symbol)
        if not tick:
            self.logger.error(f"❌ Cannot get price for {symbol}")
            return False
        
        # Prepare order
        if action.upper() == 'BUY':
            order_type = mt5.ORDER_TYPE_BUY
            price = tick.ask
        elif action.upper() == 'SELL':
            order_type = mt5.ORDER_TYPE_SELL
            price = tick.bid
        else:
            self.logger.error(f"❌ Invalid action: {action}")
            return False
        
        # Order request
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": volume,
            "type": order_type,
            "price": price,
            "deviation": 20,
            "magic": 234000,
            "comment": "AI_Bot_Trade",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        # Send order
        result = mt5.order_send(request)
        
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            self.logger.error(f"❌ Order failed: {result.comment}")
            return False
        
        self.logger.info(f"✅ Order executed: {action} {volume} {symbol} at {price}")
        return True
    
    def get_positions(self):
        """Get current positions"""
        if not self.connected:
            return []
        return mt5.positions_get()
    
    def get_account_info(self):
        """Get account information"""
        if not self.connected:
            return None
        return mt5.account_info()