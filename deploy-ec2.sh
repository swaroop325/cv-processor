#!/bin/bash

echo "🚀 Starting CV Processing Backend (EC2 Compatible)..."
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker first."
    exit 1
fi

echo "✅ Docker found"

# Load environment variables
if [ ! -f .env ]; then
    echo "❌ .env file not found. Please create .env file first."
    exit 1
fi

# Source .env file
export $(cat .env | grep -v '^#' | xargs)

# Create network if it doesn't exist
echo "📡 Creating Docker network..."
docker network create cv-processor-network 2>/dev/null || echo "Network already exists"

# Stop and remove existing containers
echo "🛑 Stopping existing containers..."
docker stop cv_processor_backend 2>/dev/null || true
docker stop cv_processor_db 2>/dev/null || true
docker rm cv_processor_backend 2>/dev/null || true
docker rm cv_processor_db 2>/dev/null || true

# Start PostgreSQL with pgvector
echo "🗄️  Starting PostgreSQL database..."
docker run -d \
    --name cv_processor_db \
    --network cv-processor-network \
    -e POSTGRES_USER=postgres \
    -e POSTGRES_PASSWORD=postgres \
    -e POSTGRES_DB=cv_processor \
    -p 5432:5432 \
    -v cv_processor_db_data:/var/lib/postgresql/data \
    --health-cmd "pg_isready -U postgres" \
    --health-interval 5s \
    --health-timeout 5s \
    --health-retries 5 \
    ankane/pgvector:latest

# Wait for database to be healthy
echo "⏳ Waiting for database to be ready..."
for i in {1..30}; do
    if docker exec cv_processor_db pg_isready -U postgres > /dev/null 2>&1; then
        echo "✅ Database is ready!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ Database failed to start"
        echo ""
        echo "📋 Database logs:"
        docker logs cv_processor_db
        exit 1
    fi
    sleep 2
done

# Build backend image
echo "🔨 Building backend image..."
docker build -t cv-processor-backend .

if [ $? -ne 0 ]; then
    echo "❌ Backend build failed"
    exit 1
fi

# Create logs directory if it doesn't exist
mkdir -p logs

# Start backend
echo "🚀 Starting backend..."
docker run -d \
    --name cv_processor_backend \
    --network cv-processor-network \
    -e DATABASE_URL=postgresql+asyncpg://postgres:postgres@cv_processor_db:5432/cv_processor \
    -e SECRET_KEY="${SECRET_KEY}" \
    -e OPENAI_API_KEY="${OPENAI_API_KEY}" \
    -e APP_NAME="${APP_NAME:-CV Processor}" \
    -e APP_VERSION="${APP_VERSION:-1.0.0}" \
    -p 8000:8000 \
    -v $(pwd)/logs:/app/logs \
    cv-processor-backend \
    sh -c "alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port 8000"

# Wait for backend to start
echo "⏳ Waiting for backend to start..."
sleep 5

# Check if backend is running
if ! docker ps | grep -q cv_processor_backend; then
    echo "❌ Backend failed to start"
    echo ""
    echo "📋 Backend logs:"
    docker logs cv_processor_backend
    exit 1
fi

# Check health
echo "🔍 Checking health..."
for i in {1..10}; do
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
        echo "📋 View logs:"
        echo "  docker logs -f cv_processor_backend"
        echo ""
        exit 0
    fi
    echo "⏳ Waiting for backend to be ready... (attempt $i/10)"
    sleep 3
done

echo "❌ Backend health check failed"
echo ""
echo "📋 Backend logs:"
docker logs cv_processor_backend
exit 1
