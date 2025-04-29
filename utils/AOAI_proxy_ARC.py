"""
usage: AOAI_proxy.py [-h] [--verbose] [--host HOST] [--port PORT]

options:
  -h, --help   show this help message and exit
  --verbose    Enable verbose logging
  --host HOST  Host IP to bind to (default: 0.0.0.0)
  --port PORT  Port to listen on (default: 8000)
  
"""

from azure.identity import ManagedIdentityCredential
from openai import AzureOpenAI, APITimeoutError, APIConnectionError, BadRequestError, AuthenticationError, PermissionDeniedError, RateLimitError, APIError
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Union
import argparse
import logging
import time
from datetime import datetime

# Set up logging
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI()

# Azure OpenAI Settings
AZURE_ENDPOINT = "https://{your-resource-name}.openai.azure.com"
API_VERSION = "2025-01-01-preview" # your API version
AZURE_SCOPE = "https://cognitiveservices.azure.com/.default"

# Token caching
cached_token = None
token_expiry = 0
TOKEN_REFRESH_THRESHOLD = 300  # Refresh token 5 minutes before expiry

# Initialize Managed Identity Credential
try:
    logger.debug("Initializing ManagedIdentityCredential")
    credential = ManagedIdentityCredential()
    logger.info("ManagedIdentityCredential initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize ManagedIdentityCredential: {e}")
    raise

def get_token():
    global cached_token, token_expiry
    
    current_time = time.time()
    
    # Return cached token if it's still valid (with buffer)
    if cached_token and current_time < (token_expiry - TOKEN_REFRESH_THRESHOLD):
        logger.debug("Using cached token")
        return cached_token
    
    try:
        logger.debug("Getting new token from managed identity")
        token_result = credential.get_token(AZURE_SCOPE)
        cached_token = token_result.token
        token_expiry = current_time + token_result.expires_on
        logger.info("New token obtained successfully")
        return cached_token
    except Exception as e:
        logger.error(f"Failed to get token: {e}")
        raise

# Initialize the Azure OpenAI client
try:
    logger.debug("Initializing Azure OpenAI client")
    client = AzureOpenAI(
        max_retries=3,
        timeout=60,
        api_version=API_VERSION,
        azure_endpoint=AZURE_ENDPOINT,
        azure_ad_token_provider=get_token
    )
    logger.info("Azure OpenAI client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Azure OpenAI client: {e}")
    raise

# Define request models
class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[dict[str, Union[str, list]]]
    n: int = 1
    temperature: float = 1.0
    max_tokens: int | None = None
    top_p: float = 1.0
    stream: bool = False

@app.post("/chat/completions")
async def chat_completion(request: ChatCompletionRequest):
    request_start_time = time.time()
    request_id = datetime.now().strftime("%Y%m%d%H%M%S%f")
    
    try:
        # Log request received
        logger.debug(f"[{request_id}] === API Request Received ===")
        #logger.debug(f"[{request_id}] Request model: {request.model}")
        #logger.debug(f"[{request_id}] Request messages: {request.messages}")
        #logger.debug(f"[{request_id}] Request parameters: n={request.n}, temp={request.temperature}, max_tokens={request.max_tokens}, top_p={request.top_p}, stream={request.stream}")

        # Log chat completion start
        logger.debug(f"[{request_id}] Sending chat completion request to Azure OpenAI...")
        chat_start_time = time.time()

        response = client.chat.completions.create(
            model=request.model,
            messages=request.messages,
            n=request.n,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            top_p=request.top_p,
            stream=request.stream
        )

        # Log chat completion response
        chat_duration = time.time() - chat_start_time
        logger.debug(f"[{request_id}] Chat completion response received in {chat_duration:.2f} seconds")
        #logger.debug(f"[{request_id}] Response choices: {response.choices}")

        # Log overall request completion
        total_duration = time.time() - request_start_time
        logger.debug(f"[{request_id}] === API Request Completed ===")
        logger.debug(f"[{request_id}] Total request duration: {total_duration:.2f} seconds")
        logger.debug(f"[{request_id}] Chat completion duration: {chat_duration:.2f} seconds")
        logger.debug(f"[{request_id}] Overhead duration: {total_duration - chat_duration:.2f} seconds")

        return response

    except APITimeoutError as e:
        logger.error(f"[{request_id}] Timeout error occurred: {str(e)}", exc_info=True)
        raise HTTPException(status_code=504, detail=f"AOAIProxy API request timed out: {e}")
    except APIConnectionError as e:
        logger.error(f"[{request_id}] Connection error occurred: {str(e)}", exc_info=True)
        raise HTTPException(status_code=503, detail=f"AOAIProxy API request failed to connect: {e}")
    except BadRequestError as e:
        logger.error(f"[{request_id}] Bad request error occurred: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=f"AOAIProxy API request was invalid: {e}")
    except AuthenticationError as e:
        logger.error(f"[{request_id}] Authentication error occurred: {str(e)}", exc_info=True)
        raise HTTPException(status_code=401, detail=f"AOAIProxy API request was not authorized: {e}")
    except PermissionDeniedError as e:
        logger.error(f"[{request_id}] Permission error occurred: {str(e)}", exc_info=True)
        raise HTTPException(status_code=403, detail=f"AOAIProxy API request was not permitted: {e}")
    except RateLimitError as e:
        logger.error(f"[{request_id}] Rate limit error occurred: {str(e)}", exc_info=True)
        raise HTTPException(status_code=429, detail=f"AOAIProxy API request exceeded rate limit: {e}")
    except APIError as e:
        logger.error(f"[{request_id}] API error occurred: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"AOAIProxy API returned an API Error: {e}")
    except Exception as e:
        logger.error(f"[{request_id}] Unexpected error occurred: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # Add command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument("--host", default="0.0.0.0", help="Host IP to bind to (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on (default: 8000)")
    args = parser.parse_args()

    # Set logging level based on verbose flag
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")
    else:
        logger.setLevel(logging.WARNING)

    import uvicorn
    logger.debug(f"Starting server on {args.host}:{args.port}")
    uvicorn.run(app, host=args.host, port=args.port)