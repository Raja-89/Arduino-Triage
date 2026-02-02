#!/usr/bin/env python3
"""
Smart Rural Triage Station - Main Application Entry Point
=========================================================

This is the main entry point for the Smart Rural Triage Station application.
It initializes and coordinates all system components including:
- Hardware interfaces (Arduino MCU, sensors, camera)
- Audio processing pipeline
- Machine learning inference
- Web interface
- Triage decision engine

Usage:
    python3 main.py [--config CONFIG_FILE] [--debug] [--demo]

Author: Smart Rural Triage Station Team
Version: 1.0.0
License: Mozilla Public License Version 2.0
"""

import sys
import os
import argparse
import asyncio
import logging
from pathlib import Path

# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT / "linux"))

from linux.core.system_manager import SystemManager
from linux.core.config_manager import ConfigManager
from linux.core.logger import setup_logging


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Smart Rural Triage Station - AI-Powered Medical Screening"
    )
    
    parser.add_argument(
        "--config",
        type=str,
        default="config/system.yaml",
        help="Path to system configuration file"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run in demo mode with simulated data"
    )
    
    parser.add_argument(
        "--web-only",
        action="store_true",
        help="Run only the web interface (for development)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=5000,
        help="Web interface port (default: 5000)"
    )
    
    return parser.parse_args()


async def main():
    """Main application entry point."""
    args = parse_arguments()
    
    # Setup logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    setup_logging(level=log_level)
    
    logger = logging.getLogger(__name__)
    logger.info("Starting Smart Rural Triage Station v1.0.0")
    
    try:
        # Load configuration
        config_manager = ConfigManager(args.config)
        config = config_manager.get_config()
        
        # Override config with command line arguments
        if args.demo:
            config['system']['demo_mode'] = True
        if args.web_only:
            config['system']['web_only'] = True
        if args.port != 5000:
            config['web']['port'] = args.port
            
        logger.info(f"Configuration loaded from: {args.config}")
        
        # Initialize system manager
        system_manager = SystemManager(config)
        
        # Start the system
        logger.info("Initializing system components...")
        await system_manager.initialize()
        
        logger.info("System initialization complete")
        logger.info(f"Web interface available at: http://localhost:{config.get('web', {}).get('port', 5000)}")
        
        if config.get('system', {}).get('demo_mode', False):
            logger.info("Running in DEMO MODE - using simulated data")
        
        # Run the main system loop
        await system_manager.run()
        
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error(f"System error: {e}", exc_info=True)
        return 1
    finally:
        logger.info("Shutting down system...")
        if 'system_manager' in locals():
            await system_manager.shutdown()
        logger.info("Shutdown complete")
    
    return 0


if __name__ == "__main__":
    # Ensure we're running on Python 3.8+
    if sys.version_info < (3, 8):
        print("Error: Python 3.8 or higher is required")
        sys.exit(1)
    
    # Run the main application
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)