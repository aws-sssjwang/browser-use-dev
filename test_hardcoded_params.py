#!/usr/bin/env python3
"""
Test to verify that hardcoded SageMaker parameters are working correctly.
This test validates that the action uses the specific hardcoded values.
"""

import asyncio
import logging
from unittest.mock import patch, MagicMock
from src.controller.custom_controller import CustomController
from browser_use.browser.browser import Browser

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_hardcoded_parameters():
    """Test that hardcoded parameters are used correctly"""
    
    logger.info("🧪 Testing Hardcoded SageMaker Parameters")
    
    # Expected hardcoded parameters
    expected_params = {
        "DomainId": "d-9cpchwz1nnno",
        "UserProfileName": "adam-test-user-1752279282450",
        "SpaceName": "adam-space-1752279293076"
    }
    
    # Mock response
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
                
                # Execute with ANY parameters (should be ignored due to hardcoding)
                result = await action_func(
                    domain_id="d-ignored",  # This should be ignored
                    user_profile_name="ignored-user",  # This should be ignored
                    space_name="ignored-space",  # This should be ignored
                    browser=browser_context,
                    region_name="us-west-2"  # This should be ignored
                )
                
                logger.info(f"✅ Action execution result: {result}")
                
                # Verify boto3 session was created with hardcoded region
                mock_session.assert_called_once_with(region_name="us-east-1")
                logger.info("✅ Boto3 session created with hardcoded region: us-east-1")
                
                # Verify SageMaker client was called with hardcoded parameters
                mock_client.create_presigned_domain_url.assert_called_once_with(**expected_params)
                logger.info("✅ SageMaker client called with hardcoded parameters:")
                logger.info(f"   DomainId: {expected_params['DomainId']}")
                logger.info(f"   UserProfileName: {expected_params['UserProfileName']}")
                logger.info(f"   SpaceName: {expected_params['SpaceName']}")
                
                # Verify navigation was called with generated URL
                mock_execute.assert_called_once_with(
                    "go_to_url",
                    {"url": mock_response["AuthorizedUrl"]},
                    browser=browser_context
                )
                logger.info(f"✅ Navigation called with URL: {mock_response['AuthorizedUrl']}")
                
                return True
                
        finally:
            await browser_context.close()
            await browser.close()

async def test_initial_actions_format():
    """Test the correct initial_actions format for hardcoded parameters"""
    
    logger.info("🧪 Testing Initial Actions Format for Hardcoded Parameters")
    
    # Since parameters are hardcoded, the initial_actions can use any values
    # but the actual execution will use the hardcoded ones
    initial_actions = [
        {
            "navigate_to_sagemaker_presigned_url": {
                "domain_id": "any-value",  # Will be ignored
                "user_profile_name": "any-value",  # Will be ignored
                "space_name": "any-value"  # Will be ignored
            }
        }
    ]
    
    logger.info("✅ Initial actions format (parameters will be ignored):")
    logger.info(f"   {initial_actions}")
    
    logger.info("✅ Actual hardcoded parameters that will be used:")
    logger.info("   DomainId: d-9cpchwz1nnno")
    logger.info("   UserProfileName: adam-test-user-1752279282450")
    logger.info("   SpaceName: adam-space-1752279293076")
    logger.info("   Region: us-east-1")
    
    return True

async def run_tests():
    """Run all hardcoded parameter tests"""
    
    logger.info("🚀 Starting Hardcoded Parameter Tests")
    
    tests = [
        ("Hardcoded Parameters", test_hardcoded_parameters),
        ("Initial Actions Format", test_initial_actions_format),
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
        logger.info("🎉 ALL TESTS PASSED! Hardcoded parameters are working correctly.")
        logger.info("")
        logger.info("📋 Summary:")
        logger.info("✅ Hardcoded DomainId: d-9cpchwz1nnno")
        logger.info("✅ Hardcoded UserProfileName: adam-test-user-1752279282450")
        logger.info("✅ Hardcoded SpaceName: adam-space-1752279293076")
        logger.info("✅ Hardcoded Region: us-east-1")
        logger.info("✅ User-provided parameters are ignored (as intended)")
        logger.info("")
        logger.info("🌐 Ready for testing at: http://dsjpnyogrtasp.cloudfront.net")
        return True
    else:
        logger.error("❌ Some tests failed. Please check the implementation.")
        return False

if __name__ == "__main__":
    success = asyncio.run(run_tests())
    exit(0 if success else 1)
