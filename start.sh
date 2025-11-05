#!/bin/bash

echo "🚀 Starting CV Processing Backend..."
echo ""

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose not found. Please install docker-compose first."
    exit 1
fi

# Default: build without cache and force recreate for clean builds
echo "📦 Building and starting containers (no cache, force recreate)..."
docker-compose build --no-cache
docker-compose up -d --force-recreate

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 5

# Check if containers are running
echo "🔍 Checking container status..."
RUNNING_CONTAINERS=$(docker-compose ps --services --filter "status=running" 2>/dev/null | wc -l)

if [ "$RUNNING_CONTAINERS" -lt 2 ]; then
    echo "❌ Containers failed to start!"
    echo ""
    echo "📋 Container status:"
    docker-compose ps
    echo ""
    echo "📋 Backend logs:"
    docker-compose logs --tail=50 backend
    echo ""
    echo "📋 Database logs:"
    docker-compose logs --tail=20 db
    exit 1
fi

# Check health
echo "🔍 Checking health..."
if [ -f .env ]; then
    SECRET_KEY=$(grep "^SECRET_KEY=" .env | cut -d= -f2)

    # Try health check with retries
    for i in {1..5}; do
        if curl -s -H "X-Secret-Key: ${SECRET_KEY}" http://localhost:8000/health > /dev/null 2>&1; then
            echo ""
            echo "✅ Backend is ready!"
            echo ""
            echo "📚 API Documentation: http://localhost:8000/docs"
            echo "🔑 SECRET_KEY: ${SECRET_KEY}"
            echo ""
            echo "Example usage:"
            echo "  curl -H \"X-Secret-Key: ${SECRET_KEY}\" http://localhost:8000/health"
            echo ""
            exit 0
        fi
        echo "⏳ Waiting for backend to be ready... (attempt $i/5)"
        sleep 3
    done

    echo "❌ Backend health check failed after 5 attempts"
    echo ""
    echo "📋 Backend logs:"
    docker-compose logs --tail=50 backend
    exit 1
else
    echo "⚠️  .env file not found. Skipping health check."
    echo ""
    echo "📚 API Documentation: http://localhost:8000/docs"
fi
