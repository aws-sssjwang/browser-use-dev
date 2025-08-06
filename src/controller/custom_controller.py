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
                
                # Step 3: Create short URL using shortener service to avoid token consumption
                short_url = presigned_url  # fallback
                try:
                    logger.info("🔗 Creating short URL to avoid token consumption...")
                    logger.info(f"📏 Original presigned URL length: {len(presigned_url)} chars")
                    
                    # Call local shortener API (same container)
                    SHORTEN_ENDPOINT = os.getenv("SHORTENER_API", "http://127.0.0.1:8799/api/shorten")
                    PRESIGN_TTL = int(os.getenv("PRESIGN_TTL", "3600"))
                    
                    response = requests.post(
                        SHORTEN_ENDPOINT,
                        json={"long_url": presigned_url, "expires_in": PRESIGN_TTL},
                        timeout=5
                    )
                    
                    if response.status_code == 200:
                        short_url = response.json()["short_url"]
                        logger.info(f"📏 Short URL length: {len(short_url)} chars")
                        logger.info(f"🔗 Short URL: {short_url}")
                        logger.info(f"✅ Short URL creation successful - reduced from {len(presigned_url)} to {len(short_url)} chars")
                    else:
                        logger.warning(f"⚠️ Short URL creation failed: HTTP {response.status_code}")
                        logger.info("🔄 Will use original presigned URL as fallback")
                        short_url = presigned_url
                    
                except Exception as shorten_error:
                    logger.warning(f"⚠️ Short URL creation failed: {str(shorten_error)}")
                    logger.info("🔄 Will use original presigned URL as fallback")
                    short_url = presigned_url
                
                # Step 4: Enhanced navigation using the short URL (pure 302 redirect, no token consumption)
                try:
                    logger.info("🌐 Executing enhanced navigation to SageMaker Studio...")
                    
                    # Get current page and navigate with improved parameters
                    page = await browser.get_current_page()
                    
                    # Navigate using the short URL with extended timeout
                    logger.info("🔄 Starting navigation with short URL (5 minutes timeout)...")
                    await page.goto(short_url, wait_until="networkidle", timeout=300000)
                    logger.info("✅ Initial navigation completed successfully")
                    
                    # Extract and verify base URL after navigation
                    logger.info("🔍 Extracting base URL after navigation...")
                    initial_url = page.url
                    logger.info(f"📍 Initial URL after navigation: {initial_url}")
                    
                    # Wait for URL to stabilize (handle any remaining redirects)
                    logger.info("⏳ Waiting for URL to stabilize...")
                    stable_url = None
                    for attempt in range(10):  # Maximum 10 attempts
                        current_url = page.url
                        await asyncio.sleep(2)  # Wait 2 seconds
                        next_url = page.url
                        
                        if current_url == next_url:  # URL is stable
                            stable_url = next_url
                            logger.info(f"✅ URL stabilized after {attempt + 1} attempts: {stable_url}")
                            break
                        else:
                            logger.info(f"🔄 URL changed from {current_url} to {next_url}, waiting...")
                    
                    if not stable_url:
                        logger.warning("⚠️ URL did not stabilize after 10 attempts, using current URL")
                        stable_url = page.url
                    
                    # Verify this is a valid SageMaker Studio base URL
                    logger.info("🔍 Verifying base URL format...")
                    if "/jupyterlab/default/lab" in stable_url:
                        logger.info("✅ Valid SageMaker Studio base URL detected")
                        base_url = stable_url
                    elif "studio.us-east-1.sagemaker.aws" in stable_url:
                        logger.info("✅ SageMaker Studio domain detected, URL may still be loading")
                        base_url = stable_url
                    else:
                        logger.warning(f"⚠️ Unexpected URL format: {stable_url}")
                        base_url = stable_url
                    
                    logger.info(f"🎯 Final base URL: {base_url}")
                    
                    # Additional wait for network to be completely idle
                    logger.info("⏳ Waiting for network to be completely idle...")
                    await page.wait_for_load_state("networkidle", timeout=90000)
                    logger.info("✅ Network idle state achieved")
                    
                    # Enhanced page content verification with JupyterLab-specific logic
                    logger.info("🔍 Verifying SageMaker Studio page content...")
                    try:
                        # For JupyterLab, wait for specific elements instead of just body
                        logger.info("🔄 Step 1: Waiting for JupyterLab to initialize...")
                        
                        # Try multiple selectors that indicate JupyterLab is loading
                        jupyterlab_selectors = [
                            'body',  # Basic fallback
                            '#jp-main-dock-panel',  # JupyterLab main panel
                            '.jp-MainAreaWidget',   # JupyterLab main area
                            '.lm-Widget',           # Lumino widget (JupyterLab framework)
                            '[data-jp-theme-light]', # JupyterLab theme container
                            '.jp-NotebookPanel'     # Notebook panel
                        ]
                        
                        element_found = False
                        for selector in jupyterlab_selectors:
                            try:
                                logger.info(f"🔍 Trying selector: {selector}")
                                await page.wait_for_selector(selector, timeout=15000)  # 15 seconds per selector
                                logger.info(f"✅ Found element with selector: {selector}")
                                element_found = True
                                break
                            except Exception as selector_error:
                                logger.info(f"⏭️ Selector {selector} not found, trying next...")
                                continue
                        
                        if element_found:
                            logger.info("✅ Step 1 completed: JupyterLab elements detected")
                        else:
                            logger.warning("⚠️ No JupyterLab elements found, but continuing...")
                        
                        # Get detailed page information
                        logger.info("🔄 Step 2: Getting page information...")
                        try:
                            current_url = page.url
                            page_title = await asyncio.wait_for(page.title(), timeout=10)
                            logger.info(f"📍 Current URL: {current_url}")
                            logger.info(f"📋 Page title: '{page_title}'")
                            logger.info("✅ Step 2 completed: Page information retrieved")
                        except asyncio.TimeoutError:
                            logger.warning("⚠️ Step 2 timeout: Could not get page title within 10 seconds")
                            current_url = page.url
                            page_title = "TIMEOUT"
                            logger.info(f"📍 Current URL: {current_url}")
                        except Exception as info_error:
                            logger.warning(f"⚠️ Step 2 error: {str(info_error)}")
                            current_url = page.url
                            page_title = "ERROR"
                        
                        # Check for JavaScript errors
                        logger.info("🔄 Step 3: Checking console logs...")
                        try:
                            console_logs = []
                            page.on("console", lambda msg: console_logs.append(f"{msg.type}: {msg.text}"))
                            await asyncio.sleep(2)  # Give time for console messages
                            if console_logs:
                                logger.info(f"🖥️ Console messages: {console_logs[-5:]}")  # Last 5 messages
                            logger.info("✅ Step 3 completed: Console logs checked")
                        except Exception as console_error:
                            logger.warning(f"⚠️ Step 3 error: Could not capture console logs: {str(console_error)}")
                        
                        # Get page content and analyze
                        logger.info("🔄 Step 4: Getting page content...")
                        try:
                            page_content = await asyncio.wait_for(page.content(), timeout=15)
                            content_length = len(page_content)
                            logger.info(f"📄 Page content length: {content_length} characters")
                            logger.info("✅ Step 4 completed: Page content retrieved")
                        except asyncio.TimeoutError:
                            logger.error("❌ Step 4 timeout: Could not get page content within 15 seconds")
                            logger.error("🔍 This suggests the page is hanging or taking too long to load")
                            return ActionResult(error="Page content retrieval timeout - page may be hanging")
                        except Exception as content_error:
                            logger.error(f"❌ Step 4 error: {str(content_error)}")
                            return ActionResult(error=f"Page content retrieval failed: {str(content_error)}")
                        
                        # Show first 500 characters of content for debugging
                        content_preview = page_content[:500].replace('\n', ' ').replace('\r', ' ')
                        logger.info(f"📄 Content preview: {content_preview}...")
                        
                        # Check for common error indicators
                        content_lower = page_content.lower()
                        error_indicators = ['error', 'invalid', 'expired', 'forbidden', 'unauthorized', 'not found']
                        found_errors = [error for error in error_indicators if error in content_lower]
                        
                        if found_errors:
                            logger.warning(f"⚠️ Potential error indicators found: {found_errors}")
                        
                        # Check for SageMaker indicators
                        sagemaker_indicators = ['sagemaker', 'jupyter', 'studio', 'notebook', 'jupyterlab']
                        found_indicators = [indicator for indicator in sagemaker_indicators if indicator in content_lower]
                        
                        if found_indicators:
                            logger.info(f"✅ SageMaker Studio content detected: {found_indicators}")
                        else:
                            logger.warning("⚠️ No specific SageMaker indicators found in page content")
                            
                        # Check for specific SageMaker Studio elements
                        try:
                            # Try to find common SageMaker Studio elements
                            studio_elements = [
                                'div[data-jp-theme-light]',
                                '.jp-MainAreaWidget',
                                '#jp-main-dock-panel',
                                '.lm-Widget',
                                '[class*="jupyter"]',
                                '[class*="sagemaker"]'
                            ]
                            
                            found_elements = []
                            for selector in studio_elements:
                                try:
                                    element = await page.query_selector(selector)
                                    if element:
                                        found_elements.append(selector)
                                except:
                                    continue
                            
                            if found_elements:
                                logger.info(f"✅ SageMaker Studio DOM elements found: {found_elements}")
                            else:
                                logger.warning("⚠️ No SageMaker Studio DOM elements found")
                                
                        except Exception as dom_error:
                            logger.warning(f"⚠️ DOM element check failed: {str(dom_error)}")
                        
                        # Check if page is still loading
                        try:
                            ready_state = await page.evaluate("document.readyState")
                            logger.info(f"📄 Document ready state: {ready_state}")
                            
                            if ready_state != "complete":
                                logger.info("⏳ Page still loading, waiting additional time...")
                                await asyncio.sleep(10)
                                ready_state = await page.evaluate("document.readyState")
                                logger.info(f"📄 Document ready state after wait: {ready_state}")
                                
                        except Exception as ready_error:
                            logger.warning(f"⚠️ Could not check document ready state: {str(ready_error)}")
                            
                    except Exception as content_error:
                        logger.error(f"❌ Page content verification failed: {str(content_error)}")
                        logger.error(f"🔍 Error type: {type(content_error).__name__}")
                        
                        # Try to get basic page info even if verification failed
                        try:
                            current_url = page.url
                            page_title = await page.title()
                            logger.info(f"📍 Current URL (fallback): {current_url}")
                            logger.info(f"📋 Page title (fallback): '{page_title}'")
                        except:
                            logger.error("❌ Could not get basic page information")
                        
                        logger.info("🔄 Continuing anyway as basic navigation succeeded")
                    
                    # Final wait for SageMaker Studio to fully initialize
                    logger.info("⏳ Waiting for SageMaker Studio to fully initialize (30 seconds)...")
                    await asyncio.sleep(30)
                    
                    # Final page status check
                    try:
                        current_url = page.url
                        page_title = await page.title()
                        logger.info(f"📍 Final URL: {current_url[:100]}...")
                        logger.info(f"📋 Page title: {page_title}")
                    except Exception as info_error:
                        logger.warning(f"⚠️ Could not get page info: {str(info_error)}")
                    
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
