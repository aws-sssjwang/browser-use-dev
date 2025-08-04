# 🔍 SageMaker Presigned URL 错误诊断与解决方案

## 📊 **当前状态分析**

**✅ 硬编码参数已部署**：
- 镜像：`web-ui:hardcoded-sagemaker-params`
- Pod 状态：Running（已重启1次）
- 服务：http://dsjpnyogrtasp.cloudfront.net 可访问

**❓ 用户报告的问题**：
- 硬编码参数似乎工作了
- 但在打开后显示 error

---

## 🎯 **可能的错误原因分析**

### 1. **SageMaker Studio 访问权限问题**
**症状**：presigned URL 生成成功，但 SageMaker Studio 页面显示错误
**可能原因**：
- IAM 权限不足
- SageMaker Domain 配置问题
- User Profile 或 Space 不存在/不可访问

### 2. **Presigned URL 过期问题**
**症状**：URL 生成但访问时显示过期错误
**可能原因**：
- Token 已过期
- 时间同步问题

### 3. **网络/代理问题**
**症状**：连接超时或网络错误
**可能原因**：
- VPC 配置问题
- Security Group 限制
- NAT Gateway 问题

---

## 🔧 **诊断步骤**

### 步骤 1：检查 SageMaker 资源状态
```bash
# 检查 Domain 状态
aws sagemaker describe-domain --domain-id d-9cpchwz1nnno

# 检查 User Profile 状态  
aws sagemaker describe-user-profile \
  --domain-id d-9cpchwz1nnno \
  --user-profile-name adam-test-user-1752279282450

# 检查 Space 状态
aws sagemaker describe-space \
  --domain-id d-9cpchwz1nnno \
  --space-name adam-space-1752279293076
```

### 步骤 2：测试 Presigned URL 生成
```python
import boto3

session = boto3.Session(region_name="us-east-1")
sagemaker_client = session.client("sagemaker")

try:
    response = sagemaker_client.create_presigned_domain_url(
        DomainId="d-9cpchwz1nnno",
        UserProfileName="adam-test-user-1752279282450",
        SpaceName="adam-space-1752279293076"
    )
    print(f"✅ URL 生成成功: {response['AuthorizedUrl'][:100]}...")
except Exception as e:
    print(f"❌ URL 生成失败: {e}")
```

### 步骤 3：检查应用程序日志
```bash
# 查看最新的应用程序日志
kubectl logs -l app=browser-use --tail=50 | grep -E "sagemaker|presigned|error"

# 查看 pod 事件
kubectl describe pod -l app=browser-use
```

---

## 🚀 **解决方案**

### 解决方案 1：增强错误处理和日志记录
```python
async def navigate_to_sagemaker_presigned_url(
    domain_id: str, 
    user_profile_name: str, 
    space_name: str, 
    browser: BrowserContext,
    region_name: str = "us-east-1"
):
    try:
        import boto3
        logger.info("Generating presigned URL for SageMaker domain with hardcoded parameters")
        
        # Create boto3 session and client
        session = boto3.Session(region_name="us-east-1")
        sagemaker_client = session.client("sagemaker")
        
        # Generate presigned URL with detailed error handling
        try:
            response = sagemaker_client.create_presigned_domain_url(
                DomainId="d-9cpchwz1nnno",
                UserProfileName="adam-test-user-1752279282450",
                SpaceName="adam-space-1752279293076"
            )
            presigned_url = response["AuthorizedUrl"]
            logger.info(f"✅ Generated presigned URL successfully (length: {len(presigned_url)} chars)")
            logger.info(f"🔗 URL preview: {presigned_url[:100]}...")
            
        except Exception as boto_error:
            error_msg = f"❌ Failed to generate presigned URL: {str(boto_error)}"
            logger.error(error_msg)
            return ActionResult(error=error_msg)
        
        # Navigate with error handling
        try:
            result = await self.registry.execute_action(
                "go_to_url",
                {"url": presigned_url},
                browser=browser
            )
            logger.info("✅ Navigation command executed")
            
            # Wait for page load
            await asyncio.sleep(5)
            
            # Check for common error indicators on the page
            page_content = await browser.get_page_content()
            if any(error_term in page_content.lower() for error_term in 
                   ['error', 'access denied', 'unauthorized', 'expired', 'invalid']):
                logger.warning("⚠️ Possible error detected on SageMaker page")
                logger.info(f"📄 Page content preview: {page_content[:200]}...")
            
            msg = f"Successfully navigated to SageMaker presigned URL"
            logger.info(msg)
            return ActionResult(extracted_content=msg, include_in_memory=True)
            
        except Exception as nav_error:
            error_msg = f"❌ Failed to navigate to presigned URL: {str(nav_error)}"
            logger.error(error_msg)
            return ActionResult(error=error_msg)
            
    except Exception as e:
        error_msg = f"❌ Unexpected error in navigate_to_sagemaker_presigned_url: {str(e)}"
        logger.error(error_msg)
        return ActionResult(error=error_msg)
```

### 解决方案 2：添加重试机制
```python
import time
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def generate_presigned_url_with_retry():
    # 重试逻辑
    pass
```

### 解决方案 3：验证 AWS 权限
确保 IAM Role 包含以下权限：
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
                "sagemaker:DescribeSpace"
            ],
            "Resource": "*"
        }
    ]
}
```

---

## 🔍 **立即诊断建议**

### 1. 检查最新日志
```bash
kubectl logs -l app=browser-use --follow
```

### 2. 手动测试 Presigned URL
在本地运行测试脚本验证 AWS 权限和资源状态

### 3. 检查 SageMaker 控制台
直接在 AWS 控制台验证：
- Domain 状态是否为 "InService"
- User Profile 是否存在且可用
- Space 是否存在且可用

---

## 📋 **下一步行动**

1. **立即**：检查应用程序日志获取具体错误信息
2. **验证**：确认 SageMaker 资源状态
3. **测试**：手动生成 presigned URL 验证权限
4. **修复**：根据具体错误信息应用相应解决方案
5. **部署**：更新代码并重新部署

---

## 🎯 **预期结果**

修复后应该看到：
- ✅ `"✅ Generated presigned URL successfully"`
- ✅ `"✅ Navigation command executed"`
- ✅ 成功访问 SageMaker Studio 界面
- ✅ 无错误页面显示

---

**状态**: 🔍 **诊断中，等待具体错误信息** ⏳  
**下一步**: 检查应用程序日志获取详细错误信息
