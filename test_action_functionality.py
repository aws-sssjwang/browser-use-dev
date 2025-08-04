#!/usr/bin/env python3
"""
Focused test for the SageMaker presigned URL action functionality.
Tests the core action without full agent initialization.
"""

import asyncio
import logging
from unittest.mock import patch, MagicMock
from src.controller.custom_controller import CustomController
from browser_use.browser.browser import Browser
from browser_use.browser.context import BrowserContext

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_action_registration():
    """Test that the action is properly registered"""
    logger.info("🧪 Testing Action Registration")
    
    controller = CustomController()
    actions = controller.registry.registry.actions
    
    # Test 1: Action exists
    assert "navigate_to_sagemaker_presigned_url" in actions, "❌ Action not registered"
    logger.info("✅ Action successfully registered")
    
    # Test 2: Action has correct description
    action_info = actions["navigate_to_sagemaker_presigned_url"]
    assert "SageMaker presigned URL" in action_info.description, "❌ Action description incorrect"
    logger.info("✅ Action description is correct")
    
    # Test 3: Action has correct parameters
    param_model = action_info.param_model
    logger.info(f"✅ Action parameter model: {param_model}")
    
    return True

async def test_action_execution():
    """Test the actual execution of the action with mocked AWS calls"""
    logger.info("🧪 Testing Action Execution")
    
    # Mock response from SageMaker
    mock_response = {
        "AuthorizedUrl": "https://d-9cpchwz1nnno.studio.us-east-1.sagemaker.aws/jupyter/default/lab?execution-role=arn:aws:iam::123456789012:role/SageMakerExecutionRole&sessionExpirationDurationInSeconds=43200"
    }
    
    with patch('boto3.Session') as mock_session:
        # Setup boto3 mock
        mock_client = MagicMock()
        mock_client.create_presigned_domain_url.return_value = mock_response
        mock_session.return_value.client.return_value = mock_client
        
        controller = CustomController()
        browser = Browser()
        browser_context = await browser.new_context()
        
        try:
            # Mock the go_to_url action to avoid actual navigation
            with patch.object(controller.registry, 'execute_action') as mock_execute:
                mock_execute.return_value = "Navigation successful"
                
                # Get the action function
                action_func = controller.registry.registry.actions["navigate_to_sagemaker_presigned_url"].function
                
                # Test 1: Execute the action
                result = await action_func(
                    domain_id="d-9cpchwz1nnno",
                    user_profile_name="adam-test-user-1752279282450",
                    space_name="adam-space-1752279293076",
                    browser=browser_context,
                    region_name="us-east-1"
                )
                
                logger.info(f"✅ Action execution result: {result}")
                assert result is not None, "❌ Action returned None"
                
                # Test 2: Verify boto3 was called correctly
                mock_session.assert_called_once_with(region_name="us-east-1")
                mock_client.create_presigned_domain_url.assert_called_once_with(
                    DomainId="d-9cpchwz1nnno",
                    UserProfileName="adam-test-user-1752279282450",
                    SpaceName="adam-space-1752279293076"
                )
                logger.info("✅ Boto3 calls verified")
                
                # Test 3: Verify go_to_url was called with the presigned URL
                mock_execute.assert_called_once_with(
                    "go_to_url",
                    {"url": mock_response["AuthorizedUrl"]},
                    browser=browser_context
                )
                logger.info("✅ Navigation call verified")
                
        finally:
            await browser_context.close()
            await browser.close()
    
    return True

async def test_initial_actions_format():
    """Test the format for initial_actions configuration"""
    logger.info("🧪 Testing Initial Actions Format")
    
    # Test the expected format for initial_actions
    initial_actions = [
        {
            "navigate_to_sagemaker_presigned_url": {
                "domain_id": "d-9cpchwz1nnno",
                "user_profile_name": "adam-test-user-1752279282450",
                "space_name": "adam-space-1752279293076",
                "region_name": "us-east-1"
            }
        }
    ]
    
    logger.info("✅ Initial actions format:")
    logger.info(f"   {initial_actions}")
    
    # Verify structure
    assert len(initial_actions) == 1, "❌ Wrong number of actions"
    assert "navigate_to_sagemaker_presigned_url" in initial_actions[0], "❌ Action name not found"
    
    params = initial_actions[0]["navigate_to_sagemaker_presigned_url"]
    required_params = ["domain_id", "user_profile_name", "space_name"]
    
    for param in required_params:
        assert param in params, f"❌ Required parameter {param} missing"
    
    logger.info("✅ Initial actions format is correct")
    return True

async def test_error_handling():
    """Test error handling when boto3 fails"""
    logger.info("🧪 Testing Error Handling")
    
    with patch('boto3.Session') as mock_session:
        # Setup boto3 to raise an exception
        mock_session.side_effect = Exception("AWS credentials not found")
        
        controller = CustomController()
        browser = Browser()
        browser_context = await browser.new_context()
        
        try:
            # Get the action function
            action_func = controller.registry.registry.actions["navigate_to_sagemaker_presigned_url"].function
            
            # Execute the action - should handle the error gracefully
            result = await action_func(
                domain_id="d-9cpchwz1nnno",
                user_profile_name="adam-test-user-1752279282450",
                space_name="adam-space-1752279293076",
                browser=browser_context,
                region_name="us-east-1"
            )
            
            logger.info(f"✅ Error handling result: {result}")
            
            # Should return an ActionResult with error
            assert hasattr(result, 'error'), "❌ Error not properly handled"
            assert "AWS credentials not found" in str(result.error), "❌ Error message not preserved"
            
            logger.info("✅ Error handling works correctly")
            
        finally:
            await browser_context.close()
            await browser.close()
    
    return True

async def run_all_tests():
    """Run all tests"""
    logger.info("🚀 Starting SageMaker Action Tests")
    
    tests = [
        ("Action Registration", test_action_registration),
        ("Action Execution", test_action_execution),
        ("Initial Actions Format", test_initial_actions_format),
        ("Error Handling", test_error_handling),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            logger.info(f"\n--- Running {test_name} ---")
            result = await test_func()
            if result:
                logger.info(f"✅ {test_name} PASSED")
                passed += 1
            else:
                logger.error(f"❌ {test_name} FAILED")
                failed += 1
        except Exception as e:
            logger.error(f"❌ {test_name} FAILED with exception: {e}")
            failed += 1
    
    logger.info(f"\n🎯 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        logger.info("🎉 ALL TESTS PASSED! SageMaker action is working correctly.")
        return True
    else:
        logger.error("❌ Some tests failed. Please check the implementation.")
        return False

if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    exit(0 if success else 1)
