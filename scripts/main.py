#!/usr/bin/env python3
"""
Smart Rural Triage Station - Main Entry Point
=============================================

This is the main entry point for the Smart Rural Triage Station system.
It initializes and starts all system components.

Author: Smart Triage Team
Version: 1.0.0
License: MIT
"""

import asyncio
import logging
import signal
import sys
import os
from pathlib import Path

# Add the linux directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'linux'))

from linux.core.system_manager import SystemManager


def setup_logging():
    """Setup logging configuration."""
    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/system.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Set specific log levels for noisy libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('PIL').setLevel(logging.WARNING)


def print_banner():
    """Print system banner."""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║           Smart Rural Triage Station                        ║
    ║           Arduino x Qualcomm AI for All Hackathon           ║
    ║                                                              ║
    ║           AI-Powered Medical Screening System               ║
    ║           Version 1.0.0                                     ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)


async def main():
    """Main application entry point."""
    print_banner()
    
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Starting Smart Rural Triage Station...")
    
    # Configuration file path
    config_path = os.path.join(os.path.dirname(__file__), 'config', 'system.yaml')
    
    # Create system manager
    system_manager = SystemManager(config_path)
    
    # Setup signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, initiating shutdown...")
        asyncio.create_task(shutdown(system_manager))
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Initialize system
        logger.info("Initializing system components...")
        if not await system_manager.initialize():
            logger.error("System initialization failed")
            sys.exit(1)
        
        logger.info("System initialization completed successfully")
        logger.info("Smart Rural Triage Station is now running")
        logger.info("Web interface available at: http://localhost:5000")
        logger.info("Press Ctrl+C to shutdown")
        
        # Keep the system running
        while system_manager.running:
            await asyncio.sleep(1.0)
            
    except KeyboardInterrupt:
        logger.info("Shutdown requested by user")
    except Exception as e:
        logger.error(f"System error: {e}")
        sys.exit(1)
    finally:
        await shutdown(system_manager)


async def shutdown(system_manager):
    """Graceful system shutdown."""
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Initiating system shutdown...")
        await system_manager.shutdown()
        logger.info("System shutdown completed")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")
    finally:
        # Force exit if needed
        sys.exit(0)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)