import os
import time
from dataclasses import dataclass

from dotenv import load_dotenv
from google import genai
from google.genai import errors as genai_errors
from google.genai import types

import config


load_dotenv(config.ROOT / ".env", override=True)

API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    raise RuntimeError(
        "GOOGLE_API_KEY not found. Create a .env at the project root "
        "(copy .env.example) and paste your Google AI Studio key."    
    )

client = genai.Client(api_key=API_KEY)

RETRAYABLE_CODES = {429, 503}
MAX_ATTEMPTS = 3
BACKOFF_SECONDS = (15, 60)

@dataclass
class ModelResponse:
    text: str
    input_tokens: int
    output_tokens: int
    latency_ms: int

def call_model(prompt_text: str, message: str) -> ModelResponse:
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            start = time.perf_counter()
            response = client.models.generate_content(
                model=config.MODEL,
                contents=message,
                config=types.GenerateContentConfig(
                    system_instruction=prompt_text,
                    temperature=config.TEMPERATURE,
                    max_output_tokens=config.MAX_OUTPUT_TOKENS,    
                ),
            )
            break
        except genai_errors.APIError as error:
            if error.code not in RETRAYABLE_CODES or attempt == MAX_ATTEMPTS:
                raise
            if "per day" in str(error).lower():
                raise RuntimeError(
                    "Daily quota exhausted for this model. The pool resets at "
                    "midnight Pacific (~05:00 Brasilia), or switch config.MODEL."    
                ) from error
            wait = BACKOFF_SECONDS[attempt - 1]
            print(f"   API {error.code}, attempt {attempt}/{MAX_ATTEMPTS}, waiting {wait}s...")
            time.sleep(wait)

    latency_ms = round((time.perf_counter() - start) * 1000)

    usage = response.usage_metadata
    return ModelResponse(
        text=response.text or "",
        input_tokens=usage.prompt_token_count or 0,
        output_tokens=usage.candidates_token_count or 0,
        latency_ms=latency_ms
    )