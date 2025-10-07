"""
Example: Model Showcase

Demonstrates how to use different lightweight LLM models with LogGem,
including Gemma 3 4B, Gemma 3 12B, Gemma 3 27B, Llama 3.2, and Mistral.
"""

from pathlib import Path
from loggem.detector.model_manager import ModelManager
from loggem.parsers import LogParserFactory


def print_section(title: str):
    """Print a section header."""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def showcase_gemma_2b():
    """
    Gemma 3 4B - The Default Choice
    
    Best for: Getting started, fast inference, low resource usage
    Speed: ⚡⚡⚡ (Fast)
    Accuracy: ⭐⭐⭐ (Good)
    RAM: 8GB
    Download: ~4GB
    """
    print_section("🚀 Gemma 3 4B - Fast & Efficient (DEFAULT)")
    
    print("""
╭─────────────────────────────────────────────────────────────────────╮
│  Gemma 3 4B-it - The Default Model                                 │
├─────────────────────────────────────────────────────────────────────┤
│  Model ID:    google/gemma-3-4b-it                                  │
│  Parameters:  2 billion                                             │
│  Download:    ~4GB (first run only)                                 │
│  RAM:         8GB minimum                                           │
│  Speed:       ⚡⚡⚡ (1-2 seconds per log entry)                       │
│  Accuracy:    ⭐⭐⭐ (Good for most use cases)                         │
├─────────────────────────────────────────────────────────────────────┤
│  Best For:                                                          │
│  • First-time users                                                 │
│  • Standard log analysis                                            │
│  • Fast inference needed                                            │
│  • Limited hardware (8GB RAM)                                       │
│  • Quick prototyping                                                │
╰─────────────────────────────────────────────────────────────────────╯
    """)
    
    print("📝 Configuration (config.yaml):")
    print("""
    model:
      provider: "huggingface"
      name: "google/gemma-3-4b-it"
      device: "auto"          # GPU if available, else CPU
      quantization: "int8"    # 4x smaller, minimal accuracy loss
      cache_dir: "./models"
      max_length: 2048
    """)
    
    print("🐍 Python Code:")
    print("""
    from loggem.detector.model_manager import ModelManager
    
    manager = ModelManager(
        provider_type="huggingface",
        provider_config={
            "model_name": "google/gemma-3-4b-it",
            "device": "auto",
            "quantization": "int8",
        }
    )
    manager.load_model()
    response = manager.generate_response("Analyze this log...")
    """)


def showcase_gemma_9b():
    """
    Gemma 3 12B - The Balanced Choice
    
    Best for: Better accuracy, production deployments
    Speed: ⚡⚡ (Medium)
    Accuracy: ⭐⭐⭐⭐ (Very Good)
    RAM: 16GB
    Download: ~12GB
    """
    print_section("⚖️  Gemma 3 12B - Balanced Performance")
    
    print("""
╭─────────────────────────────────────────────────────────────────────╮
│  Gemma 3 12B-it - The Balanced Model                                │
├─────────────────────────────────────────────────────────────────────┤
│  Model ID:    google/gemma-3-12b-it                                  │
│  Parameters:  9 billion                                             │
│  Download:    ~12GB (first run only)                                 │
│  RAM:         16GB minimum                                          │
│  Speed:       ⚡⚡ (3-5 seconds per log entry)                        │
│  Accuracy:    ⭐⭐⭐⭐ (Better pattern recognition)                     │
├─────────────────────────────────────────────────────────────────────┤
│  Best For:                                                          │
│  • Production deployments                                           │
│  • Complex log patterns                                             │
│  • Security-critical analysis                                       │
│  • Better accuracy needed                                           │
│  • Medium hardware (16GB RAM)                                       │
╰─────────────────────────────────────────────────────────────────────╯
    """)
    
    print("📝 Configuration (config.yaml):")
    print("""
    model:
      provider: "huggingface"
      name: "google/gemma-3-12b-it"
      device: "auto"
      quantization: "int8"    # Recommended for 16GB RAM
      cache_dir: "./models"
      max_length: 2048
    """)
    
    print("💡 Pro Tip:")
    print("   Use int8 quantization to fit in 16GB RAM with minimal accuracy loss")


