# Security Policy

I take the security of LogGem seriously. Here's everything you need to know about security in LogGem and how to report vulnerabilities.

## Supported Versions

I'm currently providing security updates for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | ✅ Yes             |
| < 1.0   | ❌ No              |

## Reporting a Vulnerability

If you discover a security vulnerability in LogGem, I want to know about it! Here's how to report it:

### Please Do

1. **Email me directly** at the security contact listed in the repository
2. **Provide detailed information** including:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if you have one)
3. **Give me reasonable time** to respond before public disclosure
4. **Act in good faith** - don't exploit the vulnerability

### Please Don't

- Don't open a public GitHub issue for security vulnerabilities
- Don't exploit the vulnerability beyond what's needed to demonstrate it
- Don't share the vulnerability publicly until I've had time to fix it

### What I'll Do

When you report a vulnerability, I will:

1. **Acknowledge receipt** within 48 hours
2. **Provide an initial assessment** within 7 days
3. **Keep you updated** on my progress fixing the issue
4. **Credit you** in the security advisory (if you'd like)
5. **Notify you** when the fix is released

## Security Features

I've built several security features into LogGem:

### Data Privacy

- **Local Processing**: I designed LogGem to run completely offline with local models
- **No Data Exfiltration**: Your logs never leave your network when using HuggingFace models
- **Secure by Default**: All sensitive data stays on your infrastructure

### Input Validation

- **Sanitization**: I sanitize all log entries before processing
- **Size Limits**: Maximum line lengths enforced to prevent resource exhaustion
- **Character Filtering**: Control characters are removed for safety

### Model Security

- **No Remote Code Execution**: I've disabled `trust_remote_code` by default
- **Verified Sources**: Models are downloaded from trusted sources only
- **Checksum Verification**: Model integrity is verified on download

### Audit Logging

- **Complete Audit Trail**: I log all operations to a separate audit log
- **Security Events**: Special tracking for security-relevant events
- **Tamper-Evident**: Audit logs use append-only writes

### API Key Security

When using cloud providers, I recommend:

```yaml
# Don't put API keys in config files!
# I'll read from environment variables instead
model:
  provider: "openai"
  api_key: null  # I'll check OPENAI_API_KEY env var

# Or use a secrets manager
# I support reading from various secret stores
```

## Best Practices

Here's what I recommend for secure deployment:

### 1. Use Local Models When Possible

```yaml
# Most secure - everything stays local
model:
  provider: "huggingface"
  name: "google/gemma-3-4b-it"
  device: "cpu"
```

### 2. Run as Non-Root User

```bash
# I recommend creating a dedicated user
sudo useradd -r -s /bin/false loggem
sudo -u loggem loggem analyze /var/log/auth.log
```

### 3. Limit File Permissions

```bash
# Give LogGem read-only access to logs
chmod 640 /var/log/*.log
chown root:loggem /var/log/*.log
```

### 4. Network Isolation

- I don't require network access for analysis (with local models)
- Consider air-gapped deployment for sensitive environments
- Use firewall rules to restrict network access if needed

### 5. Regular Updates

```bash
# I release security updates promptly
# Keep LogGem updated:
pip install --upgrade loggem
```

### 6. Secure Configuration

```yaml
# I've set secure defaults, but you can harden further
security:
  enable_audit_log: true
  max_line_length: 10000
  sanitize_input: true
  
logging:
  level: "INFO"  # Avoid DEBUG in production
  file: "/var/log/loggem/loggem.log"
```

### 7. Monitor Audit Logs

```bash
# I write detailed audit logs
tail -f loggem_data/audit.log

# Check for security events
grep "security_event" loggem_data/audit.log
```

## Known Security Considerations

I want to be transparent about potential security considerations:

### LLM Provider APIs

When using cloud APIs (OpenAI, Anthropic):
- Log content is sent to third-party services
- Subject to provider's data handling policies
- May not be suitable for sensitive logs
- **I recommend local models for sensitive data**

### Model Downloads

- Models are downloaded on first use
- Downloaded from HuggingFace Hub or provider APIs
- Checksums are verified, but supply chain risk exists
- **I recommend reviewing model sources before use**

### Python Dependencies

- LogGem depends on various Python packages
- I use `pip` dependency resolution
- Vulnerabilities in dependencies are possible
- **I regularly update dependencies and monitor security advisories**

### Log Content Exposure

- Parsed logs are kept in memory during processing
- Anomalies may be written to reports
- **I recommend securing report outputs appropriately**

## Security Updates

I monitor for security issues through:

- **Dependency scanning**: I use `safety` and `bandit` in CI/CD
- **GitHub Security Advisories**: I monitor for reported vulnerabilities
- **Community reports**: I appreciate security researchers' contributions

### How I Release Security Updates

1. **Urgent fixes** (Critical/High severity):
   - I release patches within 24-48 hours
   - Notify users via GitHub Security Advisory
   - Update documentation

2. **Important fixes** (Medium severity):
   - I include in next minor release (within 1-2 weeks)
   - Document in release notes
   - Update security policy

3. **Low severity issues**:
   - I address in regular maintenance releases
   - Track in GitHub Issues
   - Include in release notes

## Compliance

LogGem can help with security compliance requirements:

- **HIPAA**: Use local models to keep PHI on-premises
- **PCI-DSS**: Monitor access logs for audit trails
- **SOC 2**: Audit logging for security monitoring
- **GDPR**: Local processing for data privacy

I've designed LogGem with compliance in mind, but **you're responsible for your own compliance requirements**.

## Security Testing

I take testing seriously:

- **142 passing tests** with 56% code coverage
- **Static analysis** with ruff and bandit
- **Dependency scanning** with safety
- **Multi-OS testing** on Ubuntu, macOS, Windows
- **Code review** for all changes

### Run Security Tests Yourself

```bash
# I've included security scanning tools
pip install loggem[dev]

# Run security scanner
bandit -r src/

# Check dependencies
safety check

# Run all tests
pytest tests/ --cov=loggem
```

## Disclosure Policy

I follow **responsible disclosure**:

- **90 days** to fix before public disclosure (negotiable)
- I'll coordinate disclosure timing with reporters
- Security advisories published on GitHub
- CVEs requested for significant vulnerabilities

## Bug Bounty

I don't currently offer a bug bounty program, but I deeply appreciate security researchers' contributions! I'll publicly credit you (with your permission) for any vulnerabilities you report.

## Questions?

Have security questions? Here's how to reach me:

- **Security issues**: Use private security reporting (see repository)
- **General questions**: Open a GitHub Discussion
- **Documentation**: Check [DEPLOYMENT.md](DEPLOYMENT.md) for secure deployment

---

**I'm committed to keeping LogGem secure. Thank you for helping me do that!** 🔒

*Made with 💎 by Christian Britton*
