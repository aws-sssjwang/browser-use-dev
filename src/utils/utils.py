import base64
import os
import time
from pathlib import Path
from typing import Dict, Optional
import requests
import boto3

from langchain_anthropic import ChatAnthropic
from langchain_mistralai import ChatMistralAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from langchain_openai import AzureChatOpenAI, ChatOpenAI
from langchain_aws import ChatBedrock
import gradio as gr


model_names = {
    "openai": ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
    "anthropic": ["claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022", "claude-3-opus-20240229"],
    "ollama": ["qwen2.5:7b", "llama3.2:3b", "deepseek-r1:14b", "deepseek-r1:32b"],
    "deepseek": ["deepseek-chat", "deepseek-reasoner"],
    "google": ["Google"],
    "alibaba": ["Alibaba"],
    "moonshot": ["MoonShot"],
    "bedrock": ["anthropic.claude-3-5-sonnet-20241022-v2:0"]
}

def get_llm_model(provider: str, **kwargs):
    """
    Get LLM model based on provider
    """
    if provider == "bedrock":
        region = kwargs.get("region", "") or os.getenv("AWS_BEDROCK_REGION", "us-west-2")
        
        session = boto3.Session(region_name=region)
        bedrock_runtime = session.client(
            service_name="bedrock-runtime",
            region_name=region,
        )
        
        model_id = kwargs.get("model_name", "anthropic.claude-3-5-sonnet-20241022-v2:0")
        
        return ChatBedrock(
            client=bedrock_runtime,
            model=model_id,
        )
    else:
        raise ValueError(f"Unsupported provider: {provider}")


def encode_image(img_path):
    if not img_path:
        return None
    with open(img_path, "rb") as fin:
        image_data = base64.b64encode(fin.read()).decode("utf-8")
    return image_data


def get_latest_files(directory: str, file_types: list = ['.webm', '.zip']) -> Dict[str, Optional[str]]:
    """Get the latest recording and trace files"""
    latest_files: Dict[str, Optional[str]] = {ext: None for ext in file_types}

    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
        return latest_files

    for file_type in file_types:
        try:
            matches = list(Path(directory).rglob(f"*{file_type}"))
            if matches:
                latest = max(matches, key=lambda p: p.stat().st_mtime)
                # Only return files that are complete (not being written)
                if time.time() - latest.stat().st_mtime > 1.0:
                    latest_files[file_type] = str(latest)
        except Exception as e:
            print(f"Error getting latest {file_type} file: {e}")

    return latest_files
