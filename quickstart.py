#!/usr/bin/env python3
"""
Quick start script for LogGem.

Sets up the environment and runs a demo analysis with different model options.
"""

import subprocess
import sys
from pathlib import Path


def print_banner():
    """Print LogGem banner."""
    print("""
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║   💎 LogGem - AI-Powered Log Analysis                   ║
║   Intelligent anomaly detection with lightweight LLMs   ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
    """)


def run_command(cmd: list[str], description: str, show_output: bool = True) -> bool:
    """Run a command and return success status."""
    print(f"\n{'='*60}")
    print(f"  {description}")
    print(f"{'='*60}")
    try:
        if show_output:
            subprocess.run(cmd, check=True)
        else:
            subprocess.run(cmd, check=True, capture_output=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed: {e}")
        return False


def main() -> int:
    """Main setup function."""
    print_banner()

    # Check Python version
    if sys.version_info < (3, 9):
        print("❌ Python 3.9 or higher is required")
        return 1

    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")

    # Install LogGem
    print("\n📦 Installing LogGem with HuggingFace support...")
    print("   (Includes Gemma 3, Llama, and other local models)")
    
    if not run_command(
        [sys.executable, "-m", "pip", "install", "-e", ".[huggingface]"],
        "Installing LogGem with dependencies",
        show_output=False
    ):
        return 1

    print("\n✅ LogGem installed successfully!")

    # Show model options
    print("\n" + "=" * 60)
    print("  🤖 Available Lightweight Models")
    print("=" * 60)
    print("""
╭─────────────────────────────────────────────────────────────╮
│  Model            │  Size  │  RAM   │  Speed   │  Accuracy │
├─────────────────────────────────────────────────────────────┤
│  Gemma 3 4B-it    │  4GB   │  8GB   │  ⚡⚡⚡    │  ⭐⭐⭐    │
│  Gemma 3 12B-it    │  12GB   │  16GB  │  ⚡⚡      │  ⭐⭐⭐⭐   │
│  Gemma 3 27B-it   │  27GB  │  34GB  │  ⚡       │  ⭐⭐⭐⭐⭐  │
│  Llama 3.2 3B     │  3GB   │  8GB   │  ⚡⚡⚡    │  ⭐⭐⭐    │
│  Mistral 7B       │  7GB   │  16GB  │  ⚡⚡      │  ⭐⭐⭐⭐   │
╰─────────────────────────────────────────────────────────────╯

Default: Gemma 3 4B-it (best balance of speed & accuracy)
    """)

    # Run a demo analysis
    print("\n" + "=" * 60)
    print("  🔍 Running Demo Analysis")
    print("=" * 60)

    demo_file = Path("examples/sample_auth.log")
    if not demo_file.exists():
        print(f"⚠️  Demo file not found: {demo_file}")
        print("Skipping demo analysis")
    else:
        print(f"\n📋 Analyzing: {demo_file}")
        print("\n⚙️  Running rule-based detection (fast demo)...")
        print("   (For AI detection, run without --no-ai flag)\n")

        # Run with --no-ai for faster demo
        run_command(
            [sys.executable, "-m", "loggem.cli", "analyze", str(demo_file), "--no-ai"],
            "LogGem Analysis - Rule-Based Detection"
        )

    # Print next steps
    print("\n" + "=" * 60)
    print("  🎉 Setup Complete!")
    print("=" * 60)
    print("""
📚 Quick Start Commands:

  # 1️⃣  Rule-based detection (fast, no model download)
  loggem analyze examples/sample_auth.log --no-ai

  # 2️⃣  AI detection with Gemma 3 4B (downloads ~4GB model first time)
  loggem analyze examples/sample_auth.log

  # 3️⃣  Use larger model for better accuracy (config.yaml)
  model:
    provider: "huggingface"
    name: "google/gemma-3-12b-it"  # 9B model

  # 4️⃣  Analyze different formats
  loggem analyze examples/sample_nginx.log --format nginx
  loggem analyze examples/sample_json.log --format json

  # 5️⃣  Watch logs in real-time
  loggem watch /var/log/auth.log

  # 6️⃣  Adjust sensitivity (0.0 - 1.0)
  loggem analyze auth.log --sensitivity 0.9

📖 Documentation:
  • README.md      - Full documentation
  • QUICKSTART.md  - Quick setup guide
  • EXAMPLES.md    - More examples & model configs
  • TESTING.md     - Development guide

🔧 Model Selection:
  • Gemma 3 4B  - Fast, 8GB RAM (default)
  • Gemma 3 12B  - Balanced, 16GB RAM (better accuracy)
  • Gemma 3 27B - Best, 34GB RAM (highest accuracy)
  • Llama 3.2   - Alternative, 8GB RAM
  • Cloud APIs  - OpenAI, Anthropic (no download needed)

💡 Pro Tip: Start with --no-ai for instant results, then enable AI
           detection when you need deeper analysis!

💎 Happy log hunting with LogGem!
    """)

    return 0


if __name__ == "__main__":
    sys.exit(main())
