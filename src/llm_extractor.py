import json
import logging
import re
from typing import Any, Dict, List
import httpx
from src.config import get_settings
from src.prompt_templates import SYSTEM_EXTRACTION_PROMPT, build_user_prompt
from src.validator import validate_project_data, ProjectDocument

logger = logging.getLogger("docgen.llm")
settings = get_settings()


class LLMInferenceError(Exception):
    """Raised when Ollama inference fails or produces invalid data."""
    pass


class OllamaExtractor:
    """
    Coordinates local LLM inference using Ollama for grounded project documentation extraction.
    """

    def __init__(self, base_url: str = settings.OLLAMA_BASE_URL, model: str = settings.OLLAMA_MODEL):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = float(settings.OLLAMA_TIMEOUT)

    def check_health(self) -> Dict[str, Any]:
        """
        Verifies connectivity with the local Ollama instance and checks available models.
        """
        try:
            with httpx.Client(timeout=1.5) as client:
                res = client.get(f"{self.base_url}/api/tags")
                if res.status_code == 200:
                    models = [m.get("name", "") for m in res.json().get("models", [])]
                    model_found = any(self.model in m for m in models)
                    return {
                        "status": "healthy",
                        "available_models": models,
                        "configured_model": self.model,
                        "model_ready": model_found
                    }
                return {
                    "status": "unhealthy",
                    "error": f"Ollama returned HTTP status {res.status_code}"
                }
        except httpx.ConnectError:
            return {
                "status": "offline",
                "error": f"Could not connect to Ollama at {self.base_url}. Ensure Ollama is running (`ollama serve`)."
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    @staticmethod
    def _clean_json_response(raw_text: str) -> str:
        """
        Strips markdown code fence wrappers (```json ... ```) or conversational preamble.
        """
        cleaned = raw_text.strip()
        # Remove markdown code block if present
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned, re.IGNORECASE)
        if match:
            return match.group(1).strip()

        # If wrapped with curly braces somewhere inside
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1 and end > start:
            return cleaned[start : end + 1].strip()

        return cleaned

    def extract_project_info(self, cleaned_document_text: str) -> ProjectDocument:
        """
        Sends preprocessed text to Ollama with strict system instructions and JSON format.
        Validates output with Pydantic and returns a typed ProjectDocument instance.
        """
        user_prompt = build_user_prompt(cleaned_document_text)

        payload = {
            "model": self.model,
            "system": SYSTEM_EXTRACTION_PROMPT,
            "prompt": user_prompt,
            "format": "json",
            "stream": False,
            "options": {
                "temperature": 0.1,  # Low temperature for factual grounding
                "top_p": 0.9
            }
        }

        retries = 2
        last_error = ""

        for attempt in range(1, retries + 1):
            try:
                logger.info(f"Submitting extraction request to Ollama ({self.model}), attempt {attempt}/{retries}")
                with httpx.Client(timeout=self.timeout) as client:
                    response = client.post(
                        f"{self.base_url}/api/generate",
                        json=payload
                    )

                if response.status_code != 200:
                    raise LLMInferenceError(
                        f"Ollama server returned error {response.status_code}: {response.text}"
                    )

                result = response.json()
                raw_output = result.get("response", "")
                if not raw_output:
                    raise LLMInferenceError("Ollama returned an empty response.")

                cleaned_json_str = self._clean_json_response(raw_output)

                try:
                    data = json.loads(cleaned_json_str)
                except json.JSONDecodeError as je:
                    logger.warning(f"Failed to parse LLM JSON on attempt {attempt}: {je}")
                    last_error = f"Invalid JSON format from LLM: {je}"
                    continue

                # Validate against strict Pydantic model
                validated_doc = validate_project_data(data)
                logger.info("Successfully validated extracted project documentation schema.")
                return validated_doc

            except httpx.ConnectError:
                raise LLMInferenceError(
                    f"Connection refused at {self.base_url}. Ensure Ollama is running (`ollama serve`)."
                )
            except httpx.TimeoutException:
                last_error = f"Ollama request timed out after {self.timeout} seconds."
                logger.warning(last_error)
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Error during LLM extraction: {last_error}")

        raise LLMInferenceError(f"Extraction failed after {retries} attempts: {last_error}")
