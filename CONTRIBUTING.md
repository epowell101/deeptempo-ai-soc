# Contributing to DeepTempo AI SOC

Thank you for your interest in contributing to the DeepTempo Embeddings-First AI SOC project!

## How to Contribute

### Reporting Issues

- Use GitHub Issues to report bugs or suggest features
- Check existing issues before creating a new one
- Provide as much detail as possible:
  - Steps to reproduce
  - Expected vs actual behavior
  - Environment details (OS, Python version)

### Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests if available
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Code Style

- Follow PEP 8 for Python code
- Use type hints where appropriate
- Write docstrings for functions and classes
- Keep functions focused and small

### Commit Messages

- Use clear, descriptive commit messages
- Start with a verb (Add, Fix, Update, Remove)
- Reference issues when applicable

### Areas for Contribution

- **Skills**: New Claude Skills for SOC workflows
- **MCP Servers**: Additional MCP server functionality
- **Documentation**: Improvements to docs and examples
- **Adapters**: New data source adapters
- **Tests**: Unit and integration tests

## Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/deeptempo-embeddings-first-ai-soc.git
cd deeptempo-embeddings-first-ai-soc

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Run demo to verify setup
python scripts/demo.py
```

## Questions?

Open an issue with the "question" label or reach out to the maintainers.

## License

By contributing, you agree that your contributions will be licensed under the Apache 2.0 License.
