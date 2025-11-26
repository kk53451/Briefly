#!/usr/bin/env python
"""
Briefly Backend Development Server Runner

Usage:
    python run_server.py
    python run_server.py --port 8080
    python run_server.py --reload
"""

import uvicorn
import argparse


def main():
    parser = argparse.ArgumentParser(description="Run Briefly backend server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind (default: 8000)")
    parser.add_argument("--reload", action="store_true", default=True, help="Enable auto-reload (default: True)")
    parser.add_argument("--no-reload", action="store_true", help="Disable auto-reload")

    args = parser.parse_args()

    reload_enabled = not args.no_reload and args.reload

    print(f"🚀 Starting Briefly API server...")
    print(f"📍 URL: http://localhost:{args.port}")
    print(f"📚 Docs: http://localhost:{args.port}/docs")
    print(f"🔄 Auto-reload: {'enabled' if reload_enabled else 'disabled'}")
    print("-" * 50)

    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        reload=reload_enabled,
    )


if __name__ == "__main__":
    main()
