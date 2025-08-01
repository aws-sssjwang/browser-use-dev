# 手动部署步骤指南

## ✅ **已完成步骤**
- Docker镜像构建成功: `137386359997.dkr.ecr.us-east-1.amazonaws.com/web-ui:latest`
- 镜像包含所有修复：headless配置、placeholder逻辑、浏览器视图增强

## 🚀 **接下来需要手动执行的步骤**

### **Step 1: ECR登录和推送**
```bash
# 1. 登录到ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 137386359997.dkr.ecr.us-east-1.amazonaws.com

# 2. 推送镜像到ECR (这一步会耗时较长)
docker push 137386359997.dkr.ecr.us-east-1.amazonaws.com/web-ui:latest
```

### **Step 2: 更新Kubernetes配置**
```bash
# 3. 更新kubeconfig
aws eks update-kubeconfig --region us-east-1 --name browser-use-deployment-cluster

# 4. 更新deployment.yaml中的镜像
sed -i.bak "s|image: PLACEHOLDER_ECR_IMAGE|image: 137386359997.dkr.ecr.us-east-1.amazonaws.com/web-ui:latest|g" k8s/deployment.yaml
```

### **Step 3: 部署到EKS**
```bash
# 5. 应用Kubernetes配置
kubectl apply -f k8s/

# 6. 等待部署完成
kubectl rollout status deployment/web-ui-deployment -n default --timeout=300s

# 7. 检查部署状态
kubectl get pods -n default -l app=web-ui
kubectl get svc -n default
kubectl get ingress -n default
```

### **Step 4: 恢复原始配置**
```bash
# 8. 恢复原始deployment.yaml
mv k8s/deployment.yaml.bak k8s/deployment.yaml
```

## 🔍 **验证部署**

### **检查Pod状态**
```bash
kubectl get pods -l app=web-ui
kubectl logs -f deployment/web-ui-deployment
```

### **测试应用**
- CloudFront URL: http://dsjpnyogrtasp.cloudfront.net
- 测试任务: "open google.com"
- 验证浏览器视图是否显示实时截图

## 📋 **关键修复内容**
1. **HEADLESS=true**: 容器环境默认启用headless模式
2. **Placeholder修复**: 只替换实际存在的placeholder
3. **浏览器视图**: 在headless模式下提供实时截图
4. **AWS Bedrock**: 支持AWS Bedrock LLM

## 🚨 **注意事项**
- ECR推送可能需要5-10分钟，请耐心等待
- 如果推送失败，检查AWS凭证和网络连接
- 部署后等待2-3分钟让Pod完全启动
- CloudFront缓存更新可能需要几分钟

## 🎯 **预期结果**
部署成功后，应用将：
- 在EKS集群中稳定运行
- 通过ALB和CloudFront正常访问
- 支持headless浏览器操作
- 提供实时的浏览器截图反馈
- 正确处理AWS Bedrock LLM调用

执行完这些步骤后，你的云端部署就会包含所有本地修复的功能！