def showcase_gemma_27b():
    """
    Gemma 3 27B - The Premium Choice
    
    Best for: Highest accuracy, complex analysis
    Speed: ⚡ (Slower)
    Accuracy: ⭐⭐⭐⭐⭐ (Excellent)
    RAM: 34GB
    Download: ~27GB
    """
    print_section("🏆 Gemma 3 27B - Maximum Accuracy")
    
    print("""
╭─────────────────────────────────────────────────────────────────────╮
│  Gemma 3 27B-it - The Premium Model                                │
├─────────────────────────────────────────────────────────────────────┤
│  Model ID:    google/gemma-3-27b-it                                 │
│  Parameters:  27 billion                                            │
│  Download:    ~27GB (first run only)                                │
│  RAM:         34GB minimum (64GB recommended)                       │
│  Speed:       ⚡ (10-15 seconds per log entry)                       │
│  Accuracy:    ⭐⭐⭐⭐⭐ (Best pattern recognition)                      │
├─────────────────────────────────────────────────────────────────────┤
│  Best For:                                                          │
│  • Mission-critical systems                                         │
│  • Complex security analysis                                        │
│  • Advanced threat detection                                        │
│  • Highest accuracy required                                        │
│  • High-end hardware (34GB+ RAM)                                    │
╰─────────────────────────────────────────────────────────────────────╯
    """)
    
    print("📝 Configuration (config.yaml):")
    print("""
    model:
      provider: "huggingface"
      name: "google/gemma-3-27b-it"
      device: "cuda"          # GPU highly recommended
      quantization: "int8"    # Required for 34GB RAM
      cache_dir: "./models"
      max_length: 2048
    """)
    
    print("⚠️  Hardware Requirements:")
    print("   • GPU: NVIDIA with 24GB+ VRAM (recommended)")
    print("   • CPU: 34GB+ RAM with int8 quantization")
    print("   • Storage: 30GB+ free space")


def showcase_alternatives():
    """Show alternative models to Gemma."""
    print_section("🔄 Alternative Models")
    
    print("""
╭─────────────────────────────────────────────────────────────────────╮
│  Llama 3.2 3B - Fast Alternative                                   │
├─────────────────────────────────────────────────────────────────────┤
│  Model ID:    meta-llama/Llama-3.2-3B-Instruct                     │
│  Size:        ~3GB                                                  │
│  RAM:         8GB                                                   │
│  Speed:       ⚡⚡⚡ (Similar to Gemma 3B)                             │
│  Strength:    Good for general text analysis                        │
╰─────────────────────────────────────────────────────────────────────╯
    """)
    
    print("📝 Config:")
    print("""
    model:
      name: "meta-llama/Llama-3.2-3B-Instruct"
      device: "auto"
      quantization: "int8"
    """)
    
    print("""
╭─────────────────────────────────────────────────────────────────────╮
│  Mistral 7B - Balanced Alternative                                 │
├─────────────────────────────────────────────────────────────────────┤
│  Model ID:    mistralai/Mistral-7B-Instruct-v0.3                   │
│  Size:        ~7GB                                                  │
│  RAM:         16GB                                                  │
│  Speed:       ⚡⚡ (Similar to Gemma 9B)                              │
│  Strength:    Strong reasoning capabilities                         │
╰─────────────────────────────────────────────────────────────────────╯
    """)
    
    print("📝 Config:")
    print("""
    model:
      name: "mistralai/Mistral-7B-Instruct-v0.3"
      device: "auto"
      quantization: "int8"
    """)
    
    print("""
╭─────────────────────────────────────────────────────────────────────╮
│  Qwen 2.5 7B - Multilingual Alternative                            │
├─────────────────────────────────────────────────────────────────────┤
│  Model ID:    Qwen/Qwen2.5-7B-Instruct                             │
│  Size:        ~7GB                                                  │
│  RAM:         16GB                                                  │
│  Speed:       ⚡⚡                                                     │
│  Strength:    Excellent multilingual support                        │
╰─────────────────────────────────────────────────────────────────────╯
    """)
    
    print("📝 Config:")
    print("""
    model:
      name: "Qwen/Qwen2.5-7B-Instruct"
      device: "auto"
      quantization: "int8"
    """)


