# 🚀 EKS Deployment Guide

This guide provides step-by-step instructions for building and deploying the Browser Use Web UI with AWS Bedrock and SageMaker integration to your existing EKS cluster.

## 📋 Prerequisites

### Required Tools
- Docker with buildx support
- kubectl configured for your EKS cluster
- AWS CLI configured with appropriate permissions
- Access to your EKS cluster: `browser-use-deployment-cluster` in `us-east-1`

### AWS Permissions Required
- ECR: Create repositories, push/pull images
- EKS: Access to cluster and deployments
- SageMaker: Create presigned domain URLs
- Bedrock: Access to Claude models

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   CloudFront    │────│      ALB        │────│   EKS Cluster   │
│                 │    │                 │    │                 │
│ dsjpnyogrtasp   │    │  Load Balancer  │    │   Web UI Pod    │
│ .cloudfront.net │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
                                               ┌───────┴───────┐
                                               │               │
                                         ┌─────────┐   ┌─────────────┐
                                         │ Bedrock │   │ SageMaker   │
                                         │ Claude  │   │   Studio    │
                                         └─────────┘   └─────────────┘
```

## 🐳 Step 1: Local Testing (Optional but Recommended)

Before deploying to EKS, test the Docker image locally:

```bash
# Make the script executable
chmod +x test_docker_local.sh

# Build and run locally
./test_docker_local.sh test

# Access the application
# - Web UI: http://localhost:7788
# - VNC: http://localhost:6080

# View logs
./test_docker_local.sh logs

# Stop the test
./test_docker_local.sh stop
```

## 🚀 Step 2: Build and Deploy to EKS

### Quick Deploy
```bash
# Make the script executable
chmod +x build_and_deploy.sh

# Deploy with default settings
./build_and_deploy.sh
```

### Custom Deploy
```bash
# Deploy with custom tag
./build_and_deploy.sh --tag v1.0.0

# Deploy to specific namespace
./build_and_deploy.sh --namespace production
```

## 📊 Step 3: Verify Deployment

### Check Pod Status
```bash
kubectl get pods -l app=web-ui
kubectl logs -f deployment/web-ui-deployment
```

### Check Service and Ingress
```bash
kubectl get svc
kubectl get ingress
```

### Test Application
- **CloudFront URL**: http://dsjpnyogrtasp.cloudfront.net
- **Direct ALB**: Check ingress output for ALB URL

## 🔧 Configuration Details

### Environment Variables
The deployment includes these key environment variables:

```yaml
- AWS_BEDROCK_REGION: "us-west-2"
- AWS_DEFAULT_REGION: "us-east-1"
- SAGEMAKER_DOMAIN_ID: "d-9cpchwz1nnno"
- SAGEMAKER_USER_PROFILE_NAME: "adam-test-user-1752279282450"
- SAGEMAKER_SPACE_NAME: "adam-space-1752279293076"
- DEFAULT_LLM: "bedrock"
```

### Resource Limits
```yaml
resources:
  requests:
    memory: "2Gi"
    cpu: "1000m"
  limits:
    memory: "4Gi"
    cpu: "2000m"
```

## 🔍 Troubleshooting

### Common Issues

#### 1. ECR Authentication Failed
```bash
# Re-authenticate with ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com
```

#### 2. EKS Access Denied
```bash
# Update kubeconfig
aws eks update-kubeconfig --region us-east-1 --name browser-use-deployment-cluster
```

#### 3. Pod CrashLoopBackOff
```bash
# Check pod logs
kubectl logs -f deployment/web-ui-deployment
kubectl describe pod <pod-name>
```

#### 4. Image Pull Errors
```bash
# Verify image exists in ECR
aws ecr describe-images --repository-name web-ui --region us-east-1
```

### Debug Commands
```bash
# Get detailed pod information
kubectl describe deployment web-ui-deployment

# Check events
kubectl get events --sort-by=.metadata.creationTimestamp

# Access pod shell
kubectl exec -it deployment/web-ui-deployment -- /bin/bash

# Port forward for direct access
kubectl port-forward deployment/web-ui-deployment 7788:7788
```

## 🔄 Rolling Updates

To update the deployment with a new version:

```bash
# Build and deploy new version
./build_and_deploy.sh --tag v1.1.0

# Or manually update image
kubectl set image deployment/web-ui-deployment web-ui=<account-id>.dkr.ecr.us-east-1.amazonaws.com/web-ui:v1.1.0

# Check rollout status
kubectl rollout status deployment/web-ui-deployment
```

## 📝 Key Features Deployed

✅ **Prerequisite System**: Dynamic SageMaker URL generation  
✅ **AWS Bedrock Integration**: Claude model support  
✅ **SageMaker Studio**: Automated workspace access  
✅ **Placeholder Replacement**: Dynamic URL injection  
✅ **Multi-platform Support**: linux/amd64 optimized  
✅ **Health Checks**: Kubernetes readiness/liveness probes  
✅ **Resource Management**: Proper CPU/memory limits  
✅ **Security**: Service account with IAM roles  

## 🌐 Access Points

After successful deployment:

- **Primary Access**: http://dsjpnyogrtasp.cloudfront.net
- **VNC Access**: http://dsjpnyogrtasp.cloudfront.net:6080 (if exposed)
- **Health Check**: `<alb-url>/health` (if implemented)

## 📞 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review pod logs: `kubectl logs -f deployment/web-ui-deployment`
3. Verify AWS credentials and permissions
4. Ensure EKS cluster access is properly configured

---

**Note**: This deployment replaces your existing Docker image while maintaining all existing ALB and CloudFront configurations.
