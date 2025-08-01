#!/bin/bash

# Browser Use WebUI EKS Upgrade Script
# This script upgrades the existing browser-use-webui deployment with Arka's modifications

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
CLUSTER_NAME="browser-use-deployment-cluster"
REGION="us-east-1"
ACCOUNT_ID="137386359997"
ECR_REPO_NAME="browser-use-webui"
IMAGE_TAG="latest"
ECR_URI="$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$ECR_REPO_NAME:$IMAGE_TAG"
ROLE_NAME="browser-use-webui-role"
POLICY_NAME="browser-use-webui-bedrock-policy"

echo -e "${GREEN}=== Browser Use WebUI EKS Upgrade (with Arka's modifications) ===${NC}"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"
for cmd in aws kubectl; do
    if ! command_exists $cmd; then
        echo -e "${RED}Error: $cmd is not installed${NC}"
        exit 1
    fi
done
echo -e "${GREEN}✓ All prerequisites are installed${NC}"

# Verify cluster connection
echo -e "${YELLOW}Verifying cluster connection...${NC}"
if ! kubectl cluster-info >/dev/null 2>&1; then
    echo -e "${RED}Error: Cannot connect to Kubernetes cluster${NC}"
    echo "Please ensure kubectl is configured for cluster: $CLUSTER_NAME"
    exit 1
fi

CURRENT_CONTEXT=$(kubectl config current-context)
echo -e "${GREEN}✓ Connected to cluster: $CURRENT_CONTEXT${NC}"

# Step 1: Update IAM policy for Bedrock access
echo -e "${YELLOW}Step 1: Updating IAM policy for Bedrock access...${NC}"

# Check if policy exists and update it
if aws iam get-policy --policy-arn "arn:aws:iam::$ACCOUNT_ID:policy/$POLICY_NAME" >/dev/null 2>&1; then
    echo "Updating existing IAM policy..."
    # Create new policy version
    aws iam create-policy-version \
        --policy-arn "arn:aws:iam::$ACCOUNT_ID:policy/$POLICY_NAME" \
        --policy-document file://k8s/iam-policy.json \
        --set-as-default
    echo -e "${GREEN}✓ IAM policy updated${NC}"
else
    echo "Creating new IAM policy..."
    aws iam create-policy \
        --policy-name $POLICY_NAME \
        --policy-document file://k8s/iam-policy.json
    
    # Attach policy to existing role
    aws iam attach-role-policy \
        --role-name $ROLE_NAME \
        --policy-arn "arn:aws:iam::$ACCOUNT_ID:policy/$POLICY_NAME"
    echo -e "${GREEN}✓ IAM policy created and attached${NC}"
fi

# Step 2: Backup current deployment
echo -e "${YELLOW}Step 2: Creating backup of current deployment...${NC}"
kubectl get deployment browser-use-webui -o yaml > k8s/backup-deployment-$(date +%Y%m%d-%H%M%S).yaml
echo -e "${GREEN}✓ Backup created${NC}"

# Step 3: Apply updated Kubernetes resources
echo -e "${YELLOW}Step 3: Applying updated Kubernetes resources...${NC}"

# Apply in order
echo "Applying Secret..."
kubectl apply -f k8s/secret.yaml

echo "Applying ServiceAccount..."
kubectl apply -f k8s/serviceaccount.yaml

echo "Applying Service..."
kubectl apply -f k8s/service.yaml

echo "Applying Deployment..."
kubectl apply -f k8s/deployment.yaml

echo -e "${GREEN}✓ Kubernetes resources applied${NC}"

# Step 4: Wait for rollout to complete
echo -e "${YELLOW}Step 4: Waiting for deployment rollout...${NC}"
kubectl rollout status deployment/browser-use-webui --timeout=300s

# Step 5: Verify deployment
echo -e "${YELLOW}Step 5: Verifying deployment...${NC}"
echo -e "${BLUE}Pod Status:${NC}"
kubectl get pods -l app=browser-use-webui

echo -e "${BLUE}Service Status:${NC}"
kubectl get service browser-use-webui-service

echo -e "${BLUE}Deployment Status:${NC}"
kubectl get deployment browser-use-webui

# Step 6: Check pod logs for any issues
echo -e "${YELLOW}Step 6: Checking pod logs...${NC}"
POD_NAME=$(kubectl get pods -l app=browser-use-webui -o jsonpath='{.items[0].metadata.name}')
if [ ! -z "$POD_NAME" ]; then
    echo -e "${BLUE}Recent logs from pod $POD_NAME:${NC}"
    kubectl logs $POD_NAME --tail=20
else
    echo -e "${RED}No pods found${NC}"
fi

# Step 7: Test connectivity
echo -e "${YELLOW}Step 7: Testing connectivity...${NC}"
echo "Testing if pod is responding..."
if kubectl exec $POD_NAME -- curl -f http://localhost:7788 >/dev/null 2>&1; then
    echo -e "${GREEN}✓ Pod is responding on port 7788${NC}"
else
    echo -e "${YELLOW}⚠ Pod may still be starting up${NC}"
fi

echo -e "${GREEN}=== Upgrade Complete! ===${NC}"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Test the application with port forwarding:"
echo "   kubectl port-forward service/browser-use-webui-service 7788:7788"
echo "   Then open: http://localhost:7788"
echo ""
echo "2. Test VNC access:"
echo "   kubectl port-forward service/browser-use-webui-service 6080:6080"
echo "   Then open: http://localhost:6080/vnc.html"
echo ""
echo "3. Your ALB and CloudFront should automatically pick up the changes"
echo ""
echo -e "${YELLOW}New Features Available:${NC}"
echo "• AWS Bedrock LLM integration"
echo "• Placeholder functionality for dynamic URLs"
echo "• Prerequisite code execution"
echo ""
echo -e "${YELLOW}To rollback if needed:${NC}"
echo "kubectl apply -f k8s/backup-deployment-*.yaml"