def showcase_cloud_apis():
    """Show cloud API alternatives."""
    print_section("☁️  Cloud API Options (No Download)")
    
    print("""
╭─────────────────────────────────────────────────────────────────────╮
│  OpenAI GPT-4o Mini - Fast Cloud API                               │
├─────────────────────────────────────────────────────────────────────┤
│  Model:       gpt-4o-mini                                           │
│  Cost:        ~$0.15 per 1M tokens                                  │
│  Speed:       ⚡⚡⚡ (~500ms per log)                                  │
│  Setup:       No download, API key only                             │
│  Strength:    Fast, accurate, no local resources                    │
╰─────────────────────────────────────────────────────────────────────╯
    """)
    
    print("📝 Config:")
    print("""
    model:
      provider: "openai"
      name: "gpt-4o-mini"
      api_key: "sk-..."  # or set OPENAI_API_KEY env var
    """)
    
    print("""
╭─────────────────────────────────────────────────────────────────────╮
│  Anthropic Claude 3 Haiku - Fast Cloud API                         │
├─────────────────────────────────────────────────────────────────────┤
│  Model:       claude-3-haiku-20240307                               │
│  Cost:        ~$0.25 per 1M tokens                                  │
│  Speed:       ⚡⚡⚡ (~400ms per log)                                  │
│  Setup:       No download, API key only                             │
│  Strength:    Fast inference, good reasoning                        │
╰─────────────────────────────────────────────────────────────────────╯
    """)
    
    print("📝 Config:")
    print("""
    model:
      provider: "anthropic"
      name: "claude-3-haiku-20240307"
      api_key: "sk-ant-..."  # or set ANTHROPIC_API_KEY env var
    """)


def showcase_comparison_table():
    """Show detailed comparison of all models."""
    print_section("📊 Complete Model Comparison")
    
    print("""
╭──────────────────┬─────────┬────────┬─────────┬──────────┬─────────────╮
│ Model            │ Download│  RAM   │ Speed   │ Accuracy │ Best For    │
├──────────────────┼─────────┼────────┼─────────┼──────────┼─────────────┤
│ Gemma 3 4B ★     │  4GB    │  8GB   │ ⚡⚡⚡     │ ⭐⭐⭐     │ Getting     │
│                  │         │        │         │          │ Started     │
├──────────────────┼─────────┼────────┼─────────┼──────────┼─────────────┤
│ Gemma 3 12B       │  12GB    │  16GB  │ ⚡⚡      │ ⭐⭐⭐⭐    │ Production  │
│                  │         │        │         │          │ Use         │
├──────────────────┼─────────┼────────┼─────────┼──────────┼─────────────┤
│ Gemma 3 27B      │  27GB   │  34GB  │ ⚡       │ ⭐⭐⭐⭐⭐   │ Max         │
│                  │         │        │         │          │ Accuracy    │
├──────────────────┼─────────┼────────┼─────────┼──────────┼─────────────┤
│ Llama 3.2 3B     │  3GB    │  8GB   │ ⚡⚡⚡     │ ⭐⭐⭐     │ Alternative │
├──────────────────┼─────────┼────────┼─────────┼──────────┼─────────────┤
│ Mistral 7B       │  7GB    │  16GB  │ ⚡⚡      │ ⭐⭐⭐⭐    │ Reasoning   │
├──────────────────┼─────────┼────────┼─────────┼──────────┼─────────────┤
│ Qwen 2.5 7B      │  7GB    │  16GB  │ ⚡⚡      │ ⭐⭐⭐⭐    │ Multi-      │
│                  │         │        │         │          │ lingual     │
├──────────────────┼─────────┼────────┼─────────┼──────────┼─────────────┤
│ GPT-4o Mini      │  None   │  None  │ ⚡⚡⚡     │ ⭐⭐⭐⭐⭐   │ Cloud API   │
│                  │ (API)   │ (API)  │         │          │ No Setup    │
├──────────────────┼─────────┼────────┼─────────┼──────────┼─────────────┤
│ Claude 3 Haiku   │  None   │  None  │ ⚡⚡⚡     │ ⭐⭐⭐⭐    │ Cloud API   │
│                  │ (API)   │ (API)  │         │          │ Fast        │
╰──────────────────┴─────────┴────────┴─────────┴──────────┴─────────────╯

★ = Default model (Gemma 3 4B)
    """)
    
    print("\n📌 Selection Guide:")
    print("""
  🚀 Starting out?           → Gemma 3 4B (default)
  ⚡ Need speed + accuracy?  → Gemma 3 4B or Llama 3.2 3B
  🎯 Production deployment?  → Gemma 3 12B or Mistral 7B
  🏆 Maximum accuracy?       → Gemma 3 27B
  🌍 Multilingual logs?      → Qwen 2.5 7B
  ☁️  No local resources?    → GPT-4o Mini or Claude
  💰 Budget conscious?       → Local models (Gemma 3B)
  🔒 Data privacy critical?  → Local models only
    """)


