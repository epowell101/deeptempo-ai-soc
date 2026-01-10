# Installation Guide

This guide will help you install and set up the DeepTempo AI SOC desktop application.

## Prerequisites

- **Python 3.10 or higher** - [Download Python](https://www.python.org/downloads/)
- **Git** (optional, for cloning the repository)

## Quick Installation

### macOS / Linux

Run the installation script:

```bash
./install.sh
```

### Windows

Run the installation script:

```cmd
install.bat
```

## Manual Installation

If you prefer to install manually:

### 1. Clone or Download the Repository

```bash
git clone https://github.com/epowell101/deeptempo-ai-soc.git
cd deeptempo-ai-soc
```

### 2. Create Virtual Environment

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows:**
```cmd
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
pip install "mcp[cli]"
```

### 4. Generate Sample Data (Optional)

```bash
python -m scripts.demo
```

### 5. Run the Application

```bash
python main.py
```

## First-Time Setup

When you first run the application:

1. **Setup Wizard** - If the virtual environment is not detected, the setup wizard will guide you through installation.

2. **Configure Claude Desktop** (Optional):
   - Go to `File > Configure Claude Desktop...`
   - The wizard will auto-detect paths and configure MCP servers
   - Restart Claude Desktop to apply changes

3. **Configure Claude API** (Optional):
   - Go to `View > Claude Chat`
   - Enter your Anthropic API key
   - Get your API key from [Anthropic Console](https://console.anthropic.com/)

## Troubleshooting

### Python Version Issues

If you get a "Python 3.10+ required" error:

- **macOS**: Install via Homebrew: `brew install python@3.12`
- **Windows**: Download from [python.org](https://www.python.org/downloads/)
- **Linux**: Use your package manager or install from source

### Virtual Environment Issues

If the virtual environment fails to create:

```bash
# Remove existing venv and try again
rm -rf venv  # or rmdir /s /q venv on Windows
python3 -m venv venv
```

### Dependency Installation Issues

If pip install fails:

```bash
# Upgrade pip first
pip install --upgrade pip

# Try installing individually
pip install PyQt6
pip install anthropic
pip install qdarkstyle
pip install keyring
pip install numpy
```

### MCP SDK Issues

If MCP SDK installation fails:

```bash
# Try installing without CLI extras
pip install mcp
```

### Permission Issues (macOS/Linux)

If you get permission errors:

```bash
# Make install script executable
chmod +x install.sh

# Or use python3 explicitly
python3 -m venv venv
```

## Verification

To verify the installation:

1. **Check Python version:**
   ```bash
   python --version  # Should be 3.10+
   ```

2. **Check virtual environment:**
   ```bash
   source venv/bin/activate  # macOS/Linux
   # or
   venv\Scripts\activate  # Windows
   which python  # Should point to venv
   ```

3. **Check dependencies:**
   ```bash
   pip list | grep -E "PyQt6|anthropic|qdarkstyle"
   ```

4. **Run the application:**
   ```bash
   python main.py
   ```

## Next Steps

After installation:

1. **Generate Sample Data** (if not done during install):
   ```bash
   python -m scripts.demo
   ```

2. **Configure Claude Desktop** (optional):
   - Use the built-in configuration manager
   - Or manually edit Claude Desktop config file

3. **Start Using the Application:**
   - Explore findings in the Dashboard
   - Create and manage cases
   - Use Claude Chat for analysis
   - Monitor MCP servers

## Uninstallation

To remove the application:

1. **Deactivate virtual environment:**
   ```bash
   deactivate
   ```

2. **Remove virtual environment:**
   ```bash
   rm -rf venv  # macOS/Linux
   # or
   rmdir /s /q venv  # Windows
   ```

3. **Remove application data** (optional):
   ```bash
   rm -rf ~/.deeptempo  # macOS/Linux
   # or
   rmdir /s /q %USERPROFILE%\.deeptempo  # Windows
   ```

## Support

For issues or questions:

- Check the [README.md](README.md) for general information
- Review [TROUBLESHOOTING.md](TROUBLESHOOTING.md) if available
- Open an issue on GitHub

## Additional Resources

- [Claude Desktop Download](https://claude.ai/download)
- [Anthropic API Documentation](https://docs.anthropic.com/)
- [MITRE ATT&CK Navigator](https://mitre-attack.github.io/attack-navigator/)

