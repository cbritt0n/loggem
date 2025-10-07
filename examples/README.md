# LogGem Examples

Comprehensive examples demonstrating LogGem's features with different lightweight models.

## 📚 Available Examples

### 1. **basic_usage.py** - Start Here! 🚀
Learn LogGem fundamentals with rule-based and AI detection.

```bash
python examples/basic_usage.py
```

**Demonstrates:**
- Log parsing
- Rule-based detection (instant, no model download)
- AI detection setup (commented)
- Result analysis
- Model comparison

**Best for:** First-time users, understanding the workflow

---

### 2. **model_showcase.py** - Model Deep Dive 🤖
Comprehensive guide to all available models.

```bash
python examples/model_showcase.py
```

**Demonstrates:**
- Gemma 3 4B (default, fast, 8GB RAM)
- Gemma 3 12B (balanced, 16GB RAM)
- Gemma 3 27B (best, 34GB RAM)
- Alternative models (Llama, Mistral, Qwen)
- Cloud APIs (OpenAI, Anthropic)
- Performance comparison
- Optimization tips

**Best for:** Choosing the right model for your needs

---

### 3. **model_switching.py** - Dynamic Model Selection 🔄
Switch between models programmatically.

```bash
python examples/model_switching.py
```

**Demonstrates:**
- Programmatic model switching
- Testing multiple models
- Config-free model selection
- Performance comparison
- Memory management

**Best for:** Testing different models, advanced users

---

### 4. **custom_parser.py** - Custom Log Formats 📝
Create parsers for custom log formats.

```bash
python examples/custom_parser.py
```

**Demonstrates:**
- Creating custom parsers
- Parser registration
- Custom regex patterns
- Metadata extraction

**Best for:** Non-standard log formats

---

## 🎯 Quick Start by Use Case

### "I'm just getting started"
→ Run `basic_usage.py` with rule-based detection (no model download)

### "I want to use AI detection"
→ Start with Gemma 3 4B (default, 8GB RAM)
```bash
# First, ensure HuggingFace installed
pip install -e ".[huggingface]"

# Then run
python examples/basic_usage.py
```

### "I have 16GB RAM and want better accuracy"
→ Use Gemma 3 12B in `config.yaml`:
```yaml
model:
  name: "google/gemma-3-12b-it"
```

### "I need the best possible accuracy"
→ Use Gemma 3 27B (requires 34GB RAM):
```yaml
model:
  name: "google/gemma-3-27b-it"
```

### "I don't want to download models"
→ Use cloud APIs (OpenAI/Anthropic) - see `model_showcase.py`

### "My logs use a custom format"
→ Check `custom_parser.py` for creating custom parsers

---

## 🤖 Model Selection Guide

### Quick Comparison

| Model | RAM | Download | Speed | Accuracy | Best For |
|-------|-----|----------|-------|----------|----------|
| **Gemma 3 4B** ⭐ | 8GB | 4GB | ⚡⚡⚡ | ⭐⭐⭐ | Getting started |
| **Gemma 3 12B** | 16GB | 12GB | ⚡⚡ | ⭐⭐⭐⭐ | Production |
| **Gemma 3 27B** | 34GB | 27GB | ⚡ | ⭐⭐⭐⭐⭐ | Max accuracy |
| **Llama 3.2 3B** | 8GB | 3GB | ⚡⚡⚡ | ⭐⭐⭐ | Alternative |
| **Mistral 7B** | 16GB | 7GB | ⚡⚡ | ⭐⭐⭐⭐ | Reasoning |
| **Qwen 2.5 7B** | 16GB | 7GB | ⚡⚡ | ⭐⭐⭐⭐ | Multilingual |
| **GPT-4o Mini** | 0 | 0 | ⚡⚡⚡ | ⭐⭐⭐⭐⭐ | Cloud API |

⭐ = Default model

### Decision Tree

