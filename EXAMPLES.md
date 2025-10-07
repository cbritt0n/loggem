# LogGem Examples

I've put together these examples to help you get the most out of LogGem. From basic usage to advanced integrations, you'll find practical code samples here.

## Quick Start Examples

### Analyze a Single Log File

```bash
# I've made it simple - just point LogGem at your log file
loggem analyze /var/log/auth.log

# Want to see more details? Add verbose mode
loggem analyze /var/log/auth.log --verbose

# Need the results in JSON? I've got you covered
loggem analyze /var/log/auth.log --output report.json
```

### Real-Time Log Monitoring

```bash
# Watch logs as they grow (like tail -f, but smarter)
loggem watch /var/log/syslog

# Monitor multiple files at once
loggem watch /var/log/auth.log /var/log/nginx/access.log
```

## Python API Examples

### Basic Analysis

```python
from loggem import LogParserFactory, AnomalyDetector, LogAnalyzer

# I've made the API intuitive - here's a basic example
def analyze_log_file(filepath):
    """Analyze a log file and print results."""
    
    # Parse the log file
    parser = LogParserFactory.create_parser(file_path=filepath)
    entries = list(parser.parse_file(filepath))
    
    print(f"Parsed {len(entries)} log entries")
    
    # Detect anomalies using AI
    detector = AnomalyDetector()
    anomalies = detector.detect_batch(entries)
    
    print(f"Found {len(anomalies)} anomalies")
    
    # Get statistical analysis
    analyzer = LogAnalyzer()
    result = analyzer.analyze(entries, anomalies)
    
    return result

# Run it
result = analyze_log_file("/var/log/auth.log")
print(f"Analysis complete! Check out the {len(result.anomalies)} findings.")
```

### Custom Parser Example

```python
from loggem.parsers.base import BaseParser
from loggem.core.models import LogEntry
from datetime import datetime

class MyCustomParser(BaseParser):
    """
    I've designed the parser interface to be super flexible.
    Here's how you can create your own!
    """
    
    def parse_line(self, line: str, line_number: int = 0) -> LogEntry | None:
        """Parse a custom log format."""
        
        # Skip empty lines
        if not line.strip():
            return None
        
        # Your custom parsing logic here
        # This is just an example
        parts = line.split('|')
        if len(parts) < 3:
            return None
        
        return LogEntry(
            timestamp=datetime.fromisoformat(parts[0].strip()),
            level=parts[1].strip(),
            message=parts[2].strip(),
            raw=line,
            source="custom",
            line_number=line_number
        )

# Use your custom parser
parser = MyCustomParser()
entries = list(parser.parse_file("my_custom_format.log"))
print(f"I parsed {len(entries)} entries using your custom format!")
```

## Configuration Examples

### HuggingFace (Local Models)

```yaml
# config.yaml - I recommend starting with this for privacy
model:
  provider: "huggingface"
  name: "google/gemma-3-4b-it"  # I've set this as the default
  device: "auto"  # I'll automatically detect your best option
  quantization: "int8"  # Saves memory - I recommend this
  cache_dir: "./models"

detection:
  sensitivity: 0.75  # I've tuned this as a good starting point
  batch_size: 32
```

### OpenAI Configuration

```yaml
# config.yaml - Great for highest accuracy
model:
  provider: "openai"
  name: "gpt-4o-mini"  # I find this gives great results at low cost
  api_key: null  # I'll read from OPENAI_API_KEY env var

detection:
  sensitivity: 0.8
  batch_size: 64  # Cloud APIs handle larger batches well
```

### Anthropic (Claude)

```yaml
# config.yaml - I love Claude for its reasoning abilities
model:
  provider: "anthropic"
  name: "claude-3-haiku-20240307"  # Fast and affordable
  api_key: null  # Set ANTHROPIC_API_KEY env var

detection:
  sensitivity: 0.75
```

## Integration Examples

### Cron Job for Scheduled Analysis

```bash
# I've set up my system to analyze logs hourly
# Add this to your crontab (crontab -e):

# Analyze auth logs every hour
0 * * * * /path/to/venv/bin/loggem analyze /var/log/auth.log --output /var/log/loggem/auth_$(date +\%Y\%m\%d_\%H).json

# Analyze nginx logs every 6 hours
0 */6 * * * /path/to/venv/bin/loggem analyze /var/log/nginx/access.log --format nginx --output /var/log/loggem/nginx_$(date +\%Y\%m\%d).json
```

### Systemd Service

```ini
# /etc/systemd/system/loggem.service
# I recommend running LogGem as a service for continuous monitoring

[Unit]
Description=LogGem Log Anomaly Detection Service
After=network.target

[Service]
Type=simple
User=loggem
Group=loggem
WorkingDirectory=/home/loggem/loggem
Environment="PATH=/home/loggem/loggem/venv/bin"
ExecStart=/home/loggem/loggem/venv/bin/loggem watch /var/log/syslog
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Docker Integration

```dockerfile
# Dockerfile - I've made it easy to containerize
FROM python:3.9-slim

WORKDIR /app

# Install LogGem
RUN pip install loggem[huggingface]

# Create volume mounts
VOLUME ["/logs", "/models", "/output"]

# Set environment variables
ENV LOGGEM_MODEL__CACHE_DIR=/models
ENV LOGGEM_MODEL__DEVICE=cpu

ENTRYPOINT ["loggem"]
CMD ["analyze", "/logs/syslog", "--output", "/output/report.json"]
```

```bash
# Run with Docker
docker build -t loggem .
docker run --rm \
  -v $(pwd)/logs:/logs:ro \
  -v $(pwd)/models:/models \
  -v $(pwd)/output:/output \
  loggem analyze /logs/auth.log
