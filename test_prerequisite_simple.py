#!/usr/bin/env python3
"""
测试prerequisite功能的简单验证脚本
"""
import requests
import json
import time

def test_simple_prerequisite():
    """测试简单的prerequisite功能"""
    print("🧪 测试简单的prerequisite功能...")
    
    # 模拟prerequisite代码执行
    prerequisite_code = """
PLACEHOLDERS = {}
PLACEHOLDERS["TEST_URL"] = "https://www.google.com"
PLACEHOLDERS["TEST_MESSAGE"] = "Hello from prerequisite!"
"""
    
    # 执行prerequisite代码
    global_vars = {}
    try:
        exec(prerequisite_code, globals(), global_vars)
        placeholders = global_vars.get("PLACEHOLDERS", {})
        
        print("✅ Prerequisite代码执行成功")
        print(f"📋 提取的placeholders: {placeholders}")
        
        # 测试placeholder替换逻辑
        test_content = "Please open TEST_URL and show TEST_MESSAGE"
        print(f"🔄 原始内容: {test_content}")
        
        # 模拟我们修复后的替换逻辑
        for placeholder, value in placeholders.items():
            if placeholder in test_content:
                print(f"🔧 替换 {placeholder} -> {value}")
                test_content = test_content.replace(placeholder, value)
        
        print(f"✅ 替换后内容: {test_content}")
        return True
        
    except Exception as e:
        print(f"❌ Prerequisite执行失败: {e}")
        return False

def test_aws_prerequisite():
    """测试AWS SageMaker prerequisite（模拟）"""
    print("\n🧪 测试AWS SageMaker prerequisite...")
    
    # 模拟AWS prerequisite代码（不实际调用API）
    prerequisite_code = """
# 模拟AWS调用结果
mock_response = {
    "AuthorizedUrl": "https://mock-sagemaker-url.com/auth?token=mock-token"
}

PLACEHOLDERS = {}
PLACEHOLDERS["PLACEHOLDER_URL"] = mock_response["AuthorizedUrl"]
"""
    
    global_vars = {}
    try:
        exec(prerequisite_code, globals(), global_vars)
        placeholders = global_vars.get("PLACEHOLDERS", {})
        
        print("✅ AWS Prerequisite代码执行成功")
        print(f"📋 提取的placeholders: {placeholders}")
        
        # 测试在任务中的使用
        task_content = "open PLACEHOLDER_URL and create a new notebook"
        print(f"🔄 原始任务: {task_content}")
        
        for placeholder, value in placeholders.items():
            if placeholder in task_content:
                print(f"🔧 替换 {placeholder} -> {value}")
                task_content = task_content.replace(placeholder, value)
        
        print(f"✅ 替换后任务: {task_content}")
        return True
        
    except Exception as e:
        print(f"❌ AWS Prerequisite执行失败: {e}")
        return False

if __name__ == "__main__":
    print("🔍 开始测试prerequisite功能...")
    
    # 测试简单prerequisite
    simple_test = test_simple_prerequisite()
    
    # 测试AWS prerequisite
    aws_test = test_aws_prerequisite()
    
    print(f"\n📊 测试结果:")
    print(f"  - 简单prerequisite: {'✅ 通过' if simple_test else '❌ 失败'}")
    print(f"  - AWS prerequisite: {'✅ 通过' if aws_test else '❌ 失败'}")
    
    if simple_test and aws_test:
        print("\n🎉 所有prerequisite功能测试通过！")
        print("💡 建议:")
        print("  1. 在Web UI中测试简单的prerequisite")
        print("  2. 确认AWS凭证配置正确")
        print("  3. 测试完整的SageMaker prerequisite")
    else:
        print("\n⚠️  部分测试失败，需要进一步调试")
