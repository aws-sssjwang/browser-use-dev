# 🔧 **SageMaker 权限问题修复总结**

## 🚨 **问题诊断**

### **问题现象：**
- 简单任务（如 "open google and search aws"）可以正常响应
- 但包含 prerequisite 代码的复杂任务没有响应
- Prerequisite 代码涉及 SageMaker API 调用

### **根本原因：**
通过检查 Pod 日志发现了 **SageMaker IAM 权限问题**：

```
AccessDeniedException: User: arn:aws:sts::137386359997:assumed-role/eksctl-browser-use-deployment-clus-NodeInstanceRole-6AeLt8W3kBCM/i-067e8c7b4ac66fc64 is not authorized to perform: sagemaker:CreatePresignedDomainUrl on resource: arn:aws:sagemaker:us-east-1:137386359997:user-profile/d-9cpchwz1nnno/adam-test-user-1752279282450
```

**问题分析：**
- 您的 prerequisite 代码需要调用 `sagemaker:CreatePresignedDomainUrl` API
- EKS 节点的 IAM 角色缺少 SageMaker 相关权限
- 之前只添加了 Bedrock 权限，但没有 SageMaker 权限

## ✅ **解决方案实施**

### **第一步：创建 SageMaker 访问策略**
创建了 `BrowserUseSageMaker` IAM 策略，包含以下权限：
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "sagemaker:CreatePresignedDomainUrl",
                "sagemaker:DescribeDomain",
                "sagemaker:DescribeUserProfile",
                "sagemaker:ListDomains",
                "sagemaker:ListUserProfiles"
            ],
            "Resource": [
                "arn:aws:sagemaker:us-east-1:137386359997:domain/*",
                "arn:aws:sagemaker:us-east-1:137386359997:user-profile/*/*"
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
aws iam create-policy --policy-name BrowserUseSageMaker --policy-document file://sagemaker-access-policy.json

# 附加策略到角色
aws iam attach-role-policy --role-name eksctl-browser-use-deployment-clus-NodeInstanceRole-6AeLt8W3kBCM --policy-arn arn:aws:iam::137386359997:policy/BrowserUseSageMaker
```

### **第三步：重启 Pod 使权限生效**
```bash
kubectl delete pod browser-use-deployment-5df9f9fb4f-8nppl
```

## 🎯 **当前状态**

### **✅ 已修复：**
- **SageMaker 权限**：EKS 节点角色现在具有 SageMaker 访问权限
- **策略附加**：`BrowserUseSageMaker` 策略已成功附加
- **Pod 重启**：新 Pod 已启动并运行正常

### **📋 当前角色权限：**
EKS 节点角色现在包含以下策略：
- ✅ `BrowserUseBedrock` (之前添加)
- ✅ `BrowserUseSageMaker` (新增)
- ✅ `AmazonSSMManagedInstanceCore`
- ✅ `AmazonEKSWorkerNodePolicy`
- ✅ `AmazonEC2ContainerRegistryPullOnly`

## 🧪 **测试建议**

现在您可以通过 CloudFront URL 重新测试包含 prerequisite 代码的复杂任务：

### **Prerequisite 代码：**
```python
import boto3
session = boto3.Session(region_name="us-east-1")
sagemaker_client = session.client("sagemaker")
response = sagemaker_client.create_presigned_domain_url(
    DomainId="d-9cpchwz1nnno",
    UserProfileName="adam-test-user-1752279282450",
    SpaceName="adam-space-1752279293076"
)
PLACEHOLDERS={}
PLACEHOLDERS["PLACEHOLDER_URL"] = response["AuthorizedUrl"]
```

### **任务示例：**
```
open PLACEHOLDER_URL
Click on text "File"
Click on text "New" not "New Launcher"
Click on text "Notebook" not "Console" or "Terminal"
...
```

## 🔍 **问题解决过程回顾**

### **第一次问题：Bedrock 权限**
- **现象**：简单任务也没有响应
- **原因**：缺少 `bedrock:InvokeModel` 权限
- **解决**：添加 `BrowserUseBedrock` 策略

### **第二次问题：SageMaker 权限**
- **现象**：简单任务有响应，但复杂任务（包含 prerequisite）没有响应
- **原因**：缺少 `sagemaker:CreatePresignedDomainUrl` 权限
- **解决**：添加 `BrowserUseSageMaker` 策略

## 🚀 **后续建议**

### **权限管理最佳实践：**
1. **按需添加权限**：根据实际使用的 AWS 服务逐步添加权限
2. **最小权限原则**：只授予必要的权限，避免过度授权
3. **权限监控**：设置 CloudTrail 监控权限使用情况

### **可能需要的其他权限：**
如果您的任务还涉及其他 AWS 服务，可能需要添加相应权限：
- **S3**：如果需要访问 S3 存储桶
- **EC2**：如果需要管理 EC2 实例
- **Lambda**：如果需要调用 Lambda 函数
- **其他服务**：根据实际需求添加

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

**问题已解决！** 🎉 您的系统现在应该能够正常执行包含 SageMaker API 调用的复杂任务了。
