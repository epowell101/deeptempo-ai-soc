#!/bin/bash
# Script to run AI Decision Logs database migration

set -e  # Exit on error

echo "========================================="
echo "AI Decision Logs Migration"
echo "========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if PostgreSQL is running
echo "Checking PostgreSQL status..."

if docker ps | grep -q postgres; then
    echo -e "${GREEN}✓ PostgreSQL container is running${NC}"
    DB_CONTAINER=$(docker ps -qf "name=postgres")
    
    echo ""
    echo "Running migration..."
    echo ""
    
    # Run the migration
    docker exec -i "$DB_CONTAINER" psql -U postgres -d deeptempo_soc < database/init/003_ai_decision_logs.sql
    
    if [ $? -eq 0 ]; then
        echo ""
        echo -e "${GREEN}✓ Migration completed successfully!${NC}"
        echo ""
        
        # Verify the table was created
        echo "Verifying table creation..."
        TABLE_EXISTS=$(docker exec -i "$DB_CONTAINER" psql -U postgres -d deeptempo_soc -t -c "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'ai_decision_logs');")
        
        if [[ $TABLE_EXISTS == *"t"* ]]; then
            echo -e "${GREEN}✓ Table 'ai_decision_logs' exists${NC}"
            
            # Get table info
            echo ""
            echo "Table structure:"
            docker exec -i "$DB_CONTAINER" psql -U postgres -d deeptempo_soc -c "\d ai_decision_logs"
            
            # Count rows
            ROW_COUNT=$(docker exec -i "$DB_CONTAINER" psql -U postgres -d deeptempo_soc -t -c "SELECT COUNT(*) FROM ai_decision_logs;")
            echo ""
            echo -e "${GREEN}Current row count: $ROW_COUNT${NC}"
        else
            echo -e "${RED}✗ Table was not created${NC}"
            exit 1
        fi
    else
        echo -e "${RED}✗ Migration failed${NC}"
        exit 1
    fi
    
elif pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ PostgreSQL is running locally${NC}"
    
    echo ""
    echo "Running migration..."
    echo ""
    
    # Run migration using local psql
    psql -U postgres -d deeptempo_soc -f database/init/003_ai_decision_logs.sql
    
    if [ $? -eq 0 ]; then
        echo ""
        echo -e "${GREEN}✓ Migration completed successfully!${NC}"
    else
        echo -e "${RED}✗ Migration failed${NC}"
        exit 1
    fi
    
else
    echo -e "${RED}✗ PostgreSQL is not running${NC}"
    echo ""
    echo "Please start PostgreSQL first:"
    echo "  ./start_database.sh"
    echo ""
    exit 1
fi

echo ""
echo "========================================="
echo "Next Steps:"
echo "========================================="
echo "1. Restart the web application (if running):"
echo "   ./start_web.sh"
echo ""
echo "2. Access the AI Decisions page:"
echo "   http://localhost:6988/ai-decisions"
echo ""
echo "3. Read the documentation:"
echo "   docs/ai-decision-feedback-guide.md"
echo ""
echo -e "${GREEN}Migration complete!${NC}"

