"""
Example: Basic log analysis workflow

Demonstrates LogGem's core features with multiple model options including
lightweight models like Gemma 3 4B, Gemma 3 12B, and Gemma 3 27B.
"""

from pathlib import Path
from loggem.parsers import LogParserFactory
from loggem.detector import AnomalyDetector
from loggem.analyzer import LogAnalyzer, PatternDetector


def print_banner():
    """Print example banner."""
    print("""
╔══════════════════════════════════════════════════════════╗
║  LogGem Basic Usage Example                              ║
║  AI-Powered Log Analysis with Lightweight Models         ║
╚══════════════════════════════════════════════════════════╝
    """)


def demo_rule_based_detection():
    """Demonstrate fast rule-based detection."""
    print("\n" + "="*60)
    print("  🔍 RULE-BASED DETECTION (No AI - Instant Results)")
    print("="*60)
    
    # 1. Parse logs
    print("\n📋 Parsing auth logs...")
    parser = LogParserFactory.create_parser(
        format_type="auth",
        file_path=Path("examples/sample_auth.log")
    )
    entries = list(parser.parse_file(Path("examples/sample_auth.log")))
    print(f"✅ Parsed {len(entries)} log entries")
    
    # 2. Rule-based detection (fast, no model needed)
    print("\n� Running rule-based pattern detection...")
    pattern_detector = PatternDetector()
    rule_anomalies = pattern_detector.detect_all(entries)
    print(f"✅ Found {len(rule_anomalies)} anomalies via rules")
    
    # 3. Analyze results
    print("\n📊 Analyzing results...")
    analyzer = LogAnalyzer()
    result = analyzer.analyze(entries, rule_anomalies)
    
    # 4. Display results
    print(f"\n{'='*60}")
    print("  📈 ANALYSIS RESULTS")
    print(f"{'='*60}")
    print(f"Total entries:     {result.total_entries}")
    print(f"Anomalies found:   {len(result.anomalies)}")
    print(f"Analysis duration: {result.duration:.2f}s")
    
    if result.anomalies:
        print(f"\n{'='*60}")
        print("  🚨 TOP ANOMALIES")
        print(f"{'='*60}")
        for i, anomaly in enumerate(result.anomalies[:5], 1):
            severity_emoji = {
                "CRITICAL": "🔴",
                "HIGH": "🟠", 
                "MEDIUM": "🟡",
                "LOW": "🟢"
            }.get(anomaly.severity.value, "⚪")
            
            print(f"\n{i}. {severity_emoji} [{anomaly.severity.value}] {anomaly.anomaly_type.value}")
            print(f"   Confidence:  {anomaly.confidence:.1%}")
            print(f"   Description: {anomaly.description}")
            if anomaly.recommendation:
                print(f"   💡 {anomaly.recommendation}")
    
    print(f"\n{'='*60}")
    print("  📊 PATTERNS DETECTED")
    print(f"{'='*60}")
    for pattern, count in result.patterns.items():
        print(f"  • {pattern}: {count}")


def demo_ai_detection_gemma_2b():
    """Demonstrate AI detection with Gemma 3 4B (default, fast)."""
    print("\n\n" + "="*60)
    print("  🤖 AI DETECTION - Gemma 3 4B (Fast & Efficient)")
    print("="*60)
    print("\n⚙️  Model: google/gemma-3-4b-it")
    print("💾 Size:  ~4GB download (first run only)")
    print("🧠 RAM:   8GB required")
    print("⚡ Speed: ~1-2s per log entry")
    print("\n💡 This is the default model - best for most users!")
    
    # Uncomment to enable AI detection:
    """
    from loggem.detector.model_manager import ModelManager
    
    # Initialize with Gemma 3 4B (default)
    print("\n📥 Loading Gemma 3 4B model...")
    manager = ModelManager(
        provider_type="huggingface",
        provider_config={
            "model_name": "google/gemma-3-4b-it",
            "device": "auto",  # Uses GPU if available
            "quantization": "int8",  # 4x smaller, minimal accuracy loss
        }
    )
    manager.load_model()
    
    # Parse and detect
    parser = LogParserFactory.create_parser("auth")
    entries = list(parser.parse_file(Path("examples/sample_auth.log")))[:10]
    
    print(f"🔍 Analyzing {len(entries)} entries with AI...")
    detector = AnomalyDetector()
    anomalies = []
    
    for i, entry in enumerate(entries, 1):
        print(f"  Processing {i}/{len(entries)}...", end="\\r")
        anomaly = detector.detect(entry)
        if anomaly:
            anomalies.append(anomaly)
    
    print(f"\\n✅ Found {len(anomalies)} AI-detected anomalies")
    """
    
    print("\n⚠️  AI detection commented out in example")
    print("   Uncomment code above to enable (requires model download)")


