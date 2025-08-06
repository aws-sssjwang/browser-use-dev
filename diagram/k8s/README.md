# Browser Use WebUI - EKS Deployment Guide

This directory contains Kubernetes manifests and deployment scripts for deploying the Browser Use WebUI application to Amazon EKS.

## Prerequisites

Before deploying, ensure you have the following tools installed:

- [AWS CLI](https://aws.amazon.com/cli/) - configured with appropriate permissions
- [kubectl](https://kubernetes.io/docs/tasks/tools/) - Kubernetes command-line tool
- [eksctl](https://eksctl.io/) - EKS cluster management tool
- [Docker](https://www.docker.com/) - for building and pushing images

## Quick Deployment

The easiest way to deploy is using the automated deployment script:

```bash
./deploy.sh
```

This script will:
1. Create an EKS cluster (if it doesn't exist)
2. Set up ECR repository
3. Build and push Docker image
4. Configure IAM roles for AWS service access
5. Deploy the application to Kubernetes
6. Provide access instructions

## Manual Deployment

If you prefer to deploy manually, follow these steps:

### 1. Create EKS Cluster

```bash
eksctl create cluster \
    --name browser-use-cluster \
    --region us-east-1 \
    --nodegroup-name browser-use-nodes \
    --node-type t3.medium \
    --nodes 1 \
    --nodes-min 1 \
    --nodes-max 3 \
    --managed
```

### 2. Update kubeconfig

```bash
aws eks update-kubeconfig --region us-east-1 --name browser-use-cluster
```

### 3. Build and Push Docker Image

```bash
# Get your AWS account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Create ECR repository
aws ecr create-repository --repository-name browser-use-webui --region us-east-1

# Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

# Build and push image
docker build -t browser-use-webui:latest .
docker tag browser-use-webui:latest $ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/browser-use-webui:latest
docker push $ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/browser-use-webui:latest
```

### 4. Update Kubernetes Manifests

Update the image reference in `deployment.yaml`:

```bash
sed -i "s|browser-use-webui:latest|$ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/browser-use-webui:latest|g" deployment.yaml
sed -i "s|ACCOUNT_ID|$ACCOUNT_ID|g" serviceaccount.yaml
```

### 5. Create IAM Role for Service Account

Create an IAM role with the necessary permissions for AWS Bedrock and SageMaker:

```bash
# Create IAM policy (see deploy.sh for full policy)
aws iam create-policy --policy-name browser-use-webui-policy --policy-document file://iam-policy.json

# Create IAM role with OIDC trust relationship
aws iam create-role --role-name browser-use-webui-role --assume-role-policy-document file://trust-policy.json

# Attach policy to role
aws iam attach-role-policy --role-name browser-use-webui-role --policy-arn arn:aws:iam::$ACCOUNT_ID:policy/browser-use-webui-policy
```

### 6. Deploy to Kubernetes

```bash
kubectl apply -f secret.yaml
kubectl apply -f serviceaccount.yaml
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
```

## Accessing the Application

### Web UI Access

1. Port forward to access the web interface:
```bash
kubectl port-forward service/browser-use-webui-service 7788:7788
```

2. Open your browser and navigate to: `http://localhost:7788`

### VNC Access

1. Port forward for VNC access:
```bash
kubectl port-forward service/browser-use-webui-service 6080:6080
```

2. Open your browser and navigate to: `http://localhost:6080/vnc.html`
3. Use password: `vncpassword` (or the password you set in the secret)

## Configuration

### Environment Variables

The application can be configured using environment variables in the deployment:

- `AWS_BEDROCK_REGION`: AWS region for Bedrock service (default: us-west-2)
- `AWS_DEFAULT_REGION`: Default AWS region (default: us-east-1)
- `SAGEMAKER_DOMAIN_ID`: Your SageMaker domain ID
- `SAGEMAKER_USER_PROFILE_NAME`: Your SageMaker user profile name
- `SAGEMAKER_SPACE_NAME`: Your SageMaker space name
- `DEFAULT_LLM`: Default LLM provider (default: bedrock)
- `VNC_PASSWORD`: VNC access password (stored in secret)

### Resource Limits

The deployment includes resource requests and limits:

- **Requests**: 2Gi memory, 1000m CPU
- **Limits**: 4Gi memory, 2000m CPU

Adjust these values in `deployment.yaml` based on your needs.

### Security

The application runs with:
- Service account with IRSA for AWS access
- SYS_ADMIN capability for browser functionality
- Shared memory volume for browser operations

## Troubleshooting

### Check Pod Status

```bash
kubectl get pods -l app=browser-use-webui
kubectl describe pod <pod-name>
```

### View Logs

```bash
kubectl logs -l app=browser-use-webui -f
```

### Check Service

```bash
kubectl get service browser-use-webui-service
kubectl describe service browser-use-webui-service
```

### Common Issues

1. **Image Pull Errors**: Ensure ECR repository exists and image is pushed
2. **AWS Permission Errors**: Verify IAM role and IRSA configuration
3. **Resource Issues**: Check if cluster has sufficient resources
4. **Network Issues**: Verify security groups and network configuration

## Cleanup

To remove the deployment:

```bash
kubectl delete -f .
```

To delete the entire EKS cluster:

```bash
eksctl delete cluster --name browser-use-cluster --region us-east-1
```

## Files Description

- `deployment.yaml`: Main application deployment
- `service.yaml`: Kubernetes service for network access
- `serviceaccount.yaml`: Service account with IRSA configuration
- `secret.yaml`: Secret for VNC password
- `deploy.sh`: Automated deployment script
- `README.md`: This documentation file

## Support

For issues related to:
- Browser Use functionality: Check the main project repository
- Kubernetes deployment: Review this documentation and logs
- AWS services: Consult AWS documentation for Bedrock and SageMaker
