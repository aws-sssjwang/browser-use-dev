from __future__ import annotations

import asyncio
import json
import logging
import os
from typing import Optional, Dict, Any

from browser_use.agent.service import Agent
from browser_use.agent.views import AgentOutput
from browser_use.browser.views import BrowserState
from langchain_core.messages import BaseMessage
from json_repair import repair_json

logger = logging.getLogger(__name__)


class CustomAgent(Agent):
    def __init__(
        self,
        *args,
        placeholders: Optional[Dict[str, str]] = None,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        # Make placeholders available to the class
        self.placeholders = placeholders or {}

    async def get_next_action(self, input_messages: list[BaseMessage]) -> AgentOutput:
        """Override to add placeholder replacement and long URL bypass functionality"""
        try:
            # Get the normal LLM response first
            agent_output = await super().get_next_action(input_messages)
            
            # Only apply placeholder replacement if we have placeholders and a valid output
            if not self.placeholders or not agent_output:
                return agent_output
            
            # Convert the agent output to JSON for placeholder replacement
            try:
                output_dict = agent_output.model_dump()
                output_json = json.dumps(output_dict)
                
                # Apply Arka's simple placeholder replacement
                modified = False
                for key, value in self.placeholders.items():
                    if key in output_json:
                        # Check if this is a long URL that might cause issues
                        if len(value) > 1000 and ("http" in value.lower() or "https" in value.lower()):
                            logger.info(f"Processing long URL ({len(value)} chars) for {key}")
                        else:
                            logger.info(f"Replacing placeholder {key} with {value[:100]}{'...' if len(value) > 100 else ''}")
                        
                        output_json = output_json.replace(key, value)
                        modified = True
                
                # Only recreate the object if we actually made changes
                if modified:
                    updated_dict = json.loads(output_json)
                    return AgentOutput(**updated_dict)
                else:
                    return agent_output
                    
            except Exception as e:
                logger.warning(f"Error applying placeholders to agent output: {e}")
                return agent_output
                
        except Exception as e:
            logger.error(f"Error in get_next_action: {e}")
            # If everything fails, try the parent method without any modifications
            return await super().get_next_action(input_messages)
