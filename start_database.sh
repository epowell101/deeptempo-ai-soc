#!/bin/bash
# Start PostgreSQL database for DeepTempo AI SOC

set -e

echo "=================================================="
echo "DeepTempo AI SOC - Database Startup"
echo "=================================================="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Error: Docker is not installed"
    echo "Please install Docker from https://www.docker.com/get-started"
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Error: Docker Compose is not installed"
    echo "Please install Docker Compose"
    exit 1
fi

# Use docker-compose or docker compose based on availability
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
else
    DOCKER_COMPOSE="docker compose"
fi

# Load environment variables if .env exists
if [ -f .env ]; then
    echo "✓ Loading environment variables from .env"
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "⚠ Warning: .env file not found, using defaults"
    echo "  Copy env.example to .env and customize for your environment"
fi

# Start PostgreSQL
echo ""
echo "Starting PostgreSQL database..."
$DOCKER_COMPOSE up -d postgres

# Wait for PostgreSQL to be ready
echo ""
echo "Waiting for PostgreSQL to be ready..."
for i in {1..30}; do
    if docker exec deeptempo-postgres pg_isready -U deeptempo -d deeptempo_soc &> /dev/null; then
        echo "✓ PostgreSQL is ready!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ Error: PostgreSQL failed to start within 30 seconds"
        echo "Check logs with: $DOCKER_COMPOSE logs postgres"
        exit 1
    fi
    echo -n "."
    sleep 1
done

# Initialize database tables
echo ""
echo "Initializing database tables..."
python3 -c "
from database.connection import init_database
try:
    init_database(create_tables=True)
    print('✓ Database tables created successfully')
except Exception as e:
    print(f'❌ Error initializing database: {e}')
    exit(1)
" || {
    echo "⚠ Warning: Could not initialize database tables"
    echo "  You may need to run the migration script manually:"
    echo "  python database/migrate_json_to_db.py"
}

# Optional: Start PgAdmin
read -p "Do you want to start PgAdmin (database management UI)? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Starting PgAdmin..."
    $DOCKER_COMPOSE up -d pgadmin
    echo "✓ PgAdmin started at http://localhost:5050"
    echo "  Default login: ${PGADMIN_EMAIL:-admin@deeptempo.ai}"
fi

# Show status
echo ""
echo "=================================================="
echo "Database Status"
echo "=================================================="
$DOCKER_COMPOSE ps

echo ""
echo "=================================================="
echo "✓ Database startup complete!"
echo "=================================================="
echo ""
echo "PostgreSQL is running at: localhost:5432"
echo "Database name: ${POSTGRES_DB:-deeptempo_soc}"
echo "Username: ${POSTGRES_USER:-deeptempo}"
echo ""
echo "Useful commands:"
echo "  - View logs:        $DOCKER_COMPOSE logs -f postgres"
echo "  - Stop database:    $DOCKER_COMPOSE stop postgres"
echo "  - Restart database: $DOCKER_COMPOSE restart postgres"
echo "  - Connect to DB:    docker exec -it deeptempo-postgres psql -U deeptempo -d deeptempo_soc"
echo ""
echo "To migrate existing JSON data to PostgreSQL:"
echo "  python database/migrate_json_to_db.py"
echo ""

