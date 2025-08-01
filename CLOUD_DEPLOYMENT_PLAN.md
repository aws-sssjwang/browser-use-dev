# 云端部署更新计划

## 🎯 **目标**
将本地修复的Browser Use Web UI部署到EKS集群，确保：
- 修复的浏览器功能正常工作
- Prerequisite功能正确执行
- ALB和CloudFront配置保持不变
- 零停机时间更新

## 📋 **修复内容总结**
1. **浏览器配置修复**: 默认启用headless模式
2. **Placeholder替换逻辑修复**: 只替换实际存在的placeholder
3. **浏览器视图增强**: 在headless模式下提供实时截图
4. **环境变量优化**: 容器环境默认配置

## 🚀 **部署步骤**

### **Step 1: 构建和推送新镜像**
```bash
# 构建新的Docker镜像
./build_and_deploy.sh

# 或者手动执行：
# docker build --platform linux/amd64 -t web-ui:latest .
# docker tag web-ui:latest <ECR_REPO>:v1.1-fixed
# docker push <ECR_REPO>:v1.1-fixed
```

### **Step 2: 更新Kubernetes配置**
需要确保deployment.yaml包含：
```yaml
env:
- name: HEADLESS
  value: "true"
- name: USE_OWN_BROWSER
  value: "false"
- name: KEEP_BROWSER_OPEN
  value: "true"
```

### **Step 3: 执行滚动更新**
```bash
# 应用更新的配置
kubectl apply -f k8s/

# 监控部署状态
kubectl rollout status deployment/web-ui

# 检查Pod状态
kubectl get pods -l app=web-ui
```

### **Step 4: 验证部署**
```bash
# 检查Pod日志
kubectl logs -f deployment/web-ui

# 测试健康检查
kubectl get ingress

# 验证ALB状态
```

## 🧪 **测试验证计划**

### **功能测试**
1. **基本功能测试**
   - 访问CloudFront URL
   - 测试Web UI响应
   - 验证Submit Task按钮

2. **Prerequisite功能测试**
   - 测试简单placeholder替换
   - 测试AWS SageMaker prerequisite
   - 验证错误处理

3. **浏览器功能测试**
   - 测试headless模式下的浏览器操作
   - 验证实时截图功能
   - 测试复杂任务执行

### **性能测试**
1. **资源使用监控**
   - CPU和内存使用情况
   - Pod启动时间
   - 响应时间测试

2. **稳定性测试**
   - 长时间运行测试
   - 并发任务测试
   - 错误恢复测试

## 📊 **监控指标**

### **关键日志**
- `✅ Browser initialized`: 浏览器成功启动
- `✅ LLM initialized`: LLM连接正常
- `Replacing placeholder`: Placeholder替换过程
- `✅ Task completed`: 任务执行成功

### **错误指标**
- `❌ Browser failed`: 浏览器启动失败
- `Missing X server`: GUI环境问题
- `Model returned empty`: LLM响应问题
- `Error executing prerequisite`: Prerequisite执行失败

## 🔧 **回滚计划**

如果部署出现问题：
```bash
# 回滚到上一个版本
kubectl rollout undo deployment/web-ui

# 或者回滚到特定版本
kubectl rollout undo deployment/web-ui --to-revision=<revision-number>

# 检查回滚状态
kubectl rollout status deployment/web-ui
```

## 📝 **部署检查清单**

### **部署前检查**
- [ ] 本地Docker测试通过
- [ ] Prerequisite功能验证完成
- [ ] 浏览器功能正常
- [ ] 配置文件更新完成

### **部署中检查**
- [ ] 镜像构建成功
- [ ] 镜像推送到ECR成功
- [ ] Kubernetes配置应用成功
- [ ] Pod滚动更新正常

### **部署后检查**
- [ ] Pod状态健康
- [ ] 服务可访问
- [ ] ALB健康检查通过
- [ ] CloudFront缓存更新
- [ ] 功能测试通过

## 🎉 **预期结果**

部署成功后，系统将具备：
1. **稳定的浏览器操作**: 在headless模式下正常工作
2. **正确的Prerequisite处理**: 支持AWS API调用和参数替换
3. **实时用户反馈**: 通过截图显示浏览器操作过程
4. **云端可扩展性**: 支持EKS集群的自动扩缩容
5. **高可用性**: 通过ALB和CloudFront提供稳定访问

## 📞 **支持信息**

如果部署过程中遇到问题：
1. 检查Pod日志: `kubectl logs -f deployment/web-ui`
2. 检查事件: `kubectl get events --sort-by=.metadata.creationTimestamp`
3. 检查资源状态: `kubectl describe deployment web-ui`
4. 参考修复总结: `BROWSER_FIX_SUMMARY.md`
