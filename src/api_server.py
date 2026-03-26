#!/usr/bin/env python3
"""
MTS Employee Monitoring API Server

Simple launcher for the Employee Monitoring REST API server.
Provides an easy way to start the API server with different configurations.
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from api.employee_monitoring_api import run_api_server

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('api_server.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def main():
    """Main entry point for API server."""
    parser = argparse.ArgumentParser(
        description='MTS Employee Monitoring API Server',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python src/api_server.py                    # Start with defaults (localhost:8000)
  python src/api_server.py --host 0.0.0.0     # Allow external connections
  python src/api_server.py --port 9000       # Use custom port
  python src/api_server.py --reload          # Enable auto-reload for development
        """
    )
    
    parser.add_argument(
        '--host',
        default='127.0.0.1',
        help='Host to bind the server to (default: 127.0.0.1)'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        default=8000,
        help='Port to bind the server to (default: 8000)'
    )
    
    parser.add_argument(
        '--reload',
        action='store_true',
        help='Enable auto-reload for development (use with care in production)'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['debug', 'info', 'warning', 'error'],
        default='info',
        help='Set logging level (default: info)'
    )
    
    args = parser.parse_args()
    
    # Configure logging level
    logging.getLogger().setLevel(getattr(logging, args.log_level.upper()))
    
    # Print startup info
    print("\n" + "="*60)
    print("🚀 MTS EMPLOYEE MONITORING API SERVER")
    print("="*60)
    print(f"🌐 Host: {args.host}")
    print(f"🔌 Port: {args.port}")
    print(f"🔄 Auto-reload: {'Enabled' if args.reload else 'Disabled'}")
    print(f"📊 Log level: {args.log_level}")
    print("="*60)
    print(f"📖 API Documentation: http://{args.host}:{args.port}/docs")
    print(f"🔴 ReDoc Documentation: http://{args.host}:{args.port}/redoc")
    print(f"💚 Health Check: http://{args.host}:{args.port}/health")
    print(f"📊 System Status: http://{args.host}:{args.port}/status")
    print("="*60)
    print("🎯 API Server Features:")
    print("   ✅ Task scheduling and management")
    print("   ✅ Workflow execution control")
    print("   ✅ Real-time status monitoring")
    print("   ✅ Configuration management")
    print("   ✅ Report history access")
    print("   ✅ Health check endpoints")
    print("="*60)
    print("⏹️  Press Ctrl+C to stop the server")
    print("="*60 + "\n")
    
    try:
        logger.info(f"Starting API server on {args.host}:{args.port}")
        run_api_server(host=args.host, port=args.port, reload=args.reload)
    except KeyboardInterrupt:
        logger.info("API server stopped by user")
    except Exception as e:
        logger.error(f"API server failed to start: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
