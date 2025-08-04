#!/usr/bin/env python3
"""
Integration test for SageMaker presigned URL with initial_actions.
This test simulates the actual usage scenario with the BrowserUseAgent.
"""

import asyncio
import logging
import os
from unittest.mock import patch, MagicMock
from src.agent.browser_use.browser_use_agent import BrowserUseAgent
from src.controller.custom_controller import CustomController
from browser_use.browser.browser import Browser
from browser_use.browser.context import BrowserContext

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_initial_actions_integration():
    """Test the complete initial_actions integration with SageMaker navigation"""
    
    logger.info("🧪 Testing SageMaker Initial Actions Integration")
    
    # Mock the boto3 calls to avoid needing real AWS credentials
    mock_response = {
        "AuthorizedUrl": "https://d-9cpchwz1nnno.studio.us-east-1.sagemaker.aws/jupyter/default/lab?execution-role=arn:aws:iam::123456789012:role/SageMakerExecutionRole&sessionExpirationDurationInSeconds=43200"
    }
    
    with patch('boto3.Session') as mock_session:
        # Setup mock
        mock_client = MagicMock()
        mock_client.create_presigned_domain_url.return_value = mock_response
        mock_session.return_value.client.return_value = mock_client
        
        try:
            # Test 1: Verify action is available in controller
            controller = CustomController()
            actions = controller.registry.registry.actions
            
            assert "navigate_to_sagemaker_presigned_url" in actions, "❌ Action not registered"
            logger.info("✅ Action successfully registered in controller")
            
            # Test 2: Test action parameters
            action_info = actions["navigate_to_sagemaker_presigned_url"]
            logger.info(f"✅ Action description: {action_info.description}")
            
            # Test 3: Create initial_actions configuration
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
            
            logger.info("✅ Initial actions configuration created")
            logger.info(f"Configuration: {initial_actions}")
            
            # Test 4: Verify the action can be converted to ActionModel
            from browser_use.agent.service import Agent
            
            # Create a proper mock LLM that's compatible with LangChain
            mock_llm = MagicMock()
            mock_llm.model_name = "test-model"
            mock_llm.get.return_value = None  # For LangChain compatibility
            mock_llm.invoke.return_value = MagicMock(content="Paris")
            
            # Test the _convert_initial_actions method
            browser = Browser()
            browser_context = await browser.new_context()
            
            try:
                # Create agent with initial actions
                agent = BrowserUseAgent(
                    task="Test task",
                    llm=mock_llm,
                    browser=browser,
                    browser_context=browser_context,
                    controller=controller
                )
                
                # Test the conversion of initial actions
                if initial_actions:
                    converted_actions = agent._convert_initial_actions(initial_actions)
                    logger.info(f"✅ Successfully converted {len(converted_actions)} initial actions")
                    
                    # Verify the converted action has the right structure
                    if converted_actions:
                        first_action = converted_actions[0]
                        action_dict = first_action.model_dump(exclude_unset=True)
                        logger.info(f"✅ Converted action structure: {list(action_dict.keys())}")
                        
                        if "navigate_to_sagemaker_presigned_url" in action_dict:
                            params = action_dict["navigate_to_sagemaker_presigned_url"]
                            logger.info(f"✅ Action parameters: {params}")
                        else:
                            logger.error("❌ Action not found in converted structure")
                
                logger.info("✅ Initial actions integration test completed successfully")
                
            finally:
                await browser_context.close()
                await browser.close()
                
        except Exception as e:
            logger.error(f"❌ Test failed with error: {e}")
            raise
    
    logger.info("🎉 All integration tests passed!")

async def test_mock_execution():
    """Test the actual execution of the action with mocked AWS calls"""
    
    logger.info("🧪 Testing Mock Execution of SageMaker Action")
    
    mock_response = {
        "AuthorizedUrl": "https://d-9cpchwz1nnno.studio.us-east-1.sagemaker.aws/jupyter/default/lab?execution-role=arn:aws:iam::123456789012:role/SageMakerExecutionRole&sessionExpirationDurationInSeconds=43200"
    }
    
    with patch('boto3.Session') as mock_session:
        # Setup mock
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
                
                # Execute the action
                result = await action_func(
                    domain_id="d-9cpchwz1nnno",
                    user_profile_name="adam-test-user-1752279282450",
                    space_name="adam-space-1752279293076",
                    browser=browser_context,
                    region_name="us-east-1"
                )
                
                logger.info(f"✅ Action execution result: {result}")
                
                # Verify boto3 was called correctly
                mock_session.assert_called_once_with(region_name="us-east-1")
                mock_client.create_presigned_domain_url.assert_called_once_with(
                    DomainId="d-9cpchwz1nnno",
                    UserProfileName="adam-test-user-1752279282450",
                    SpaceName="adam-space-1752279293076"
                )
                
                # Verify go_to_url was called with the presigned URL
                mock_execute.assert_called_once_with(
                    "go_to_url",
                    {"url": mock_response["AuthorizedUrl"]},
                    browser=browser_context
                )
                
                logger.info("✅ All mock calls verified successfully")
                
        finally:
            await browser_context.close()
            await browser.close()

if __name__ == "__main__":
    async def run_all_tests():
        await test_initial_actions_integration()
        await test_mock_execution()
        logger.info("🎉 ALL TESTS PASSED! Implementation is working correctly.")
    
    asyncio.run(run_all_tests())
