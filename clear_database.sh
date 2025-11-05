#!/bin/bash

# Script to clear all records from CV and JD tables

echo "Clearing CV and JD database tables..."

# Execute SQL commands to delete all records from both tables
docker exec -it cv_processor_db psql -U postgres -d cv_processor -c "
BEGIN;
DELETE FROM cv;
DELETE FROM jd;
COMMIT;
"

if [ $? -eq 0 ]; then
    echo "✓ Successfully cleared all records from CV and JD tables"
else
    echo "✗ Failed to clear database tables"
    exit 1
fi
