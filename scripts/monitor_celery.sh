#!/usr/bin/env bash
# Celery Monitoring CLI - Alternative to Flower
# Usage: ./scripts/monitor_celery.sh [command]

set -e

WORKER_CONTAINER="beehus-app-celery-worker-1"
CELERY_APP="core.celery_app"

function show_help() {
    cat << EOF
Celery Monitoring CLI (Flower Alternative)

Usage: ./scripts/monitor_celery.sh [COMMAND]

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
  ./scripts/monitor_celery.sh active
  ./scripts/monitor_celery.sh stats
  ./scripts/monitor_celery.sh queue

EOF
}

function check_container() {
    if ! docker ps --format '{{.Names}}' | grep -q "$WORKER_CONTAINER"; then
        echo "❌ Error: Worker container '$WORKER_CONTAINER' is not running"
        echo "Start it with: docker compose up -d celery-worker"
        exit 1
    fi
}

case "${1:-help}" in
    active)
        echo "📊 Active Tasks:"
        docker exec $WORKER_CONTAINER celery -A $CELERY_APP inspect active
        ;;
    
    stats)
        echo "📈 Worker Statistics:"
        docker exec $WORKER_CONTAINER celery -A $CELERY_APP inspect stats
        ;;
    
    registered)
        echo "📋 Registered Tasks:"
        docker exec $WORKER_CONTAINER celery -A $CELERY_APP inspect registered
        ;;
    
    scheduled)
        echo "⏰ Scheduled Tasks:"
        docker exec $WORKER_CONTAINER celery -A $CELERY_APP inspect scheduled
        ;;
    
    queue)
        echo "📥 Tasks in Queue:"
        docker exec $WORKER_CONTAINER celery -A $CELERY_APP inspect reserved
        ;;
    
    workers)
        echo "👷 Active Workers:"
        docker exec $WORKER_CONTAINER celery -A $CELERY_APP inspect active_queues
        ;;
    
    ping)
        echo "🏓 Pinging Workers:"
        docker exec $WORKER_CONTAINER celery -A $CELERY_APP inspect ping
        ;;
    
    help|--help|-h)
        show_help
        ;;
    
    *)
        echo "❌ Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac
