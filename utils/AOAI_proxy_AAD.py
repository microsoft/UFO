"""
usage: AOAI_proxy.py [-h] [--verbose] [--host HOST] [--port PORT]

options:
  -h, --help   show this help message and exit
  --verbose    Enable verbose logging
  --host HOST  Host IP to bind to (default: 0.0.0.0)
  --port PORT  Port to listen on (default: 8000)
  
"""

from azure.identity import AzureCliCredential, get_bearer_token_provider
from openai import AzureOpenAI, APITimeoutError, APIConnectionError, BadRequestError, AuthenticationError, PermissionDeniedError, RateLimitError, APIError
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Union
import argparse
import logging

# Set up logging
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI()

# Initialize Azure OpenAI client
credential = AzureCliCredential()

# Get the token provider
token_provider = get_bearer_token_provider(credential, "https://cognitiveservices.azure.com/.default")

# Initialize the Azure OpenAI client
client = AzureOpenAI(
    max_retries=3,
    timeout=60,
    api_version="2025-01-01-preview", # your API version
    azure_endpoint="https://{your-resource-name}.openai.azure.com/",
    azure_ad_token_provider=token_provider
)

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
    try:
        # Add detailed request debugging
        #logger.debug("=== Received Request Details ===")
        #logger.debug(f"Request model: {request.model}")
        #logger.debug(f"Request messages: {request.messages}")
        #logger.debug(f"Request parameters: n={request.n}, temp={request.temperature}, max_tokens={request.max_tokens}, top_p={request.top_p}, stream={request.stream}")

        response = client.chat.completions.create(
            model=request.model,
            messages=request.messages,
            n=request.n,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            top_p=request.top_p,
            stream=request.stream
        )

        #logger.debug("=== Response Details ===")
        #logger.debug(f"Response raw: {response}")
        #logger.debug(f"Response choices: {response.choices}")


        return response

    except APITimeoutError as e:
        logger.error(f"Timeout error occurred: {str(e)}", exc_info=True)
        raise HTTPException(status_code=504, detail=f"AOAIProxy API request timed out: {e}")
    except APIConnectionError as e:
        logger.error(f"Connection error occurred: {str(e)}", exc_info=True)
        raise HTTPException(status_code=503, detail=f"AOAIProxy API request failed to connect: {e}")
    except BadRequestError as e:
        logger.error(f"Bad request error occurred: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail=f"AOAIProxy API request was invalid: {e}")
    except AuthenticationError as e:
        logger.error(f"Authentication error occurred: {str(e)}", exc_info=True)
        raise HTTPException(status_code=401, detail=f"AOAIProxy API request was not authorized: {e}")
    except PermissionDeniedError as e:
        logger.error(f"Permission error occurred: {str(e)}", exc_info=True)
        raise HTTPException(status_code=403, detail=f"AOAIProxy API request was not permitted: {e}")
    except RateLimitError as e:
        logger.error(f"Rate limit error occurred: {str(e)}", exc_info=True)
        raise HTTPException(status_code=429, detail=f"AOAIProxy API request exceeded rate limit: {e}")
    except APIError as e:
        logger.error(f"API error occurred: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"AOAIProxy API returned an API Error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error occurred: {str(e)}", exc_info=True)
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