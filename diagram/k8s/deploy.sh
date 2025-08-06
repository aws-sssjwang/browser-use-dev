#!/bin/bash

# Browser Use WebUI EKS Deployment Script
# This script deploys the browser-use-webui application to an EKS cluster

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
CLUSTER_NAME="browser-use-cluster"
REGION="us-east-1"
NODE_GROUP_NAME="browser-use-nodes"
INSTANCE_TYPE="t3.medium"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REPO_NAME="browser-use-webui"
IMAGE_TAG="latest"

echo -e "${GREEN}=== Browser Use WebUI EKS Deployment ===${NC}"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"
for cmd in aws kubectl docker eksctl; do
    if ! command_exists $cmd; then
        echo -e "${RED}Error: $cmd is not installed${NC}"
        exit 1
    fi
done
echo -e "${GREEN}✓ All prerequisites are installed${NC}"

# Step 1: Create EKS Cluster (if it doesn't exist)
echo -e "${YELLOW}Step 1: Creating EKS cluster...${NC}"
if ! eksctl get cluster --name $CLUSTER_NAME --region $REGION >/dev/null 2>&1; then
    echo "Creating EKS cluster: $CLUSTER_NAME"
    eksctl create cluster \
        --name $CLUSTER_NAME \
        --region $REGION \
        --nodegroup-name $NODE_GROUP_NAME \
        --node-type $INSTANCE_TYPE \
        --nodes 1 \
        --nodes-min 1 \
        --nodes-max 3 \
        --managed
    echo -e "${GREEN}✓ EKS cluster created successfully${NC}"
else
    echo -e "${GREEN}✓ EKS cluster already exists${NC}"
fi

# Step 2: Update kubeconfig
echo -e "${YELLOW}Step 2: Updating kubeconfig...${NC}"
aws eks update-kubeconfig --region $REGION --name $CLUSTER_NAME
echo -e "${GREEN}✓ Kubeconfig updated${NC}"

# Step 3: Create ECR repository (if it doesn't exist)
echo -e "${YELLOW}Step 3: Setting up ECR repository...${NC}"
if ! aws ecr describe-repositories --repository-names $ECR_REPO_NAME --region $REGION >/dev/null 2>&1; then
    echo "Creating ECR repository: $ECR_REPO_NAME"
    aws ecr create-repository --repository-name $ECR_REPO_NAME --region $REGION
    echo -e "${GREEN}✓ ECR repository created${NC}"
else
    echo -e "${GREEN}✓ ECR repository already exists${NC}"
fi

# Step 4: Build and push Docker image
echo -e "${YELLOW}Step 4: Building and pushing Docker image...${NC}"
ECR_URI="$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$ECR_REPO_NAME:$IMAGE_TAG"

# Login to ECR
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com

# Build and tag image
docker build -t $ECR_REPO_NAME:$IMAGE_TAG .
docker tag $ECR_REPO_NAME:$IMAGE_TAG $ECR_URI

# Push image
docker push $ECR_URI
echo -e "${GREEN}✓ Docker image pushed to ECR${NC}"

# Step 5: Create IAM role for IRSA
echo -e "${YELLOW}Step 5: Setting up IAM role for service account...${NC}"
ROLE_NAME="browser-use-webui-role"
POLICY_NAME="browser-use-webui-policy"

# Create trust policy
cat > trust-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::$ACCOUNT_ID:oidc-provider/$(aws eks describe-cluster --name $CLUSTER_NAME --region $REGION --query "cluster.identity.oidc.issuer" --output text | sed 's|https://||')"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "$(aws eks describe-cluster --name $CLUSTER_NAME --region $REGION --query "cluster.identity.oidc.issuer" --output text | sed 's|https://||'):sub": "system:serviceaccount:default:browser-use-webui-sa",
          "$(aws eks describe-cluster --name $CLUSTER_NAME --region $REGION --query "cluster.identity.oidc.issuer" --output text | sed 's|https://||'):aud": "sts.amazonaws.com"
        }
      }
    }
  ]
}
EOF

# Create IAM policy for AWS services
cat > iam-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "sagemaker:CreatePresignedDomainUrl",
        "sagemaker:DescribeDomain",
        "sagemaker:DescribeUserProfile",
        "sagemaker:DescribeSpace"
      ],
      "Resource": "*"
    }
  ]
}
EOF

# Create IAM policy
if ! aws iam get-policy --policy-arn "arn:aws:iam::$ACCOUNT_ID:policy/$POLICY_NAME" >/dev/null 2>&1; then
    aws iam create-policy --policy-name $POLICY_NAME --policy-document file://iam-policy.json
    echo -e "${GREEN}✓ IAM policy created${NC}"
else
    echo -e "${GREEN}✓ IAM policy already exists${NC}"
fi

# Create IAM role
if ! aws iam get-role --role-name $ROLE_NAME >/dev/null 2>&1; then
    aws iam create-role --role-name $ROLE_NAME --assume-role-policy-document file://trust-policy.json
    aws iam attach-role-policy --role-name $ROLE_NAME --policy-arn "arn:aws:iam::$ACCOUNT_ID:policy/$POLICY_NAME"
    echo -e "${GREEN}✓ IAM role created and policy attached${NC}"
else
    echo -e "${GREEN}✓ IAM role already exists${NC}"
fi

# Clean up temporary files
rm -f trust-policy.json iam-policy.json

# Step 6: Update Kubernetes manifests with actual values
echo -e "${YELLOW}Step 6: Updating Kubernetes manifests...${NC}"
sed -i.bak "s|browser-use-webui:latest|$ECR_URI|g" k8s/deployment.yaml
sed -i.bak "s|ACCOUNT_ID|$ACCOUNT_ID|g" k8s/serviceaccount.yaml

# Step 7: Deploy to Kubernetes
echo -e "${YELLOW}Step 7: Deploying to Kubernetes...${NC}"
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/serviceaccount.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml

echo -e "${GREEN}✓ Application deployed to Kubernetes${NC}"

# Step 8: Wait for deployment to be ready
echo -e "${YELLOW}Step 8: Waiting for deployment to be ready...${NC}"
kubectl wait --for=condition=available --timeout=300s deployment/browser-use-webui

# Step 9: Show deployment status
echo -e "${YELLOW}Step 9: Deployment status${NC}"
kubectl get pods -l app=browser-use-webui
kubectl get services browser-use-webui-service

echo -e "${GREEN}=== Deployment Complete! ===${NC}"
echo -e "${YELLOW}To access the application:${NC}"
echo "1. Port forward to access locally:"
echo "   kubectl port-forward service/browser-use-webui-service 7788:7788"
echo "2. Then open: http://localhost:7788"
echo ""
echo "3. For VNC access:"
echo "   kubectl port-forward service/browser-use-webui-service 6080:6080"
echo "4. Then open: http://localhost:6080/vnc.html"
echo ""
echo -e "${YELLOW}To clean up:${NC}"
echo "eksctl delete cluster --name $CLUSTER_NAME --region $REGION"
