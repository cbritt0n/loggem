# LogGem Examples

I've put together some sample files and code examples to help you get started with LogGem.

## Sample Log Files

I've included several sample log files in this directory that you can use to try out LogGem:

- **`sample_auth.log`** - Linux authentication logs (SSH, sudo attempts)
- **`sample_nginx.log`** - Nginx access logs with various requests
- **`sample_json.log`** - JSON-formatted application logs

## Quick Try-Out

```bash
# I recommend starting with these simple examples

# Analyze authentication logs
loggem analyze examples/sample_auth.log --format auth

# Analyze nginx logs
loggem analyze examples/sample_nginx.log --format nginx

# Analyze JSON logs
loggem analyze examples/sample_json.log --format json
```

## Code Examples

### Basic Usage (`basic_usage.py`)

I've created a simple example showing how to use LogGem programmatically:

```python
from loggem import LogParserFactory, AnomalyDetector

# Parse and analyze logs
parser = LogParserFactory.create_parser(file_path="examples/sample_auth.log")
entries = list(parser.parse_file("examples/sample_auth.log"))

detector = AnomalyDetector()
anomalies = detector.detect_batch(entries)

print(f"I found {len(anomalies)} anomalies!")
```

Run it:
```bash
python examples/basic_usage.py
```

### Custom Parser (`custom_parser.py`)

I've also included an example showing how to create your own log parser:

```python
from loggem.parsers.base import BaseParser
from loggem.core.models import LogEntry

class MyCustomParser(BaseParser):
    def parse_line(self, line: str, line_number: int = 0):
        # Your custom parsing logic here
        # I've made the interface simple and flexible
        pass
```

Run it:
```bash
python examples/custom_parser.py
```

## More Examples

For more comprehensive examples, check out:

- **[EXAMPLES.md](../EXAMPLES.md)** - Complete examples guide I wrote
- **[README.md](../README.md)** - Main documentation with quick start
- **[ARCHITECTURE.md](../ARCHITECTURE.md)** - How I built LogGem

## Need Help?

If you have questions or need help with these examples:

- Open an issue on GitHub
- Check the documentation
- Join the discussions

---

**I hope these examples help you get started!** 🚀

*Made with 💎 by Christian Britton*
