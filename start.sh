#!/bin/bash

echo "🚀 Starting CV Processing Backend..."
echo ""

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose not found. Please install docker-compose first."
    exit 1
fi

# Stop and remove existing containers
echo "🛑 Stopping existing containers..."
docker-compose down

# Start services with rebuild
echo "📦 Building and starting Docker containers..."
docker-compose up -d --build --no-cache

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 5

# Check health
echo "🔍 Checking health..."
if [ -f .env ]; then
    SECRET_KEY=$(grep "^SECRET_KEY=" .env | cut -d= -f2)
    curl -s -H "X-Secret-Key: ${SECRET_KEY}" http://localhost:8000/health
    echo ""
    echo "✅ Backend is ready!"
    echo ""
    echo "📚 API Documentation: http://localhost:8000/docs"
    echo "🔑 SECRET_KEY: ${SECRET_KEY}"
else
    echo "⚠️  .env file not found. Skipping health check."
    echo ""
    echo "📚 API Documentation: http://localhost:8000/docs"
fi
echo ""
echo "Example usage:"
echo "  curl -H \"X-Secret-Key: ${SECRET_KEY}\" http://localhost:8000/health"
echo ""
