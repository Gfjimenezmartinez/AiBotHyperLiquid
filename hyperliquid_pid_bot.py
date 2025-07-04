# hyperliquid_pid_bot.py
from dotenv import load_dotenv
import os
import ccxt
import time

load_dotenv()

class MarginTrader:
    def __init__(self):
        self.exchange = ccxt.hyperliquid({
            "walletAddress": os.getenv("WALLET_ADDRESS"),
            "privateKey": os.getenv("PRIVATE_KEY"),
            "enableRateLimit": True,
            "options": {"defaultType": "swap"}
        })
        
        # Trading parameters
        self.leverage = 25  # 25x leverage
        self.portfolio_risk = 0.25  # 25% of total portfolio per trade
        self.take_profit_pct = 0.30  # 30% profit target
        self.stop_loss_pct = 0.10  # 10% stop loss
        
        # Initialize account
        self._setup_account()

    def _setup_account(self):
        """Configure margin and leverage"""
        try:
            self.exchange.set_margin_mode("cross", "ETH/USDC:USDC")
            self.exchange.set_leverage(self.leverage, "ETH/USDC:USDC")
            print(f"Account configured: Cross Margin {self.leverage}x")
        except Exception as e:
            print(f"Account config failed: {e}")
            exit()

    def _get_support_zone(self) -> float:
        """Placeholder for support zone analysis"""
        ticker = self.exchange.fetch_ticker("ETH/USDC:USDC")
        return ticker['last'] * 0.99  # Temporary 1% below current price

    def _calculate_position(self) -> dict:
        """Calculate trade size using 25% of portfolio"""
        balance = self.exchange.fetch_balance()['USDC']['total']  # Total portfolio value
        margin_to_use = balance * self.portfolio_risk
        entry_price = self._get_support_zone()
        
        # Calculate max position size (margin * leverage)
        size = (margin_to_use * self.leverage) / entry_price
        
        return {
            "size": size,
            "entry": entry_price,
            "tp": entry_price * (1 + self.take_profit_pct),
            "sl": entry_price * (1 - self.stop_loss_pct),
            "margin_used": margin_to_use
        }

    def execute_trade(self):
        """Execute trade with 25% portfolio margin"""
        trade = self._calculate_position()
        current_price = self.exchange.fetch_ticker("ETH/USDC:USDC")['last']
        
        if current_price > trade['entry']:
            print(f"Current price {current_price} above entry {trade['entry']}. Waiting...")
            return

        print(f"""
        Trade Setup:
        Entry Price: {trade['entry']:.2f}
        Position Size: {trade['size']:.4f} ETH
        Take Profit: {trade['tp']:.2f}
        Stop Loss: {trade['sl']:.2f}
        Margin Used: ${trade['margin_used']:.2f} (25% of portfolio)
        Leverage: {self.leverage}x
        """)

        try:
            self.exchange.create_order(
                symbol="ETH/USDC:USDC",
                type="limit",
                side="buy",
                amount=trade['size'],
                price=trade['entry'],
                params={
                    "takeProfitPrice": trade['tp'],
                    "stopLossPrice": trade['sl'],
                    "reduceOnly": False
                }
            )
            print("Limit order placed at target price")
        except Exception as e:
            print(f"Order failed: {e}")

    def run(self):
        """Main trading loop"""
        print("Starting 25% Margin Trader...")
        while True:
            try:
                self.execute_trade()
                time.sleep(60)
            except KeyboardInterrupt:
                print("Trading stopped by user")
                break
            except Exception as e:
                print(f"Error: {e}")
                time.sleep(30)

if __name__ == "__main__":
    trader = MarginTrader()
    trader.run()
