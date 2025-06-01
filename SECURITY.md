# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

## Reporting a Vulnerability

We take the security of LLM Pipeline seriously. If you believe you've found a security vulnerability, please follow these steps:

1. **Do not disclose the vulnerability publicly**
2. Email us at [artisanllmframeworks@gmail.com] with details about the vulnerability
3. Allow time for us to assess and address the vulnerability before any public disclosure
4. We will acknowledge receipt of your report within 48 hours

## LLM-Specific Security Considerations

### Prompt Injection Risks

LLM Pipeline provides some safeguards against prompt injection attacks through input validation and preprocessing. However, users should be aware of the following best practices:

- Always validate and sanitize user inputs before passing them to the pipeline
- Consider implementing additional application-specific input filtering
- Review generated prompts and outputs for potential security issues

### API Key Protection

- Never hardcode API keys in your application
- Use environment variables or secure secret management systems
- Implement appropriate access controls and key rotation practices
- Monitor API usage for unexpected patterns that may indicate compromise

### Data Privacy

- Be mindful of what data is sent to external LLM providers
- Consider data residency and compliance requirements
- Implement appropriate logging practices that don't expose sensitive information
- Review the privacy policies of any LLM providers you integrate with

### Mitigations

LLM Pipeline implements several security features:

- Input validation using Pydantic schemas
- Configurable input preprocessing
- API key storage via environment variables
- Error handling that avoids leaking sensitive information
- Timeouts to prevent request blocking

## Security Updates

Security updates will be released as patch versions and announced through GitHub releases. Users are encouraged to stay updated with the latest security patches.