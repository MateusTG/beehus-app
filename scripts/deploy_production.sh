#!/usr/bin/env bash
# Production Build and Deploy Script
# Builds frontend and starts production stack with nginx:alpine

set -e

echo "🏗️  Building Beehus App for Production..."
echo ""

# Step 1: Build Frontend
echo "📦 Step 1/3: Building frontend..."
cd beehus-web
npm run build
cd ..
echo "✅ Frontend built to beehus-web/dist/"
echo ""

# Step 2: Stop existing services
echo "🛑 Step 2/3: Stopping existing services..."
docker compose down
echo "✅ Services stopped"
echo ""

# Step 3: Start production stack
echo "🚀 Step 3/3: Starting production stack..."
docker compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d
echo "✅ Production stack started"
echo ""

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."
sleep 5

# Show status
echo ""
echo "📊 Service Status:"
docker compose ps
echo ""

echo "✅ Production deployment complete!"
echo ""
echo "🌐 Access points:"
echo "   Frontend:  http://localhost:5173"
echo "   API Docs:  http://localhost:8000/docs"
echo "   Selenium:  http://localhost:4444"
echo ""
echo "💾 Memory savings: ~600MB (nginx:alpine vs Node.js dev server)"
echo ""
echo "📝 To view logs: docker compose logs -f"
echo "🛑 To stop:      docker compose down"
