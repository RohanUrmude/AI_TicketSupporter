"""
Hugging Face OpenAI-Compatible API Client Utility.

Centralizes all communication with Hugging Face TGI Router endpoint.
Uses OpenAI-compatible interface with robust error handling, timeouts, and proxies.
"""
import os
import logging
from typing import Tuple, Optional, Any
import httpx
from openai import OpenAI, APIError, APIConnectionError, APITimeoutError, RateLimitError
from utils.exceptions import (
    HuggingFaceAPIError,
    APITimeoutError as CustomTimeoutError,
    APIConnectionError as CustomConnectionError,
    ProcessingError,
)

logger = logging.getLogger(__name__)

# --- Configuration ---
BASE_URL = os.getenv("HF_API_BASE_URL", "https://router.huggingface.co/v1")
HF_API_TOKEN = os.getenv("HF_API_TOKEN")
LLM_MODEL = os.getenv("LLM_MODEL", "meta-llama/Llama-3.1-8B-Instruct")

if not HF_API_TOKEN:
    raise ValueError("Hugging Face API token not found. Please set HF_API_TOKEN.")

# --- HTTP Client Configuration ---
http_proxy = os.getenv("HTTP_PROXY")
https_proxy = os.getenv("HTTPS_PROXY")
proxies = {"http://": http_proxy, "https://": https_proxy} if http_proxy or https_proxy else None

http_client = httpx.Client(
    proxy=proxies,
    timeout=30.0,
    limits=httpx.Limits(max_connections=100, max_keepalive_connections=20)
)

# --- OpenAI Client ---
client = OpenAI(
    base_url=BASE_URL,
    api_key=HF_API_TOKEN,
    http_client=http_client
)


def query_chat_model(
    messages: list,
    model_name: str,
    is_json: bool = False
) -> Tuple[Optional[str], Optional[dict]]:
    """
    Query a chat model via Hugging Face API.

    Args:
        messages: List of message dicts with 'role' and 'content'
        model_name: Model identifier (e.g., "meta-llama/Llama-3.1-8B-Instruct")
        is_json: Enable JSON mode for structured output

    Returns:
        Tuple of (response_content, error_dict) - one will be None

    Raises:
        HuggingFaceAPIError: API error with retryable flag set
        ProcessingError: Processing failed, not retryable
    """
    try:
        logger.info(f"Querying {model_name}", extra={"model": model_name})

        completion = client.chat.completions.create(
            model=model_name,
            messages=messages,
            response_format={"type": "json_object"} if is_json else None,
            timeout=30.0,
        )

        response_text = completion.choices[0].message.content
        logger.info(f"Model response received", extra={"model": model_name})
        return response_text, None

    except APITimeoutError as err:
        logger.error(f"HF API timeout: {err}")
        raise CustomTimeoutError(
            message="Hugging Face API request timed out",
            details={"model": model_name, "cause": str(err)}
        )

    except RateLimitError as err:
        logger.warning(f"HF API rate limited: {err}")
        raise HuggingFaceAPIError(
            message="Hugging Face API rate limit exceeded",
            status_code=429,
            retryable=True,
            details={"model": model_name}
        )

    except APIConnectionError as err:
        logger.error(f"HF API connection error: {err}")
        raise CustomConnectionError(
            message="Failed to connect to Hugging Face API",
            details={"model": model_name, "cause": str(err)}
        )

    except APIError as err:
        logger.error(f"HF API error: {err}", exc_info=True)

        # Determine if error is retryable based on status code
        status_code = getattr(err, "status_code", None)
        retryable = status_code and 500 <= status_code < 600

        raise HuggingFaceAPIError(
            message=f"Hugging Face API error: {str(err)}",
            status_code=status_code,
            retryable=retryable,
            details={"model": model_name}
        )

    except Exception as err:
        logger.exception(f"Unexpected error querying model {model_name}")
        raise ProcessingError(
            message="Unexpected error during model processing",
            retryable=False,
            details={"model": model_name, "error_type": type(err).__name__}
        )