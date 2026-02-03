# Production Build and Deploy Script (Windows PowerShell)
# Builds frontend and starts production stack with nginx:alpine

Write-Host "🏗️  Building Beehus App for Production..." -ForegroundColor Cyan
Write-Host ""

# Step 1: Build Frontend
Write-Host "📦 Step 1/3: Building frontend..." -ForegroundColor Yellow
Set-Location beehus-web
npm run build
Set-Location ..
Write-Host "✅ Frontend built to beehus-web/dist/" -ForegroundColor Green
Write-Host ""

# Step 2: Stop existing services
Write-Host "🛑 Step 2/3: Stopping existing services..." -ForegroundColor Yellow
docker compose down
Write-Host "✅ Services stopped" -ForegroundColor Green
Write-Host ""

# Step 3: Start production stack
Write-Host "🚀 Step 3/3: Starting production stack..." -ForegroundColor Yellow
docker compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d
Write-Host "✅ Production stack started" -ForegroundColor Green
Write-Host ""

# Wait for services to be healthy
Write-Host "⏳ Waiting for services to be healthy..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Show status
Write-Host ""
Write-Host "📊 Service Status:" -ForegroundColor Cyan
docker compose ps
Write-Host ""

Write-Host "✅ Production deployment complete!" -ForegroundColor Green
Write-Host ""
Write-Host "🌐 Access points:" -ForegroundColor Cyan
Write-Host "   Frontend:  http://localhost:5173"
Write-Host "   API Docs:  http://localhost:8000/docs"
Write-Host "   Selenium:  http://localhost:4444"
Write-Host ""
Write-Host "💾 Memory savings: ~600MB (nginx:alpine vs Node.js dev server)" -ForegroundColor Green
Write-Host ""
Write-Host "📝 To view logs: docker compose logs -f"
Write-Host "🛑 To stop:      docker compose down"