```
Do you have sensitive data?
├─ Yes → Use local models (Gemma, Llama, Mistral)
└─ No  → Cloud APIs OK (OpenAI, Anthropic)

How much RAM do you have?
├─ 8GB  → Gemma 3 4B or Llama 3.2 3B
├─ 16GB → Gemma 3 12B or Mistral 7B
└─ 34GB → Gemma 3 27B

What's your priority?
├─ Speed        → Gemma 3 4B or cloud APIs
├─ Accuracy     → Gemma 3 27B or GPT-4o
├─ Balance      → Gemma 3 12B
└─ Multilingual → Qwen 2.5 7B
```

---

## 📦 Installation by Model

### Gemma Models (HuggingFace)
```bash
pip install -e ".[huggingface]"
```

### OpenAI
```bash
pip install -e ".[openai]"
export OPENAI_API_KEY="sk-..."
```

### Anthropic
```bash
pip install -e ".[anthropic]"
export ANTHROPIC_API_KEY="sk-ant-..."
```

### Ollama
```bash
pip install -e ".[ollama]"
ollama pull llama3  # or mistral, gemma, etc.
```

---

## 🔧 Configuration

### Gemma 3 4B (Default)
```yaml
# config.yaml
model:
  provider: "huggingface"
  name: "google/gemma-3-4b-it"
  device: "auto"
  quantization: "int8"
```

### Gemma 3 12B
```yaml
model:
  provider: "huggingface"
  name: "google/gemma-3-12b-it"
  device: "auto"
  quantization: "int8"
```

### Gemma 3 27B
```yaml
model:
  provider: "huggingface"
  name: "google/gemma-3-27b-it"
  device: "cuda"  # GPU recommended
  quantization: "int8"
```

### Cloud APIs
```yaml
# OpenAI
model:
  provider: "openai"
  name: "gpt-4o-mini"

# Anthropic
model:
  provider: "anthropic"
  name: "claude-3-haiku-20240307"
```

---

## 💡 Pro Tips

1. **Start Small**: Begin with Gemma 3 4B, upgrade if needed
2. **Use Quantization**: `int8` saves 4x memory with minimal accuracy loss
3. **GPU Acceleration**: Set `device: "cuda"` for 5-10x speedup
4. **Batch Processing**: Process multiple logs at once for efficiency
5. **Rule-Based First**: Use `--no-ai` for instant results, add AI later
6. **Cloud for Testing**: Try cloud APIs first (no download), switch to local if needed
7. **Privacy Matters**: Use local models for sensitive data

---

## 📊 Sample Data

The `examples/` directory includes sample log files:
- `sample_auth.log` - Authentication logs (syslog format)
- `sample_nginx.log` - Nginx access logs
- `sample_json.log` - JSON application logs

---

## 🚀 Next Steps

1. **Try examples** in order (basic_usage → model_showcase → model_switching)
2. **Choose your model** based on RAM and accuracy needs
3. **Update config.yaml** with your preferred model
4. **Analyze your logs** with `loggem analyze your_logs.log`
5. **Read documentation**:
   - `../README.md` - Full documentation
   - `../EXAMPLES.md` - More usage examples
   - `../QUICKSTART.md` - Quick setup guide
   - `../TESTING.md` - Development guide

---

## 🆘 Need Help?

- **Getting Started**: Run `basic_usage.py`
- **Model Selection**: Run `model_showcase.py`
- **Custom Formats**: Check `custom_parser.py`
- **Documentation**: See `../README.md`
- **Issues**: Check GitHub issues

---

## 💎 LogGem Philosophy

**Start Simple, Scale Up**

1. Start with rule-based detection (`--no-ai`)
2. Add Gemma 3 4B when ready (8GB RAM)
3. Upgrade to 9B if you need more accuracy (16GB RAM)
4. Go to 27B for mission-critical systems (34GB RAM)
5. Or use cloud APIs if you prefer (no local resources)

**Privacy First**

- Local models = complete privacy
- Your logs never leave your machine
- No API calls, no data sharing
- Perfect for sensitive data

**Performance Optimized**

- Lightweight models (2B-27B parameters)
- Smart quantization (int8 = 4x smaller)
- GPU acceleration when available
- Batch processing for efficiency

---

**Happy log hunting with LogGem!** 💎
