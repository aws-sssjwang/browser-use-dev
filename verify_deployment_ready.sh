#!/bin/bash

# Deployment Readiness Verification Script
# Checks if all components are ready for EKS deployment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo_info() {
    echo -e "${GREEN}[✓]${NC} $1"
}

echo_warn() {
    echo -e "${YELLOW}[!]${NC} $1"
}

echo_error() {
    echo -e "${RED}[✗]${NC} $1"
}

echo_header() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check AWS credentials
check_aws_credentials() {
    echo_header "Checking AWS credentials..."
    
    if command_exists aws; then
        if aws sts get-caller-identity >/dev/null 2>&1; then
            ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
            echo_info "AWS credentials configured (Account: $ACCOUNT_ID)"
            return 0
        else
            echo_error "AWS credentials not configured or invalid"
            return 1
        fi
    else
        echo_error "AWS CLI not installed"
        return 1
    fi
}

# Check Docker and buildx
check_docker() {
    echo_header "Checking Docker setup..."
    
    if command_exists docker; then
        if docker info >/dev/null 2>&1; then
            echo_info "Docker is running"
            
            if docker buildx version >/dev/null 2>&1; then
                echo_info "Docker buildx is available"
                return 0
            else
                echo_error "Docker buildx not available"
                return 1
            fi
        else
            echo_error "Docker is not running"
            return 1
        fi
    else
        echo_error "Docker not installed"
        return 1
    fi
}

# Check kubectl
check_kubectl() {
    echo_header "Checking kubectl setup..."
    
    if command_exists kubectl; then
        if kubectl cluster-info >/dev/null 2>&1; then
            CLUSTER_NAME=$(kubectl config current-context)
            echo_info "kubectl configured (Context: $CLUSTER_NAME)"
            return 0
        else
            echo_error "kubectl not configured or cluster not accessible"
            return 1
        fi
    else
        echo_error "kubectl not installed"
        return 1
    fi
}

# Check required files
check_files() {
    echo_header "Checking required files..."
    
    local files=(
        "Dockerfile"
        "requirements.txt"
        "build_and_deploy.sh"
        "test_docker_local.sh"
        "k8s/deployment.yaml"
        "k8s/service.yaml"
        "k8s/secret.yaml"
        "k8s/serviceaccount.yaml"
        "k8s/ingress.yaml"
    )
    
    local missing_files=()
    
    for file in "${files[@]}"; do
        if [[ -f "$file" ]]; then
            echo_info "Found: $file"
        else
            echo_error "Missing: $file"
            missing_files+=("$file")
        fi
    done
    
    if [[ ${#missing_files[@]} -eq 0 ]]; then
        return 0
    else
        echo_error "Missing ${#missing_files[@]} required files"
        return 1
    fi
}

# Check script permissions
check_permissions() {
    echo_header "Checking script permissions..."
    
    local scripts=("build_and_deploy.sh" "test_docker_local.sh")
    
    for script in "${scripts[@]}"; do
        if [[ -x "$script" ]]; then
            echo_info "$script is executable"
        else
            echo_warn "$script is not executable, fixing..."
            chmod +x "$script"
            echo_info "Fixed permissions for $script"
        fi
    done
    
    return 0
}

# Check Python dependencies
check_python_deps() {
    echo_header "Checking Python dependencies..."
    
    if [[ -f "requirements.txt" ]]; then
        local key_deps=("browser-use" "langchain-aws" "boto3" "gradio")
        local missing_deps=()
        
        for dep in "${key_deps[@]}"; do
            if pip show "$dep" >/dev/null 2>&1; then
                echo_info "Found: $dep"
            else
                echo_warn "Missing: $dep"
                missing_deps+=("$dep")
            fi
        done
        
        if [[ ${#missing_deps[@]} -gt 0 ]]; then
            echo_warn "Some Python dependencies are missing. Run: pip install -r requirements.txt"
        fi
    fi
    
    return 0
}

# Check EKS cluster access
check_eks_access() {
    echo_header "Checking EKS cluster access..."
    
    if kubectl get nodes >/dev/null 2>&1; then
        NODE_COUNT=$(kubectl get nodes --no-headers | wc -l)
        echo_info "EKS cluster accessible ($NODE_COUNT nodes)"
        
        # Check if namespace exists
        if kubectl get namespace default >/dev/null 2>&1; then
            echo_info "Default namespace accessible"
        fi
        
        return 0
    else
        echo_error "Cannot access EKS cluster nodes"
        return 1
    fi
}

# Main verification function
main() {
    echo_header "🚀 EKS Deployment Readiness Check"
    echo_header "=================================="
    echo
    
    local checks_passed=0
    local total_checks=7
    
    # Run all checks
    check_aws_credentials && ((checks_passed++))
    echo
    
    check_docker && ((checks_passed++))
    echo
    
    check_kubectl && ((checks_passed++))
    echo
    
    check_files && ((checks_passed++))
    echo
    
    check_permissions && ((checks_passed++))
    echo
    
    check_python_deps && ((checks_passed++))
    echo
    
    check_eks_access && ((checks_passed++))
    echo
    
    # Summary
    echo_header "Summary"
    echo_header "======="
    
    if [[ $checks_passed -eq $total_checks ]]; then
        echo_info "All checks passed! ✅"
        echo_info "Ready to deploy to EKS!"
        echo
        echo_header "Next steps:"
        echo "1. Test locally (optional): ./test_docker_local.sh"
        echo "2. Deploy to EKS: ./build_and_deploy.sh"
        echo "3. Access via CloudFront: http://dsjpnyogrtasp.cloudfront.net"
        echo
        return 0
    else
        echo_error "Failed $((total_checks - checks_passed)) out of $total_checks checks"
        echo_error "Please fix the issues above before deploying"
        echo
        return 1
    fi
}

# Run main function
main "$@"
