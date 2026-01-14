# Installation Guide

This guide will help you install and set up the DeepTempo AI SOC web application with PostgreSQL database.

## Prerequisites

### Required
- **Python 3.10 or higher** - [Download Python](https://www.python.org/downloads/)
- **Node.js 18 or higher** - [Download Node.js](https://nodejs.org/) (for frontend UI)
- **Docker Desktop** - [Download Docker](https://www.docker.com/products/docker-desktop/) (for PostgreSQL)

### Optional
- **Git** - For cloning the repository

## Quick Installation

### macOS / Linux

Run the complete installation script:

```bash
chmod +x install_all.sh
./install_all.sh
```

This installs everything:
- ✅ Python environment and dependencies
- ✅ Frontend UI (React + Vite)
- ✅ PostgreSQL database with Docker
- ✅ Database tables and initialization

### Windows

Run the installation script:

```cmd
install_all.bat
```

Or use individual scripts:
- `install_web_essentials.bat` - Python dependencies only
- `start_database.bat` - PostgreSQL only
- `start_web.bat` - Application startup

## What Gets Installed

### Backend Components
- **Python Environment**: Virtual environment with all dependencies
- **Database Packages**: SQLAlchemy, psycopg2, Alembic
- **API Framework**: FastAPI with uvicorn server
- **AI Integration**: Anthropic Claude API client
- **Reporting**: PDF generation, visualization libraries
- **Integrations**: AWS S3, Timesketch, and more

### Frontend Components
- **React Application**: Modern React 18+ UI
- **Vite**: Fast development server and build tool
- **TypeScript**: Type-safe development
- **UI Components**: Material-UI, charts, tables

### Database
- **PostgreSQL 16**: Production-grade relational database
- **Docker Container**: Isolated database environment
- **PgAdmin**: Web-based database management UI (optional)
- **Auto-initialization**: Tables created automatically

## Manual Installation

If you prefer to install components individually:

### 1. Clone or Download the Repository

```bash
git clone https://github.com/epowell101/deeptempo-ai-soc.git
cd deeptempo-ai-soc
```

### 2. Install Backend

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements_web.txt
```

**Windows:**
```cmd
python -m venv venv
venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements_web.txt
```

Or use the essentials script (recommended):
```bash
chmod +x install_web_essentials.sh
./install_web_essentials.sh
```

### 3. Install Frontend

**All platforms:**
```bash
cd frontend
npm install
cd ..
```

### 4. Install PostgreSQL

**Using Docker (recommended):**
```bash
# Copy environment file
cp env.example .env

# Edit .env and set passwords

# Start PostgreSQL
chmod +x start_database.sh
./start_database.sh
```

**Without Docker:**
- Install PostgreSQL manually from [postgresql.org](https://www.postgresql.org/download/)
- Create database: `createdb deeptempo_soc`
- Update `.env` with connection details

### 5. Migrate Existing Data (Optional)

If you have existing JSON data:
```bash
python database/migrate_json_to_db.py
```

### 6. Run the Application

```bash
chmod +x start_web.sh
./start_web.sh
```

Or start components individually:
```bash
# Terminal 1: Backend API
cd backend
uvicorn main:app --host 127.0.0.1 --port 6987 --reload

# Terminal 2: Frontend UI
cd frontend
npm run dev
```

## First-Time Setup

When you first run the application:

### 1. Environment Configuration

Create or edit the `.env` file:
```env
# PostgreSQL Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=deeptempo_soc
POSTGRES_USER=deeptempo
POSTGRES_PASSWORD=your_secure_password_here  # CHANGE THIS!

# Data backend
DATA_BACKEND=database

# PgAdmin (optional)
PGADMIN_EMAIL=admin@deeptempo.ai
PGADMIN_PASSWORD=your_admin_password  # CHANGE THIS!
```

### 2. Configure Claude API (Optional)

If using AI features:
1. Get your API key from [Anthropic Console](https://console.anthropic.com/)
2. Set in environment or enter in UI settings

### 3. Access the Application

After running `./start_web.sh`:
- **Frontend UI**: http://localhost:6988
- **Backend API**: http://localhost:6987
- **API Docs**: http://localhost:6987/docs
- **PgAdmin**: http://localhost:5050 (if started)

### 4. Verify Installation

Check that all components are running:
```bash
# Check PostgreSQL
docker ps | grep deeptempo-postgres

# Check backend logs
# (should show "PostgreSQL database connected and ready")

# Check frontend
# Open http://localhost:6988 in browser
```

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
pip install keyring  # Optional: only needed if using keyring backend
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

### 1. Generate Sample Data (Optional)

Create demo findings and cases:
```bash
python -m scripts.demo
```

### 2. Import Your Data

Import existing data from CSV or JSON:
```bash
# Via API
curl -X POST http://localhost:6987/api/ingest/upload \
  -F "file=@your_data.json" \
  -F "data_type=finding"

# Via Python
python database/migrate_json_to_db.py
```

See [DATA_INGESTION_GUIDE.md](DATA_INGESTION_GUIDE.md) for details.

### 3. Start Using the Application

- **View Dashboard**: http://localhost:6988
- **Explore Findings**: Browse security findings with filters
- **Manage Cases**: Create and track investigations
- **Use AI Analysis**: Integrate Claude for threat analysis
- **Query Database**: Use PgAdmin or psql for advanced queries

### 4. Configure Integrations (Optional)

Set up integrations with your security tools:
- See [docs/integration-wizard-guide.md](docs/integration-wizard-guide.md)
- Configure MCP servers in Settings
- Add API keys for cloud services

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