```

## Advanced Examples

### Streaming with Custom Callbacks

```python
from loggem.streaming import LogStreamer
from loggem.detector import AnomalyDetector

# I've designed the streaming API to be event-driven
def monitor_logs_realtime(filepath):
    """Monitor logs in real-time with custom handling."""
    
    detector = AnomalyDetector()
    
    with LogStreamer(filepath, follow=True) as streamer:
        for event in streamer.iter_events():
            # Analyze each new entry as it arrives
            result = detector.analyze_entry(event.entry)
            
            if result.anomalies:
                anomaly = result.anomalies[0]
                print(f"🚨 Alert! {anomaly.severity.value.upper()}: {anomaly.reasoning}")
                
                # You can add your custom handling here
                # - Send to Slack
                # - Write to database
                # - Trigger automation
                # I've made it flexible for your needs!

# Run it
monitor_logs_realtime("/var/log/auth.log")
```

### Multi-Channel Alerting

```python
from loggem.alerting import (
    AlertManager, 
    SlackChannel, 
    EmailChannel,
    create_high_score_rule,
    create_severity_rule
)

# I've built a powerful alerting system - here's how to use it
def setup_alerting():
    """Configure multi-channel alerting."""
    
    manager = AlertManager()
    
    # Add alerting rules (I've provided some useful presets)
    manager.add_rule(create_high_score_rule(threshold=0.8))
    manager.add_rule(create_severity_rule(min_severity="high"))
    
    # Configure Slack alerts
    slack = SlackChannel(
        webhook_url="your-webhook-url",
        channel="#security-alerts"
    )
    manager.add_channel("slack", slack)
    
    # Configure email alerts  
    email = EmailChannel(
        smtp_server="smtp.gmail.com",
        smtp_port=587,
        from_addr="alerts@yourcompany.com",
        to_addrs=["security@yourcompany.com"]
    )
    manager.add_channel("email", email)
    
    return manager

# Use it
alert_manager = setup_alerting()

# When you find anomalies, I'll route them to the right channels
for anomaly in anomalies:
    alert_manager.process_anomaly(anomaly)
```

### Batch Processing for High Throughput

```python
from loggem.performance import BatchProcessor
from loggem.detector import AnomalyDetector

# I've optimized this for handling large volumes
def process_large_logfile(filepath):
    """Process large log files efficiently."""
    
    parser = LogParserFactory.create_parser(file_path=filepath)
    entries = list(parser.parse_file(filepath))
    
    print(f"I'm processing {len(entries)} entries in batches...")
    
    # I use parallel processing to speed things up
    processor = BatchProcessor(batch_size=100, max_workers=4)
    detector = AnomalyDetector()
    
    # Process in batches
    results = processor.process_entries(
        entries,
        lambda batch: detector.detect_batch(batch)
    )
    
    # Flatten results
    all_anomalies = [a for batch_result in results for a in batch_result]
    
    print(f"Done! I found {len(all_anomalies)} anomalies.")
    return all_anomalies
```

### Report Generation

```python
from loggem.reporting import ReportGenerator

# I've made it easy to generate beautiful reports
def generate_analysis_report(result, output_dir="./reports"):
    """Generate comprehensive analysis reports."""
    
    report = ReportGenerator(result)
    
    # I can export to multiple formats
    print("Generating reports...")
    
    report.export_json(f"{output_dir}/analysis.json")
    print(f"✓ JSON report saved")
    
    report.export_csv(f"{output_dir}/anomalies.csv")
    print(f"✓ CSV report saved")
    
    report.export_html(f"{output_dir}/report.html")
    print(f"✓ HTML report saved (open this in your browser!)")
    
    # I also provide a nice terminal summary
    report.print_summary()
```

## Tips and Tricks

### Performance Optimization

```python
# I've found these settings work well for different scenarios

# For fast analysis (less accuracy)
config = {
    "model": {
        "provider": "huggingface",
        "name": "google/gemma-3-4b-it",
        "quantization": "int8"
    },
    "detection": {
        "batch_size": 64,
        "sensitivity": 0.7
    }
}

# For high accuracy (slower)
config = {
    "model": {
        "provider": "openai",
        "name": "gpt-4o"
    },
    "detection": {
        "batch_size": 32,
        "sensitivity": 0.85
    }
}

# For maximum privacy (fully offline)
config = {
    "model": {
        "provider": "huggingface",
        "name": "google/gemma-3-4b-it",
        "device": "cpu",
        "quantization": "int8"
    }
}
```

### Error Handling

```python
from loggem.core.models import LogEntry
from loggem.parsers import LogParserFactory

# I always recommend good error handling
def robust_log_analysis(filepath):
    """Analyze logs with proper error handling."""
    
    try:
        parser = LogParserFactory.create_parser(file_path=filepath)
        entries = list(parser.parse_file(filepath))
        
        if not entries:
            print("No entries found - check your log format")
            return None
        
        detector = AnomalyDetector()
        anomalies = detector.detect_batch(entries)
        
        return anomalies
        
    except FileNotFoundError:
        print(f"I couldn't find {filepath} - check the path")
    except PermissionError:
        print(f"I don't have permission to read {filepath}")
    except Exception as e:
        print(f"Something went wrong: {e}")
        print("Try running with --verbose for more details")
    
    return None
```

## Need More Help?

- Check out the [README.md](README.md) for complete documentation
- See [ARCHITECTURE.md](ARCHITECTURE.md) to understand how I built LogGem
- Read [DEPLOYMENT.md](DEPLOYMENT.md) for production deployment
- Visit [TESTING.md](TESTING.md) to learn about testing

---

**I hope these examples help you get started with LogGem! If you create something cool, I'd love to hear about it!** 🚀

*Made with 💎 by Christian Britton for the community*
