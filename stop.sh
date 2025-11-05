#!/bin/bash

echo "🛑 Stopping CV Processing Backend..."
echo ""

# Stop containers
echo "Stopping containers..."
docker stop cv_processor_backend 2>/dev/null && echo "✅ Backend stopped" || echo "⚠️  Backend not running"
docker stop cv_processor_db 2>/dev/null && echo "✅ Database stopped" || echo "⚠️  Database not running"

# Remove containers
echo ""
echo "Removing containers..."
docker rm cv_processor_backend 2>/dev/null && echo "✅ Backend removed" || echo "⚠️  Backend not found"
docker rm cv_processor_db 2>/dev/null && echo "✅ Database removed" || echo "⚠️  Database not found"

echo ""
echo "✅ Cleanup complete"
echo ""
echo "Note: Database volume 'cv_processor_db_data' is preserved."
echo "To remove it: docker volume rm cv_processor_db_data"
