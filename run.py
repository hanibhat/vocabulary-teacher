#!/usr/bin/env python3
"""
Cross-platform single-command server runner for Vocabulary Teacher.

Usage:
    python run.py                   # Run with defaults
    python run.py --port 8080       # Override port
    python run.py --no-reload       # Disable auto-reload
    python run.py -- --root-path /api  # Pass arbitrary uvicorn args after --

All arguments after an optional ``--`` separator are forwarded to uvicorn.
"""

import argparse
import os
import subprocess
import sys
import venv
from pathlib import Path

SERVER_DIR = Path(__file__).resolve().parent / "server"
VENV_DIR = SERVER_DIR / "venv"
REQUIREMENTS = SERVER_DIR / "requirements.txt"

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 5000


def _venv_python() -> Path:
    if sys.platform == "win32":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def _venv_pip() -> Path:
    if sys.platform == "win32":
        return VENV_DIR / "Scripts" / "pip.exe"
    return VENV_DIR / "bin" / "pip"


def ensure_venv():
    """Create the virtual environment if it doesn't exist."""
    if not VENV_DIR.exists():
        print("[run.py] Creating virtual environment...")
        venv.create(VENV_DIR, with_pip=True)
        print(f"[run.py] Virtual environment created at {VENV_DIR}")
    else:
        print(f"[run.py] Virtual environment found at {VENV_DIR}")


def install_dependencies():
    """Install requirements from requirements.txt."""
    print("[run.py] Installing dependencies...")
    subprocess.check_call(
        [str(_venv_pip()), "install", "-r", str(REQUIREMENTS)]
    )
    print("[run.py] Dependencies installed.")


def start_server(host: str, port: int, reload: bool, extra_args: list[str]):
    """Start uvicorn with the given configuration."""
    uvicorn_args = [
        str(_venv_python()),
        "-m",
        "uvicorn",
        "main:app",
        "--host", host,
        "--port", str(port),
    ]
    if reload:
        uvicorn_args.append("--reload")
    uvicorn_args.extend(extra_args)

    print(f"[run.py] Starting server on http://{host}:{port}")
    if reload:
        print("[run.py] Auto-reload is enabled.")

    os.chdir(SERVER_DIR)

    try:
        subprocess.check_call(uvicorn_args)
    except KeyboardInterrupt:
        print("\n[run.py] Server stopped.")
        sys.exit(0)


def parse_args(argv: list[str]) -> argparse.Namespace:
    """Parse command-line arguments, splitting uvicorn passthrough after --."""
    if "--" in argv:
        sep = argv.index("--")
        main_args = argv[:sep]
        extra_args = argv[sep + 1:]
    else:
        main_args = argv
        extra_args = []

    parser = argparse.ArgumentParser(
        description="Run the Vocabulary Teacher server.",
    )
    parser.add_argument(
        "--host",
        default=DEFAULT_HOST,
        help=f"Bind address (default: {DEFAULT_HOST})",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help=f"Bind port (default: {DEFAULT_PORT})",
    )
    parser.add_argument(
        "--no-reload",
        action="store_true",
        help="Disable auto-reload on code changes",
    )
    parser.add_argument(
        "extra",
        nargs="*",
        help=argparse.SUPPRESS,
    )

    namespace = parser.parse_args(main_args)
    namespace.extra = extra_args
    return namespace


def main():
    argv = sys.argv[1:] if len(sys.argv) > 1 else []
    args = parse_args(argv)

    ensure_venv()
    install_dependencies()
    start_server(
        host=args.host,
        port=args.port,
        reload=not args.no_reload,
        extra_args=args.extra,
    )


if __name__ == "__main__":
    main()
