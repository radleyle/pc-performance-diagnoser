"""
Send structured diagnosis JSON to Ollama and get a plain-English explanation.

The LLM only explains what the detection engine found — it does not detect issues.
"""

import json

import httpx

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
DEFAULT_MODEL = "llama3.2"
REQUEST_TIMEOUT_SECONDS = 60.0


class OllamaError(Exception):
    """Raised when Ollama is unreachable or returns an error."""


def build_prompt(diagnosis: dict) -> str:
    """
    Build the prompt sent to the LLM.

    We pass the full diagnosis JSON so the model has evidence to explain.
    """
    issues_json = json.dumps(diagnosis, indent=2)

    return f"""You are a helpful PC performance assistant.

You will receive JSON from a rule-based detection engine that already analyzed real system metrics.
Your job is ONLY to explain the results in plain English and suggest 2-3 practical fixes.

STRICT RULES:
- Do NOT invent new issues, processes, or numbers that are not in the JSON.
- If issues is empty, say the system looks healthy and give light maintenance tips.
- Keep the response under 150 words.
- Be direct and friendly.

DIAGNOSIS JSON:
{issues_json}

Write a short explanation for the user:"""


def explain_diagnosis(diagnosis: dict, model: str = DEFAULT_MODEL) -> str:
    """
    Call Ollama and return the plain-English explanation string.
    """
    prompt = build_prompt(diagnosis)

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
    }

    try:
        response = httpx.post(
            OLLAMA_URL,
            json=payload,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
    except httpx.ConnectError as exc:
        raise OllamaError(
            "Cannot connect to Ollama. Is it running? Try: ollama serve"
        ) from exc
    except httpx.HTTPError as exc:
        raise OllamaError(f"Ollama request failed: {exc}") from exc

    data = response.json()
    explanation = data.get("response", "").strip()

    if not explanation:
        raise OllamaError("Ollama returned an empty response")

    return explanation