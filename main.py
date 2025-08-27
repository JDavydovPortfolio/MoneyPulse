#!/usr/bin/env python3
"""
Merchant Document Processing Pipeline
Premium GUI Version - Main Entry Point
"""

import sys
import os
import logging
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def setup_application():
    """Setup application environment and logging."""
    # Create necessary directories
    Path("input").mkdir(exist_ok=True)
    Path("output").mkdir(exist_ok=True)
    Path("logs").mkdir(exist_ok=True)
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/application.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    """Main application entry point."""
    try:
        setup_application()
        
        # Import and launch GUI
        from src.gui.premium_gui import launch_application
        launch_application()
        
    except ImportError as e:
        print(f"Import Error: {e}")
        print("Please ensure all dependencies are installed: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"Application Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()