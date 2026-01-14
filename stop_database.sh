#!/bin/bash
# Stop PostgreSQL database for DeepTempo AI SOC

set -e

echo "=================================================="
echo "DeepTempo AI SOC - Database Shutdown"
echo "=================================================="

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Error: Docker Compose is not installed"
    exit 1
fi

# Use docker-compose or docker compose based on availability
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
else
    DOCKER_COMPOSE="docker compose"
fi

# Stop containers
echo "Stopping PostgreSQL and PgAdmin..."
$DOCKER_COMPOSE stop postgres pgadmin

echo ""
echo "✓ Database stopped successfully"
echo ""
echo "To start again: ./start_database.sh"
echo "To remove containers and data: $DOCKER_COMPOSE down -v"
echo ""

