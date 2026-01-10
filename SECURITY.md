# Security Policy

## Security Philosophy

This project follows an **embeddings-first, least-privilege** approach to security:

1. **Minimize raw log access**: Embeddings are the primary interface, not raw logs
2. **Gate sensitive operations**: Evidence access is tiered and audited
3. **Never auto-execute**: Response actions require human approval
4. **Redact by default**: PII redaction is enabled by default

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability, please:

1. **Do NOT** open a public GitHub issue
2. Email security concerns to the repository maintainers
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

We will respond within 48 hours and work with you to address the issue.

## Security Considerations

### Data Handling

- Sample data is synthetic and contains no real PII
- In production, ensure proper data classification
- Enable redaction for all evidence access
- Audit all data access operations

### MCP Server Security

- MCP servers should run in isolated environments
- Use appropriate authentication when deploying
- Rate limit API access
- Log all tool invocations

### Deployment

- Do not expose MCP servers directly to the internet
- Use TLS for all communications
- Rotate credentials regularly
- Follow principle of least privilege

## Security Features

### Tiered Access Control

| Tier | Access Level | Default |
|------|--------------|---------|
| 1 | Embeddings, findings, aggregations | Enabled |
| 2 | Evidence snippets (redacted) | Gated |
| 3 | Raw log export | Disabled |

### Audit Logging

All MCP tool invocations are logged with:
- Timestamp
- Tool name
- Parameters
- User/session
- Result status

### Redaction

Built-in redaction patterns for:
- Email addresses
- Phone numbers
- SSNs
- Credentials/tokens
- Session IDs

## Acknowledgments

We appreciate responsible disclosure of security issues.
