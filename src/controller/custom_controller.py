import pdb

import pyperclip
from typing import Optional, Type, Callable, Dict, Any, Union, Awaitable, TypeVar
from pydantic import BaseModel
from browser_use.agent.views import ActionResult
from browser_use.browser.context import BrowserContext
from browser_use.controller.service import Controller, DoneAction
from browser_use.controller.registry.service import Registry, RegisteredAction
from main_content_extractor import MainContentExtractor
from browser_use.controller.views import (
    ClickElementAction,
    DoneAction,
    ExtractPageContentAction,
    GoToUrlAction,
    InputTextAction,
    OpenTabAction,
    ScrollAction,
    SearchGoogleAction,
    SendKeysAction,
    SwitchTabAction,
)
import logging
import inspect
import asyncio
import os
from langchain_core.language_models.chat_models import BaseChatModel
from browser_use.agent.views import ActionModel, ActionResult

from src.utils.mcp_client import create_tool_param_model, setup_mcp_client_and_tools

from browser_use.utils import time_execution_sync

logger = logging.getLogger(__name__)

Context = TypeVar('Context')


class CustomController(Controller):
    def __init__(self, exclude_actions: list[str] = [],
                 output_model: Optional[Type[BaseModel]] = None,
                 ask_assistant_callback: Optional[Union[Callable[[str, BrowserContext], Dict[str, Any]], Callable[
                     [str, BrowserContext], Awaitable[Dict[str, Any]]]]] = None,
                 ):
        super().__init__(exclude_actions=exclude_actions, output_model=output_model)
        self._register_custom_actions()
        self.ask_assistant_callback = ask_assistant_callback
        self.mcp_client = None
        self.mcp_server_config = None

    def _register_custom_actions(self):
        """Register all custom browser actions"""

        @self.registry.action(
            "Navigate to SageMaker presigned URL. This action generates a fresh presigned URL using boto3 and "
            "navigates directly to it. Use this for accessing SageMaker Studio domains that require presigned URLs."
        )
        async def navigate_to_sagemaker_presigned_url(
            domain_id: str, 
            user_profile_name: str, 
            space_name: str, 
            browser: BrowserContext,
            region_name: str = "us-east-1"
        ):
            try:
                import boto3
                import requests
                import time
                
                logger.info("🚀 SIMPLIFIED SageMaker Navigation - Debug Version")
                logger.info(f"📋 Hardcoded parameters: DomainId=d-9cpchwz1nnno, UserProfile=adam-test-user-1752279282450, Space=adam-space-1752279293076")
                
                # Step 1: Create AWS session with retry
                session = None
                sagemaker_client = None
                for attempt in range(3):
                    try:
                        logger.info(f"🔄 AWS session attempt {attempt + 1}/3...")
                        session = boto3.Session(region_name="us-east-1")
                        sagemaker_client = session.client("sagemaker")
                        logger.info("✅ AWS session and SageMaker client created successfully")
                        break
                    except Exception as aws_error:
                        logger.warning(f"⚠️ AWS session attempt {attempt + 1} failed: {str(aws_error)}")
                        if attempt == 2:
                            error_msg = f"❌ Failed to create AWS session after 3 attempts: {str(aws_error)}"
                            logger.error(error_msg)
                            return ActionResult(error=error_msg)
                        await asyncio.sleep(2)
                
                # Step 2: Generate presigned URL with retry
                presigned_url = None
                if sagemaker_client:
                    for attempt in range(3):
                        try:
                            logger.info(f"🔄 Presigned URL generation attempt {attempt + 1}/3...")
                            response = sagemaker_client.create_presigned_domain_url(
                                DomainId="d-9cpchwz1nnno",
                                UserProfileName="adam-test-user-1752279282450",
                                SpaceName="adam-space-1752279293076"
                            )
                            
                            presigned_url = response["AuthorizedUrl"]
                            logger.info(f"✅ Generated presigned URL successfully (length: {len(presigned_url)} chars)")
                            logger.info(f"🔗 URL preview: {presigned_url[:100]}...")
                            break
                            
                        except Exception as boto_error:
                            logger.warning(f"⚠️ Presigned URL attempt {attempt + 1} failed: {str(boto_error)}")
                            if attempt == 2:
                                error_msg = f"❌ Failed to generate presigned URL after 3 attempts: {str(boto_error)}"
                                logger.error(error_msg)
                                return ActionResult(error=error_msg)
                            await asyncio.sleep(2)
                
                if not presigned_url:
                    error_msg = "❌ Failed to generate presigned URL - no URL obtained"
                    logger.error(error_msg)
                    return ActionResult(error=error_msg)
                
                # Step 3: Pre-validate URL accessibility
                if presigned_url:
                    logger.info("🔍 Pre-validating URL accessibility...")
                    try:
                        response = requests.head(presigned_url, timeout=30, allow_redirects=True)
                        logger.info(f"✅ URL pre-validation successful: HTTP {response.status_code}")
                    except Exception as pre_error:
                        logger.warning(f"⚠️ URL pre-validation failed: {str(pre_error)}")
                        # Continue anyway, as this might be expected
                
                # Step 4: Simple and fast navigation
                try:
                    logger.info("🌐 Executing navigation to SageMaker Studio...")
                    
                    # 直接使用浏览器的导航方法
                    page = await browser.get_current_page()
                    await page.goto(presigned_url, wait_until="domcontentloaded", timeout=60000)
                    logger.info("✅ Navigation command executed successfully")
                    
                    # Short wait for initial page load
                    logger.info("⏳ Waiting for SageMaker Studio to load (15 seconds)...")
                    await asyncio.sleep(15)
                    
                    # Success! SageMaker Studio should now be accessible
                    msg = f"🎉 SUCCESS: SageMaker Studio navigation completed successfully"
                    logger.info(msg)
                    logger.info("📍 SageMaker Studio should now be loaded and ready to use")
                    logger.info("🔗 The JupyterLab environment should be available for your tasks")
                    
                    return ActionResult(extracted_content=msg, include_in_memory=True)
                    
                except Exception as nav_error:
                    error_msg = f"❌ Navigation failed: {str(nav_error)}"
                    logger.error(error_msg)
                    logger.error(f"🔍 Error type: {type(nav_error).__name__}")
                    return ActionResult(error=error_msg)
                    
            except Exception as e:
                error_msg = f"❌ CRITICAL ERROR in ultimate SageMaker navigation: {str(e)}"
                logger.error(error_msg)
                logger.error(f"🔍 Error type: {type(e).__name__}")
                return ActionResult(error=error_msg)

        @self.registry.action(
            "When executing tasks, prioritize autonomous completion. However, if you encounter a definitive blocker "
            "that prevents you from proceeding independently – such as needing credentials you don't possess, "
            "requiring subjective human judgment, needing a physical action performed, encountering complex CAPTCHAs, "
            "or facing limitations in your capabilities – you must request human assistance."
        )
        async def ask_for_assistant(query: str, browser: BrowserContext):
            if self.ask_assistant_callback:
                if inspect.iscoroutinefunction(self.ask_assistant_callback):
                    user_response = await self.ask_assistant_callback(query, browser)
                else:
                    user_response = self.ask_assistant_callback(query, browser)
                msg = f"AI ask: {query}. User response: {user_response['response']}"
                logger.info(msg)
                return ActionResult(extracted_content=msg, include_in_memory=True)
            else:
                return ActionResult(extracted_content="Human cannot help you. Please try another way.",
                                    include_in_memory=True)

        @self.registry.action(
            'Upload file to interactive element with file path ',
        )
        async def upload_file(index: int, path: str, browser: BrowserContext, available_file_paths: list[str]):
            if path not in available_file_paths:
                return ActionResult(error=f'File path {path} is not available')

            if not os.path.exists(path):
                return ActionResult(error=f'File {path} does not exist')

            dom_el = await browser.get_dom_element_by_index(index)

            file_upload_dom_el = dom_el.get_file_upload_element()

            if file_upload_dom_el is None:
                msg = f'No file upload element found at index {index}'
                logger.info(msg)
                return ActionResult(error=msg)

            file_upload_el = await browser.get_locate_element(file_upload_dom_el)

            if file_upload_el is None:
                msg = f'No file upload element found at index {index}'
                logger.info(msg)
                return ActionResult(error=msg)

            try:
                await file_upload_el.set_input_files(path)
                msg = f'Successfully uploaded file to index {index}'
                logger.info(msg)
                return ActionResult(extracted_content=msg, include_in_memory=True)
            except Exception as e:
                msg = f'Failed to upload file to index {index}: {str(e)}'
                logger.info(msg)
                return ActionResult(error=msg)

    @time_execution_sync('--act')
    async def act(
            self,
            action: ActionModel,
            browser_context: Optional[BrowserContext] = None,
            #
            page_extraction_llm: Optional[BaseChatModel] = None,
            sensitive_data: Optional[Dict[str, str]] = None,
            available_file_paths: Optional[list[str]] = None,
            #
            context: Context | None = None,
    ) -> ActionResult:
        """Execute an action"""

        try:
            for action_name, params in action.model_dump(exclude_unset=True).items():
                if params is not None:
                    if action_name.startswith("mcp"):
                        # this is a mcp tool
                        logger.debug(f"Invoke MCP tool: {action_name}")
                        mcp_tool = self.registry.registry.actions.get(action_name).function
                        result = await mcp_tool.ainvoke(params)
                    else:
                        result = await self.registry.execute_action(
                            action_name,
                            params,
                            browser=browser_context,
                            page_extraction_llm=page_extraction_llm,
                            sensitive_data=sensitive_data,
                            available_file_paths=available_file_paths,
                            context=context,
                        )

                    if isinstance(result, str):
                        return ActionResult(extracted_content=result)
                    elif isinstance(result, ActionResult):
                        return result
                    elif result is None:
                        return ActionResult()
                    else:
                        raise ValueError(f'Invalid action result type: {type(result)} of {result}')
            return ActionResult()
        except Exception as e:
            raise e

    async def setup_mcp_client(self, mcp_server_config: Optional[Dict[str, Any]] = None):
        self.mcp_server_config = mcp_server_config
        if self.mcp_server_config:
            self.mcp_client = await setup_mcp_client_and_tools(self.mcp_server_config)
            self.register_mcp_tools()

    def register_mcp_tools(self):
        """
        Register the MCP tools used by this controller.
        """
        if self.mcp_client:
            for server_name in self.mcp_client.server_name_to_tools:
                for tool in self.mcp_client.server_name_to_tools[server_name]:
                    tool_name = f"mcp.{server_name}.{tool.name}"
                    self.registry.registry.actions[tool_name] = RegisteredAction(
                        name=tool_name,
                        description=tool.description,
                        function=tool,
                        param_model=create_tool_param_model(tool),
                    )
                    logger.info(f"Add mcp tool: {tool_name}")
                logger.debug(
                    f"Registered {len(self.mcp_client.server_name_to_tools[server_name])} mcp tools for {server_name}")
        else:
            logger.warning(f"MCP client not started.")

    async def close_mcp_client(self):
        if self.mcp_client:
            await self.mcp_client.__aexit__(None, None, None)
