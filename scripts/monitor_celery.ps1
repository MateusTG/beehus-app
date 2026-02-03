# Celery Monitoring CLI - Alternative to Flower (Windows PowerShell)
# Usage: .\scripts\monitor_celery.ps1 [command]

param(
    [Parameter(Position=0)]
    [ValidateSet("active", "stats", "registered", "scheduled", "queue", "workers", "ping", "help")]
    [string]$Command = "help"
)

$WorkerContainer = "beehus-app-celery-worker-1"
$CeleryApp = "core.celery_app"

function Show-Help {
    Write-Host @"
Celery Monitoring CLI (Flower Alternative)

Usage: .\scripts\monitor_celery.ps1 [COMMAND]

Commands:
  active        Show currently running tasks
  stats         Show worker statistics
  registered    List all registered tasks
  scheduled     Show scheduled tasks (Beat)
  queue         Show tasks in queue
  workers       List active workers
  ping          Ping workers
  help          Show this help message

Examples:
  .\scripts\monitor_celery.ps1 active
  .\scripts\monitor_celery.ps1 stats
  .\scripts\monitor_celery.ps1 queue

"@
}

function Test-Container {
    $running = docker ps --format '{{.Names}}' | Select-String -Pattern $WorkerContainer
    if (-not $running) {
        Write-Host "❌ Error: Worker container '$WorkerContainer' is not running" -ForegroundColor Red
        Write-Host "Start it with: docker compose up -d celery-worker"
        exit 1
    }
}

Test-Container

switch ($Command) {
    "active" {
        Write-Host "📊 Active Tasks:" -ForegroundColor Cyan
        docker exec $WorkerContainer celery -A $CeleryApp inspect active
    }
    
    "stats" {
        Write-Host "📈 Worker Statistics:" -ForegroundColor Cyan
        docker exec $WorkerContainer celery -A $CeleryApp inspect stats
    }
    
    "registered" {
        Write-Host "📋 Registered Tasks:" -ForegroundColor Cyan
        docker exec $WorkerContainer celery -A $CeleryApp inspect registered
    }
    
    "scheduled" {
        Write-Host "⏰ Scheduled Tasks:" -ForegroundColor Cyan
        docker exec $WorkerContainer celery -A $CeleryApp inspect scheduled
    }
    
    "queue" {
        Write-Host "📥 Tasks in Queue:" -ForegroundColor Cyan
        docker exec $WorkerContainer celery -A $CeleryApp inspect reserved
    }
    
    "workers" {
        Write-Host "👷 Active Workers:" -ForegroundColor Cyan
        docker exec $WorkerContainer celery -A $CeleryApp inspect active_queues
    }
    
    "ping" {
        Write-Host "🏓 Pinging Workers:" -ForegroundColor Cyan
        docker exec $WorkerContainer celery -A $CeleryApp inspect ping
    }
    
    "help" {
        Show-Help
    }
}
