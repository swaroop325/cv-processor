#!/bin/bash

echo "🚀 Starting CV Processing Backend..."
echo ""

# Check which docker compose command to use
# Prefer V2 as it has better buildx support
if command -v docker &> /dev/null && docker compose version &> /dev/null 2>&1; then
    DOCKER_COMPOSE="docker compose"
    echo "✅ Using Docker Compose V2"
elif command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
    echo "⚠️  Using Docker Compose V1 (may have buildx compatibility issues)"
    echo "💡 Consider upgrading to Docker Compose V2: https://docs.docker.com/compose/install/"
else
    echo "❌ Docker Compose not found."
    echo ""
    echo "Please install Docker Compose:"
    echo "  - Docker Compose V2 (recommended): comes with Docker Engine"
    echo "  - Docker Compose V1: https://docs.docker.com/compose/install/standalone/"
    exit 1
fi

# Default: build without cache and force recreate for clean builds
echo "📦 Building and starting containers (no cache, force recreate)..."
$DOCKER_COMPOSE build --no-cache
$DOCKER_COMPOSE up -d --force-recreate

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 5

# Check if containers are running
echo "🔍 Checking container status..."
RUNNING_CONTAINERS=$($DOCKER_COMPOSE ps --services --filter "status=running" 2>/dev/null | wc -l)

if [ "$RUNNING_CONTAINERS" -lt 2 ]; then
    echo "❌ Containers failed to start!"
    echo ""
    echo "📋 Container status:"
    $DOCKER_COMPOSE ps
    echo ""
    echo "📋 Backend logs:"
    $DOCKER_COMPOSE logs --tail=50 backend
    echo ""
    echo "📋 Database logs:"
    $DOCKER_COMPOSE logs --tail=20 db
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
    $DOCKER_COMPOSE logs --tail=50 backend
    exit 1
else
    echo "⚠️  .env file not found. Skipping health check."
    echo ""
    echo "📚 API Documentation: http://localhost:8000/docs"
fi
