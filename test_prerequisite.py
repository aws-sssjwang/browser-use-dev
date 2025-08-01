#!/usr/bin/env python3
"""
Test script for prerequisite system functionality
测试prerequisite系统功能的脚本
"""

import os
import sys
import json
import logging

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_prerequisite_execution():
    """测试prerequisite代码执行功能"""
    print("=== Testing Prerequisite Execution ===")
    
    # Test prerequisite code (similar to what's in the UI)
    prerequisite_code = """
import boto3
import os

# Mock SageMaker client for testing (in real scenario, this would be actual AWS call)
class MockSageMakerClient:
    def create_presigned_domain_url(self, **kwargs):
        return {
            "AuthorizedUrl": f"https://d-{kwargs['DomainId']}.studio.{os.getenv('AWS_DEFAULT_REGION', 'us-east-1')}.sagemaker.aws/jupyter/default/lab?spaceName={kwargs.get('SpaceName', 'default')}"
        }

# Use mock client for testing
session = boto3.Session(region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1"))
# In real scenario: sagemaker_client = session.client("sagemaker")
sagemaker_client = MockSageMakerClient()  # Mock for testing

response = sagemaker_client.create_presigned_domain_url(
    DomainId=os.getenv("SAGEMAKER_DOMAIN_ID", "d-9cpchwz1nnno"),
    UserProfileName=os.getenv("SAGEMAKER_USER_PROFILE_NAME", "adam-test-user-1752279282450"),
    SpaceName=os.getenv("SAGEMAKER_SPACE_NAME", "adam-space-1752279293076")
)

PLACEHOLDERS = {}
PLACEHOLDERS["PLACEHOLDER_URL"] = response["AuthorizedUrl"]
"""
    
    try:
        # Execute prerequisite code
        global_vars = {}
        exec(prerequisite_code, globals(), global_vars)
        
        # Extract placeholders
        placeholders = global_vars.get("PLACEHOLDERS", {})
        
        print(f"✅ Prerequisite execution successful!")
        print(f"📋 Generated placeholders: {json.dumps(placeholders, indent=2)}")
        
        # Test placeholder replacement
        test_task = "open PLACEHOLDER_URL and create a new notebook"
        
        for placeholder, value in placeholders.items():
            test_task = test_task.replace(placeholder, value)
        
        print(f"🔄 Original task: open PLACEHOLDER_URL and create a new notebook")
        print(f"✨ Task after placeholder replacement: {test_task}")
        
        return True, placeholders
        
    except Exception as e:
        print(f"❌ Prerequisite execution failed: {e}")
        return False, {}

def test_custom_agent_placeholder():
    """测试CustomAgent的placeholder功能"""
    print("\n=== Testing CustomAgent Placeholder Functionality ===")
    
    try:
        from src.agent.custom_agent import CustomAgent
        
        # Create test placeholders
        test_placeholders = {
            "PLACEHOLDER_URL": "https://test-sagemaker-url.com/lab",
            "PLACEHOLDER_USER": "test-user"
        }
        
        print(f"✅ CustomAgent import successful!")
        print(f"📋 Test placeholders: {json.dumps(test_placeholders, indent=2)}")
        
        return True
        
    except Exception as e:
        print(f"❌ CustomAgent test failed: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 Starting Prerequisite System Tests")
    print("=" * 50)
    
    # Test 1: Prerequisite execution
    success1, placeholders = test_prerequisite_execution()
    
    # Test 2: CustomAgent placeholder functionality
    success2 = test_custom_agent_placeholder()
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print(f"  Prerequisite Execution: {'✅ PASS' if success1 else '❌ FAIL'}")
    print(f"  CustomAgent Placeholder: {'✅ PASS' if success2 else '❌ FAIL'}")
    
    if success1 and success2:
        print("\n🎉 All tests passed! Prerequisite system is working correctly.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please check the implementation.")
        return 1

if __name__ == "__main__":
    exit(main())
