# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability in LogGem, please report it responsibly:

1. **DO NOT** open a public GitHub issue
2. Email security details to: security@loggem.dev (or create a private security advisory)
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

We will respond within 48 hours and provide a timeline for a fix.

## Security Features

LogGem implements several security measures:

- **Input Sanitization**: All log entries are validated and sanitized
- **No Remote Code Execution**: Models run in isolated environments
- **Audit Logging**: Complete audit trail of all operations
- **Secure Defaults**: Conservative security settings out of the box
- **Dependency Scanning**: Regular updates to address CVEs
- **Rate Limiting**: Protection against resource exhaustion

## Best Practices

When using LogGem:

1. Run with minimal required permissions
2. Keep dependencies updated
3. Use read-only access to log files when possible
4. Enable audit logging
5. Review anomaly reports regularly
6. Isolate LogGem in a secure environment for sensitive logs

## Disclosure Policy

We follow responsible disclosure:

1. Vulnerability reported privately
2. Patch developed and tested
3. Security advisory published
4. Public disclosure after patch release
