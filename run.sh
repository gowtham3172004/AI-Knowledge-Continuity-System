#!/bin/bash
# =============================================================================
# AI Knowledge Continuity System - Production Run Script
# =============================================================================
# This script starts both the backend API and frontend UI
# 
# Usage:
#   ./run.sh              # Start both backend and frontend
#   ./run.sh backend      # Start only backend
#   ./run.sh frontend     # Start only frontend
#   ./run.sh ingest       # Run document ingestion
#   ./run.sh test         # Test the system
#   ./run.sh stop         # Stop all services
# =============================================================================

set -e

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PATH="${PROJECT_ROOT}/../.venv"
BACKEND_PORT=8000
FRONTEND_PORT=3000

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check if Python virtual environment exists
check_venv() {
    if [ ! -d "$VENV_PATH" ]; then
        log_error "Virtual environment not found at $VENV_PATH"
        log_info "Please create it with: python -m venv $VENV_PATH"
        exit 1
    fi
}

# Check if Node.js is installed
check_node() {
    if ! command -v node &> /dev/null; then
        log_error "Node.js is not installed"
        exit 1
    fi
    if ! command -v npm &> /dev/null; then
        log_error "npm is not installed"
        exit 1
    fi
}

# Check if .env file exists
check_env() {
    if [ ! -f "$PROJECT_ROOT/.env" ]; then
        log_warning ".env file not found"
        log_info "Creating from template..."
        if [ -f "$PROJECT_ROOT/.env.example" ]; then
            cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
            log_warning "Please edit .env and add your GEMINI_API_KEY"
        fi
    fi
}

# Run document ingestion
run_ingest() {
    log_info "Running document ingestion..."
    cd "$PROJECT_ROOT"
    source "$VENV_PATH/bin/activate"
    python main.py --ingest
    log_success "Ingestion complete!"
}

# Start the backend server
start_backend() {
    log_info "Starting backend API on port $BACKEND_PORT..."
    cd "$PROJECT_ROOT"
    source "$VENV_PATH/bin/activate"
    
    # Check if port is in use
    if lsof -Pi :$BACKEND_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        log_warning "Port $BACKEND_PORT is already in use"
        log_info "Stopping existing process..."
        kill $(lsof -Pi :$BACKEND_PORT -sTCP:LISTEN -t) 2>/dev/null || true
        sleep 2
    fi
    
    # Start uvicorn
    python -m uvicorn backend.main:create_app --factory --host 0.0.0.0 --port $BACKEND_PORT &
    BACKEND_PID=$!
    echo $BACKEND_PID > "$PROJECT_ROOT/.backend.pid"
    
    # Wait for server to be ready
    log_info "Waiting for backend to start..."
    for i in {1..30}; do
        if curl -s "http://localhost:$BACKEND_PORT/api/health" > /dev/null 2>&1; then
            log_success "Backend API is running at http://localhost:$BACKEND_PORT"
            log_info "API Documentation: http://localhost:$BACKEND_PORT/docs"
            return 0
        fi
        sleep 1
    done
    
    log_error "Backend failed to start within 30 seconds"
    return 1
}

# Start the frontend development server
start_frontend() {
    log_info "Starting frontend on port $FRONTEND_PORT..."
    cd "$PROJECT_ROOT/frontend"
    
    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        log_info "Installing frontend dependencies..."
        npm install
    fi
    
    # Check if port is in use
    if lsof -Pi :$FRONTEND_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        log_warning "Port $FRONTEND_PORT is already in use"
    fi
    
    # Start React development server
    BROWSER=none npm start &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > "$PROJECT_ROOT/.frontend.pid"
    
    sleep 5
    log_success "Frontend is running at http://localhost:$FRONTEND_PORT"
}

# Stop all services
stop_services() {
    log_info "Stopping all services..."
    
    # Stop backend
    if [ -f "$PROJECT_ROOT/.backend.pid" ]; then
        PID=$(cat "$PROJECT_ROOT/.backend.pid")
        kill $PID 2>/dev/null || true
        rm "$PROJECT_ROOT/.backend.pid"
    fi
    
    # Stop frontend
    if [ -f "$PROJECT_ROOT/.frontend.pid" ]; then
        PID=$(cat "$PROJECT_ROOT/.frontend.pid")
        kill $PID 2>/dev/null || true
        rm "$PROJECT_ROOT/.frontend.pid"
    fi
    
    # Kill any remaining processes
    pkill -f "uvicorn backend.main" 2>/dev/null || true
    pkill -f "react-scripts start" 2>/dev/null || true
    
    log_success "All services stopped"
}

# Test the system
test_system() {
    log_info "Testing system..."
    cd "$PROJECT_ROOT"
    source "$VENV_PATH/bin/activate"
    
    # Test query
    log_info "Testing RAG query..."
    python main.py --query "What lessons were learned about caching?"
    
    log_success "System test complete!"
}

# Show help
show_help() {
    echo ""
    echo "AI Knowledge Continuity System - Run Script"
    echo "============================================"
    echo ""
    echo "Usage: ./run.sh [command]"
    echo ""
    echo "Commands:"
    echo "  (no command)  Start both backend and frontend"
    echo "  backend       Start only the backend API"
    echo "  frontend      Start only the frontend UI"
    echo "  ingest        Run document ingestion"
    echo "  test          Test the system with a sample query"
    echo "  stop          Stop all running services"
    echo "  help          Show this help message"
    echo ""
    echo "Environment:"
    echo "  Backend URL:  http://localhost:$BACKEND_PORT"
    echo "  Frontend URL: http://localhost:$FRONTEND_PORT"
    echo "  API Docs:     http://localhost:$BACKEND_PORT/docs"
    echo ""
}

# Main entry point
main() {
    echo ""
    echo "============================================"
    echo "AI Knowledge Continuity System"
    echo "============================================"
    echo ""
    
    case "${1:-all}" in
        backend)
            check_venv
            check_env
            start_backend
            ;;
        frontend)
            check_node
            start_frontend
            ;;
        ingest)
            check_venv
            check_env
            run_ingest
            ;;
        test)
            check_venv
            check_env
            test_system
            ;;
        stop)
            stop_services
            ;;
        help|--help|-h)
            show_help
            ;;
        all|*)
            check_venv
            check_node
            check_env
            
            log_info "Starting complete system..."
            echo ""
            
            start_backend
            echo ""
            start_frontend
            
            echo ""
            log_success "=========================================="
            log_success "System is ready!"
            log_success "=========================================="
            echo ""
            log_info "Frontend: http://localhost:$FRONTEND_PORT"
            log_info "Backend:  http://localhost:$BACKEND_PORT"
            log_info "API Docs: http://localhost:$BACKEND_PORT/docs"
            echo ""
            log_info "Press Ctrl+C to stop, or run: ./run.sh stop"
            
            # Wait for user interrupt
            wait
            ;;
    esac
}

main "$@"