def performance_tips():
    """Show performance optimization tips."""
    print_section("⚡ Performance Optimization Tips")
    
    print("""
1️⃣  Quantization (Recommended)
   ├─ int8:  4x smaller, minimal accuracy loss
   ├─ fp16:  2x smaller, better accuracy
   └─ fp32:  Full precision, largest size

   model:
     quantization: "int8"  # Best balance

2️⃣  Device Selection
   ├─ auto:  Automatically choose best device
   ├─ cuda:  Use NVIDIA GPU (fastest)
   ├─ mps:   Use Apple Silicon GPU
   └─ cpu:   Use CPU (slowest)

   model:
     device: "auto"  # Recommended

3️⃣  Batch Processing
   detection:
     batch_size: 32     # Process logs in batches
     context_window: 100 # Include previous logs

4️⃣  Caching
   model:
     cache_dir: "./models"  # Avoid re-downloading

5️⃣  Hardware Acceleration
   • NVIDIA GPU: Install CUDA + cuDNN
   • Apple Silicon: Automatic with PyTorch
   • AMD GPU: ROCm support (experimental)

6️⃣  Memory Management
   • Use int8 for large models
   • Clear cache between runs
   • Process logs in smaller batches
   • Monitor RAM usage
    """)


def main():
    """Run the showcase."""
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║   💎 LogGem Model Showcase                                           ║
║   Comprehensive guide to lightweight LLM models                      ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝

This showcase demonstrates all available models for LogGem, helping you
choose the right model for your use case.
    """)
    
    # Show each model
    showcase_gemma_2b()      # Default: Fast & efficient
    showcase_gemma_9b()      # Balanced performance
    showcase_gemma_27b()     # Maximum accuracy
    showcase_alternatives()  # Other local models
    showcase_cloud_apis()    # Cloud options
    
    # Comparison and tips
    showcase_comparison_table()
    performance_tips()
    
    print_section("✅ Showcase Complete")
    print("""
🎯 Quick Recommendations:

  👉 New to LogGem?
     Start with Gemma 3 4B - it's fast, efficient, and works great!

  👉 Have 16GB+ RAM?
     Try Gemma 3 12B for better accuracy

  👉 Need best possible accuracy?
     Use Gemma 3 27B (requires 34GB RAM)

  👉 Want zero setup?
     Use OpenAI GPT-4o Mini or Claude 3 Haiku

  👉 Privacy concerns?
     Stick with local models (Gemma, Llama, Mistral)

📚 More Information:
  • README.md      - Full documentation
  • EXAMPLES.md    - More usage examples
  • config.yaml    - Configuration file
  • QUICKSTART.md  - Quick setup guide

💎 LogGem - Intelligent log analysis with lightweight LLMs!
    """)


if __name__ == "__main__":
    main()
