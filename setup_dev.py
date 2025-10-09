#!/usr/bin/env python3
"""
Setup script for API Debugger development.
This script helps developers get started quickly.
"""

import subprocess
import sys


def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"📦 {description}...")
    try:
        subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        if e.stdout:
            print(f"stdout: {e.stdout}")
        if e.stderr:
            print(f"stderr: {e.stderr}")
        return False


def main():
    """Main setup function."""
    print("🚀 Setting up API Debugger development environment...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        sys.exit(1)
    
    print(f"✅ Python {sys.version} detected")
    
    # Install the package in development mode
    commands = [
        ("pip install -e .", "Installing API Debugger in development mode"),
        ("pip install -e '.[dev]'", "Installing development dependencies"),
        ("pytest --version", "Verifying pytest installation"),
    ]
    
    for cmd, desc in commands:
        if not run_command(cmd, desc):
            print(f"❌ Setup failed at: {desc}")
            sys.exit(1)
    
    # Optional: Install pre-commit hooks
    try:
        run_command("pre-commit --version", "Checking pre-commit availability")
        run_command("pre-commit install", "Installing pre-commit hooks")
    except Exception:
        print("⚠️ Pre-commit not available (optional)")
    
    print("\n🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print("  1. Run tests: pytest")
    print("  2. Run examples: python examples/sample_usage.py")
    print("  3. Check coverage: pytest --cov=api_debugger")
    print("  4. Start developing! 🚀")


if __name__ == "__main__":
    main()