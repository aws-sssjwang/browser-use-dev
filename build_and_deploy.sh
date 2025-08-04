#!/bin/bash

# Build and Deploy Script for EKS
# This script builds the Docker image for linux/amd64 and deploys to EKS

set -e

# Configuration
AWS_REGION="us-east-1"
CLUSTER_NAME="browser-use-deployment-cluster"
ECR_REPOSITORY="web-ui"
IMAGE_TAG="latest"
NAMESPACE="default"

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

# Function to get AWS account ID
get_account_id() {
    aws sts get-caller-identity --query Account --output text
}

# Function to check if ECR repository exists
check_ecr_repo() {
    local repo_name=$1
    aws ecr describe-repositories --repository-names $repo_name --region $AWS_REGION >/dev/null 2>&1
}

# Function to create ECR repository if it doesn't exist
create_ecr_repo() {
    local repo_name=$1
    echo_info "Creating ECR repository: $repo_name"
    aws ecr create-repository --repository-name $repo_name --region $AWS_REGION
}

# Main deployment function
main() {
    echo_info "Starting Docker build and EKS deployment process..."
    
    # Get AWS account ID
    ACCOUNT_ID=$(get_account_id)
    if [ -z "$ACCOUNT_ID" ]; then
        echo_error "Failed to get AWS account ID. Please check your AWS credentials."
        exit 1
    fi
    
    ECR_URI="${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
    FULL_IMAGE_NAME="${ECR_URI}/${ECR_REPOSITORY}:${IMAGE_TAG}"
    
    echo_info "AWS Account ID: $ACCOUNT_ID"
    echo_info "ECR URI: $ECR_URI"
    echo_info "Full Image Name: $FULL_IMAGE_NAME"
    
    # Check if ECR repository exists, create if not
    if ! check_ecr_repo $ECR_REPOSITORY; then
        echo_warn "ECR repository $ECR_REPOSITORY does not exist. Creating..."
        create_ecr_repo $ECR_REPOSITORY
    fi
    
    # Login to ECR
    echo_info "Logging in to ECR..."
    aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_URI
    
    # Build Docker image for linux/amd64
    echo_info "Building Docker image for linux/amd64..."
    docker buildx build --platform linux/amd64 -t $FULL_IMAGE_NAME . --load
    
    # Push image to ECR
    echo_info "Pushing image to ECR..."
    docker push $FULL_IMAGE_NAME
    
    # Update kubeconfig
    echo_info "Updating kubeconfig for EKS cluster..."
    aws eks update-kubeconfig --region $AWS_REGION --name $CLUSTER_NAME
    
    # Update deployment with new image
    echo_info "Updating Kubernetes deployment..."
    
    # Update the deployment.yaml with the new image
    sed -i.bak "s|image: PLACEHOLDER_ECR_IMAGE|image: $FULL_IMAGE_NAME|g" k8s/deployment.yaml
    
    # Apply Kubernetes configurations
    echo_info "Applying Kubernetes configurations..."
    kubectl apply -f k8s/
    
    # Wait for deployment to be ready
    echo_info "Waiting for deployment to be ready..."
    kubectl rollout status deployment/web-ui-deployment -n $NAMESPACE --timeout=300s
    
    # Get deployment status
    echo_info "Deployment status:"
    kubectl get pods -n $NAMESPACE -l app=browser-use
    
    # Get service information
    echo_info "Service information:"
    kubectl get svc -n $NAMESPACE
    
    # Get ingress information
    echo_info "Ingress information:"
    kubectl get ingress -n $NAMESPACE
    
    echo_info "Deployment completed successfully!"
    echo_info "CloudFront URL: http://dsjpnyogrtasp.cloudfront.net"
    
    # Restore original deployment.yaml
    mv k8s/deployment.yaml.bak k8s/deployment.yaml
}

# Check if required tools are installed
check_dependencies() {
    local deps=("docker" "kubectl" "aws")
    for dep in "${deps[@]}"; do
        if ! command -v $dep &> /dev/null; then
            echo_error "$dep is not installed or not in PATH"
            exit 1
        fi
    done
    
    # Check if docker buildx is available
    if ! docker buildx version &> /dev/null; then
        echo_error "Docker buildx is not available. Please install Docker Desktop or enable buildx."
        exit 1
    fi
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --tag)
            IMAGE_TAG="$2"
            shift 2
            ;;
        --namespace)
            NAMESPACE="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [--tag IMAGE_TAG] [--namespace NAMESPACE]"
            echo "  --tag: Docker image tag (default: latest)"
            echo "  --namespace: Kubernetes namespace (default: default)"
            exit 0
            ;;
        *)
            echo_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Run dependency check
check_dependencies

# Run main function
main
