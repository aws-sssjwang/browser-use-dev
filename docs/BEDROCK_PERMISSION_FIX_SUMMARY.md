# 🔧 **Bedrock 权限问题修复总结**

## 🚨 **问题诊断**

### **问题现象：**
- 在部署 `long-url-fix` 镜像后，简单的 prompt（如 "open google and search aws"）没有响应
- 通过 CloudFront URL 访问系统

### **根本原因：**
通过检查 Pod 日志发现了 **AWS IAM 权限问题**：

```
AccessDeniedException: User: arn:aws:sts::137386359997:assumed-role/eksctl-browser-use-deployment-clus-NodeInstanceRole-6AeLt8W3kBCM/i-067e8c7b4ac66fc64 is not authorized to perform: bedrock:InvokeModel on resource: arn:aws:bedrock:us-west-2::foundation-model/anthropic.claude-3-5-sonnet-20241022-v2:0
```

**问题分析：**
- EKS 节点的 IAM 角色缺少调用 Bedrock 模型的权限
- 之前可能通过其他方式配置了权限，但在新镜像部署后失效
- Pod 使用默认的 Service Account，依赖节点 IAM 角色权限

## ✅ **解决方案实施**

### **第一步：创建 Bedrock 访问策略**
创建了 `BrowserUseBedrock` IAM 策略，包含以下权限：
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel",
                "bedrock:InvokeModelWithResponseStream"
            ],
            "Resource": [
                "arn:aws:bedrock:*::foundation-model/anthropic.claude-*",
                "arn:aws:bedrock:*::foundation-model/amazon.titan-*",
                "arn:aws:bedrock:*::foundation-model/meta.llama2-*",
                "arn:aws:bedrock:*::foundation-model/cohere.command-*"
            ]
        }
    ]
}
```

### **第二步：附加策略到 EKS 节点角色**
将策略附加到角色：`eksctl-browser-use-deployment-clus-NodeInstanceRole-6AeLt8W3kBCM`

**执行的命令：**
```bash
# 创建策略
aws iam create-policy --policy-name BrowserUseBedrock --policy-document file://bedrock-access-policy.json

# 附加策略到角色
aws iam attach-role-policy --role-name eksctl-browser-use-deployment-clus-NodeInstanceRole-6AeLt8W3kBCM --policy-arn arn:aws:iam::137386359997:policy/BrowserUseBedrock
```

### **第三步：重启 Pod 使权限生效**
```bash
kubectl delete pod browser-use-deployment-5df9f9fb4f-k8mqb
```

## 🎯 **当前状态**

### **✅ 已修复：**
- **IAM 权限**：EKS 节点角色现在具有 Bedrock 访问权限
- **策略附加**：`BrowserUseBedrock` 策略已成功附加
- **Pod 重启**：新 Pod 已启动并运行正常

### **📋 当前角色权限：**
EKS 节点角色现在包含以下策略：
- ✅ `BrowserUseBedrock` (新增)
- ✅ `AmazonSSMManagedInstanceCore`
- ✅ `AmazonEKSWorkerNodePolicy`
- ✅ `AmazonEC2ContainerRegistryPullOnly`

## 🧪 **测试建议**

现在您可以通过 CloudFront URL 重新测试系统：

1. **访问 Web UI**
2. **输入简单的 prompt**：如 "open google and search aws"
3. **验证响应**：系统应该能够正常调用 Bedrock 并执行任务

## 🔍 **为什么之前有权限？**

可能的原因：
1. **之前的镜像**可能使用了不同的权限配置方式
2. **环境变量**中可能包含了 AWS 凭证
3. **Service Account**可能之前配置了 IRSA (IAM Roles for Service Accounts)
4. **临时凭证**可能之前通过其他方式注入

## 🚀 **后续建议**

### **最佳实践：**
1. **使用 IRSA**：考虑为更精细的权限控制配置 IAM Roles for Service Accounts
2. **最小权限原则**：当前策略允许访问多个 Bedrock 模型，可以根据实际需要进一步限制
3. **监控**：设置 CloudWatch 监控来跟踪 Bedrock API 调用

### **如果问题仍然存在：**
1. 检查 Bedrock 模型是否在正确的区域启用
2. 验证 AWS 区域配置是否正确
3. 检查网络连接和安全组设置

## 📊 **验证命令**

如需验证权限是否正确配置：
```bash
# 检查角色权限
aws iam list-attached-role-policies --role-name eksctl-browser-use-deployment-clus-NodeInstanceRole-6AeLt8W3kBCM

# 检查 Pod 状态
kubectl get pods -l app=browser-use

# 查看 Pod 日志
kubectl logs -l app=browser-use --tail=50
```

---

**问题已解决！** 🎉 您的系统现在应该能够正常响应 Bedrock LLM 请求了。
