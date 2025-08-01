#!/bin/bash

# Local Docker Test Script
# Test the Docker image locally before deploying to EKS

set -e

# Configuration
IMAGE_NAME="web-ui-test"
CONTAINER_NAME="web-ui-test-container"
HOST_PORT="7788"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

echo_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

echo_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to cleanup existing container
cleanup() {
    echo_info "Cleaning up existing container..."
    docker stop $CONTAINER_NAME 2>/dev/null || true
    docker rm $CONTAINER_NAME 2>/dev/null || true
}

# Function to build and test locally
test_local() {
    echo_info "Starting local Docker test..."
    
    # Cleanup any existing container
    cleanup
    
    # Build the image for linux/amd64
    echo_info "Building Docker image for linux/amd64..."
    docker buildx build --platform linux/amd64 -t $IMAGE_NAME . --load
    
    # Run the container
    echo_info "Starting container..."
    docker run -d \
        --name $CONTAINER_NAME \
        --platform linux/amd64 \
        -p $HOST_PORT:7788 \
        -p 6080:6080 \
        -p 5901:5901 \
        -p 9222:9222 \
        -e AWS_BEDROCK_REGION=us-west-2 \
        -e AWS_DEFAULT_REGION=us-east-1 \
        -e DEFAULT_LLM=bedrock \
        -e ANONYMIZED_TELEMETRY=false \
        -e BROWSER_USE_LOGGING_LEVEL=info \
        -v ~/.aws:/root/.aws:ro \
        --shm-size=2g \
        --cap-add=SYS_ADMIN \
        $IMAGE_NAME
    
    # Wait for container to start
    echo_info "Waiting for container to start..."
    sleep 10
    
    # Check if container is running
    if docker ps | grep -q $CONTAINER_NAME; then
        echo_info "✅ Container is running successfully!"
        
        # Show container logs
        echo_info "Container logs:"
        docker logs $CONTAINER_NAME --tail 20
        
        # Test HTTP endpoint
        echo_info "Testing HTTP endpoint..."
        if curl -f http://localhost:$HOST_PORT >/dev/null 2>&1; then
            echo_info "✅ HTTP endpoint is responding!"
        else
            echo_warn "⚠️ HTTP endpoint is not responding yet (this might be normal during startup)"
        fi
        
        echo_info "🌐 Access the application at:"
        echo_info "  - Web UI: http://localhost:$HOST_PORT"
        echo_info "  - VNC: http://localhost:6080"
        echo_info "  - Chrome Debug: http://localhost:9222"
        
        echo_info "To stop the test container, run: docker stop $CONTAINER_NAME"
        echo_info "To view logs, run: docker logs -f $CONTAINER_NAME"
        
    else
        echo_error "❌ Container failed to start!"
        echo_error "Container logs:"
        docker logs $CONTAINER_NAME
        exit 1
    fi
}

# Function to stop test container
stop_test() {
    echo_info "Stopping test container..."
    cleanup
    echo_info "Test container stopped."
}

# Parse command line arguments
case "${1:-test}" in
    test)
        test_local
        ;;
    stop)
        stop_test
        ;;
    logs)
        echo_info "Showing container logs:"
        docker logs -f $CONTAINER_NAME
        ;;
    shell)
        echo_info "Opening shell in container:"
        docker exec -it $CONTAINER_NAME /bin/bash
        ;;
    *)
        echo "Usage: $0 [test|stop|logs|shell]"
        echo "  test: Build and run container locally (default)"
        echo "  stop: Stop and remove test container"
        echo "  logs: Show container logs"
        echo "  shell: Open shell in running container"
        exit 1
        ;;
esac
