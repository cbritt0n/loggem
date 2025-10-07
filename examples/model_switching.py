"""
Example: Quick Model Switching

Demonstrates how to easily switch between different models
without modifying config files.
"""

from loggem.detector.model_manager import ModelManager
from loggem.parsers import LogParserFactory
from pathlib import Path


def test_model(model_config: dict, sample_log: str, model_desc: str):
    """Test a model with a sample log entry."""
    print(f"\n{'='*70}")
    print(f"  Testing: {model_desc}")
    print(f"{'='*70}")
    
    try:
        # Create manager with specific config
        manager = ModelManager(
            provider_type=model_config["provider"],
            provider_config=model_config["config"]
        )
        
        print(f"📥 Loading model: {model_config['config'].get('model_name', model_config['config'].get('model', 'N/A'))}")
        manager.load_model()
        
        print(f"🔍 Analyzing sample log...")
        prompt = f"""Analyze this log entry for security anomalies:

Log: {sample_log}

Provide a brief security assessment."""
        
        response = manager.generate_response(prompt)
        print(f"\n💬 Model Response:")
        print(f"   {response[:200]}..." if len(response) > 200 else f"   {response}")
        
        print(f"\n✅ Success!")
        
        # Cleanup
        manager.unload_model()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")


def main():
    """Demonstrate quick model switching."""
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║   🔄 Quick Model Switching Demo                                      ║
║   Test different models without changing config files               ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝

This example shows how to programmatically switch between models.
    """)
    
    # Sample log entry for testing
    sample_log = "Failed password for admin from 192.168.1.100 port 22 ssh2"
    
    print(f"\n📋 Sample Log Entry:")
    print(f"   {sample_log}")
    
    # Define model configurations
    models = {
        "gemma_2b": {
            "provider": "huggingface",
            "config": {
                "model_name": "google/gemma-3-4b-it",
                "device": "auto",
                "quantization": "int8",
            },
            "desc": "Gemma 3 4B - Fast & Efficient (8GB RAM)"
        },
        "gemma_9b": {
            "provider": "huggingface",
            "config": {
                "model_name": "google/gemma-3-12b-it",
                "device": "auto",
                "quantization": "int8",
            },
            "desc": "Gemma 3 12B - Balanced (16GB RAM)"
        },
        "llama_3b": {
            "provider": "huggingface",
            "config": {
                "model_name": "meta-llama/Llama-3.2-3B-Instruct",
                "device": "auto",
                "quantization": "int8",
            },
            "desc": "Llama 3.2 3B - Fast Alternative (8GB RAM)"
        },
        "mistral_7b": {
            "provider": "huggingface",
            "config": {
                "model_name": "mistralai/Mistral-7B-Instruct-v0.3",
                "device": "auto",
                "quantization": "int8",
            },
            "desc": "Mistral 7B - Strong Reasoning (16GB RAM)"
        },
        "qwen_7b": {
            "provider": "huggingface",
            "config": {
                "model_name": "Qwen/Qwen2.5-7B-Instruct",
                "device": "auto",
                "quantization": "int8",
            },
            "desc": "Qwen 2.5 7B - Multilingual (16GB RAM)"
        },
        "gpt4o_mini": {
            "provider": "openai",
            "config": {
                "model": "gpt-4o-mini",
                # API key from environment variable
            },
            "desc": "GPT-4o Mini - Fast Cloud API"
        },
        "claude_haiku": {
            "provider": "anthropic",
            "config": {
                "model": "claude-3-haiku-20240307",
                # API key from environment variable
            },
            "desc": "Claude 3 Haiku - Fast Cloud API"
        },
    }
    
    print(f"\n\n{'='*70}")
    print("  Available Models to Test")
    print(f"{'='*70}\n")
    
    for i, (key, model) in enumerate(models.items(), 1):
        print(f"{i}. {model['desc']}")
    
    print(f"\n{'='*70}")
    print("  Testing Models")
    print(f"{'='*70}")
    print("\n⚠️  Note: This will download models on first run (~2-27GB each)")
    print("⚠️  Cloud APIs require API keys in environment variables")
    print("⚠️  Models are tested sequentially - this may take time")
    
    # Test only Gemma 3B by default (comment out others to avoid large downloads)
    print("\n\n💡 Testing Gemma 3 4B only (uncomment others in code to test)")
    test_model(models["gemma_2b"], sample_log, models["gemma_2b"]["desc"])
    
    # Uncomment to test other models:
    # test_model(models["gemma_9b"], sample_log, models["gemma_9b"]["desc"])
    # test_model(models["llama_3b"], sample_log, models["llama_3b"]["desc"])
    # test_model(models["mistral_7b"], sample_log, models["mistral_7b"]["desc"])
    # test_model(models["qwen_7b"], sample_log, models["qwen_7b"]["desc"])
    # test_model(models["gpt4o_mini"], sample_log, models["gpt4o_mini"]["desc"])
    # test_model(models["claude_haiku"], sample_log, models["claude_haiku"]["desc"])
    
    print(f"\n\n{'='*70}")
    print("  💡 Model Switching Tips")
    print(f"{'='*70}\n")
    print("""
1️⃣  Programmatic Switching (this example):
   
   manager = ModelManager(
       provider_type="huggingface",
       provider_config={"model_name": "google/gemma-3-12b-it"}
   )

2️⃣  Config File (config.yaml):
   
   model:
     provider: "huggingface"
     name: "google/gemma-3-12b-it"

3️⃣  Environment Variables:
   
   export LOGGEM_MODEL__PROVIDER="huggingface"
   export LOGGEM_MODEL__NAME="google/gemma-3-12b-it"

4️⃣  Command Line (future feature):
   
   loggem analyze auth.log --model gemma-3-12b-it

📊 Performance Tips:

  • Start with Gemma 3 4B (8GB RAM)
  • Upgrade to 9B if you have 16GB RAM
  • Use int8 quantization to save memory
  • Cloud APIs (OpenAI/Anthropic) need no local resources
  • Local models = data privacy + no API costs
  • GPU acceleration = 5-10x faster inference

🔒 Privacy Considerations:

  • Local models (Gemma, Llama, Mistral, Qwen): 100% private
  • Cloud APIs (OpenAI, Anthropic): Logs sent to provider
  • Use local models for sensitive data
    """)
    
    print(f"\n{'='*70}")
    print("  ✅ Demo Complete")
    print(f"{'='*70}\n")
    print("""
📚 Next Steps:
  1. Test different models by uncommenting code above
  2. Compare model outputs for your specific logs
  3. Choose the best model for your use case
  4. Update config.yaml with your choice
  5. Check examples/model_showcase.py for detailed comparison

💎 LogGem - Flexible model selection for every need!
    """)


if __name__ == "__main__":
    main()