def demo_model_comparison():
    """Show comparison of different Gemma models."""
    print("\n\n" + "="*60)
    print("  📊 MODEL COMPARISON")
    print("="*60)
    print("""
╭──────────────────────────────────────────────────────────────────────╮
│  Model          │ Download │  RAM  │ Speed    │ Accuracy │ Use Case  │
├──────────────────────────────────────────────────────────────────────┤
│  Gemma 3 4B-it  │  ~4GB    │  8GB  │ ⚡⚡⚡     │ ⭐⭐⭐     │ Default   │
│                 │          │       │          │          │ Fast      │
│                 │          │       │          │          │ Efficient │
├──────────────────────────────────────────────────────────────────────┤
│  Gemma 3 12B-it  │  ~12GB    │ 16GB  │ ⚡⚡       │ ⭐⭐⭐⭐    │ Balanced  │
│                 │          │       │          │          │ Better    │
│                 │          │       │          │          │ Accuracy  │
├──────────────────────────────────────────────────────────────────────┤
│  Gemma 3 27B-it │  ~27GB   │ 34GB  │ ⚡        │ ⭐⭐⭐⭐⭐   │ Best      │
│                 │          │       │          │          │ Highest   │
│                 │          │       │          │          │ Quality   │
╰──────────────────────────────────────────────────────────────────────╯

💡 How to use different models:
""")
    
    print("\n1️⃣  Gemma 3 4B (Default) - config.yaml:")
    print("""
    model:
      provider: "huggingface"
      name: "google/gemma-3-4b-it"
      device: "auto"
      quantization: "int8"
    """)
    
    print("\n2️⃣  Gemma 3 12B (Better) - config.yaml:")
    print("""
    model:
      provider: "huggingface"
      name: "google/gemma-3-12b-it"
      device: "auto"
      quantization: "int8"
    """)
    
    print("\n3️⃣  Gemma 3 27B (Best) - config.yaml:")
    print("""
    model:
      provider: "huggingface"
      name: "google/gemma-3-27b-it"
      device: "auto"
      quantization: "int8"
    """)
    
    print("\n4️⃣  Alternative Models:")
    print("""
    # Llama 3.2 3B (Fast alternative)
    name: "meta-llama/Llama-3.2-3B-Instruct"
    
    # Mistral 7B (Balanced)
    name: "mistralai/Mistral-7B-Instruct-v0.3"
    
    # Qwen 2.5 7B (Good multilingual)
    name: "Qwen/Qwen2.5-7B-Instruct"
    """)


def main():
    """Run all demonstrations."""
    print_banner()
    
    print("""
This example demonstrates LogGem's capabilities:
  • Rule-based detection (instant, no AI)
  • AI detection with Gemma 3 models
  • Model comparison and selection

Choose the right model for your needs:
  • Gemma 3 4B:  Fast, 8GB RAM  ← Start here!
  • Gemma 3 12B:  Better, 16GB RAM
  • Gemma 3 27B: Best, 34GB RAM
""")
    
    # Demo 1: Fast rule-based detection
    demo_rule_based_detection()
    
    # Demo 2: AI detection with Gemma 3B
    demo_ai_detection_gemma_2b()
    
    # Demo 3: Model comparison
    demo_model_comparison()
    
    print("\n\n" + "="*60)
    print("  ✅ EXAMPLE COMPLETE")
    print("="*60)
    print("""
📚 Next Steps:
  1. Try enabling AI detection (uncomment code above)
  2. Experiment with different models in config.yaml
  3. Check examples/custom_parser.py for custom formats
  4. Read EXAMPLES.md for more advanced usage

💎 LogGem - Intelligent log analysis with lightweight LLMs!
    """)


if __name__ == "__main__":
    main()
