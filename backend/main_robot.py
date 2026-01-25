#!/usr/bin/env python3
"""
AI Trading Robot - Main Entry Point

This is the main entry point for the 24/7 AI Trading Robot.
It starts the trading orchestrator and manages all AI components.

Usage:
    python main_robot.py [--paper] [--config CONFIG_PATH]

Options:
    --paper     Run in paper trading mode (no real trades)
    --config    Path to configuration file
"""

import asyncio
import argparse
import logging
import signal
import sys
import os
from datetime import datetime
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def setup_logging(log_level: str = "INFO", log_dir: str = "./logs"):
    """Setup logging configuration"""
    os.makedirs(log_dir, exist_ok=True)

    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(log_format, date_format))

    # File handler
    log_file = os.path.join(log_dir, f"trading_robot_{datetime.now().strftime('%Y%m%d')}.log")
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(logging.Formatter(log_format, date_format))

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    return root_logger


def print_banner():
    """Print startup banner"""
    banner = """
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║     █████╗ ██╗    ████████╗██████╗  █████╗ ██████╗ ██╗███╗   ██║║
║    ██╔══██╗██║    ╚══██╔══╝██╔══██╗██╔══██╗██╔══██╗██║████╗  ██║║
║    ███████║██║       ██║   ██████╔╝███████║██║  ██║██║██╔██╗ ██║║
║    ██╔══██║██║       ██║   ██╔══██╗██╔══██║██║  ██║██║██║╚██╗██║║
║    ██║  ██║██║       ██║   ██║  ██║██║  ██║██████╔╝██║██║ ╚████║║
║    ╚═╝  ╚═╝╚═╝       ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝ ╚═╝╚═╝  ╚═══╝║
║                                                                  ║
║              🤖 24/7 AI-Powered Trading Robot 🤖                 ║
║                                                                  ║
║    Features:                                                     ║
║    • Neural Networks (LSTM, Transformer, CNN)                   ║
║    • Reinforcement Learning Trading Agent                        ║
║    • LLM-Powered Market Analysis                                 ║
║    • Real-Time News & Sentiment Analysis                         ║
║    • Pattern Recognition                                         ║
║    • Multi-Timeframe Analysis                                    ║
║    • Autonomous Decision Making                                  ║
║    • Self-Healing & Auto-Recovery                                ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
"""
    print(banner)


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="AI Trading Robot")
    parser.add_argument("--paper", action="store_true", help="Run in paper trading mode")
    parser.add_argument("--config", type=str, default="./config/orchestrator_config.json",
                       help="Path to configuration file")
    parser.add_argument("--log-level", type=str, default="INFO",
                       help="Logging level (DEBUG, INFO, WARNING, ERROR)")
    args = parser.parse_args()

    # Setup logging
    logger = setup_logging(args.log_level)

    # Print banner
    print_banner()

    logger.info("=" * 60)
    logger.info("AI Trading Robot Starting...")
    logger.info("=" * 60)
    logger.info(f"Mode: {'Paper Trading' if args.paper else 'Live Trading'}")
    logger.info(f"Config: {args.config}")
    logger.info(f"Log Level: {args.log_level}")
    logger.info("=" * 60)

    # Check for required environment variables
    required_vars = []
    optional_vars = {
        "OPENAI_API_KEY": "OpenAI LLM analysis",
        "ANTHROPIC_API_KEY": "Anthropic LLM analysis",
        "NEWS_API_KEY": "News aggregation",
        "FINNHUB_API_KEY": "Financial data"
    }

    logger.info("Checking API keys...")
    for var, desc in optional_vars.items():
        if os.getenv(var):
            logger.info(f"  ✓ {var} - {desc}")
        else:
            logger.warning(f"  ✗ {var} - {desc} (not configured)")

    # Import and start the orchestrator
    try:
        from trading_orchestrator import TradingOrchestrator

        orchestrator = TradingOrchestrator(
            config_path=args.config,
            enable_paper_trading=args.paper or os.getenv("PAPER_TRADING", "true").lower() == "true",
            auto_recovery=True
        )

        # Handle shutdown signals
        shutdown_event = asyncio.Event()

        def signal_handler(sig):
            logger.info(f"Received signal {sig}, initiating shutdown...")
            asyncio.create_task(orchestrator.stop())
            shutdown_event.set()

        loop = asyncio.get_event_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            try:
                loop.add_signal_handler(sig, lambda s=sig: signal_handler(s))
            except NotImplementedError:
                # Windows doesn't support add_signal_handler
                signal.signal(sig, lambda s, f: signal_handler(s))

        # Add callbacks for logging
        async def on_trade_opened(order):
            logger.info(f"🎯 Trade Opened: {order.direction} {order.volume} {order.symbol}")

        async def on_signal_generated(decision):
            logger.info(f"📊 Signal: {decision.action} {decision.symbol} (confidence: {decision.confidence:.2%})")

        orchestrator.on_trade_opened.append(on_trade_opened)
        orchestrator.on_signal_generated.append(on_signal_generated)

        # Start the orchestrator
        logger.info("")
        logger.info("🚀 Starting Trading Orchestrator...")
        logger.info("")

        await orchestrator.start()

    except KeyboardInterrupt:
        logger.info("Shutdown requested by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    logger.info("AI Trading Robot shutdown complete")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutdown requested")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
