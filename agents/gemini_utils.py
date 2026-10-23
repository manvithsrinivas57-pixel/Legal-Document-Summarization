"""Utilities for Google Gemini API communication, retries, model discovery, and error handling."""

import logging
import re
import threading
import time
from typing import Any

import config

logger = logging.getLogger(__name__)

# Verified official text models supporting generateContent from the google.genai catalog
VERIFIED_OFFICIAL_GEMINI_MODELS = [
    "gemini-3.8-flash",
    "gemini-flash-lite-latest",
    "gemini-3.5-flash-lite",
    "gemini-flash-latest",
    "gemini-3-flash-preview",
    "gemini-3.5-flash",
    "gemini-pro-latest",
    "gemini-3.1-pro-preview",
    "gemini-3.6-flash",
    "gemini-3.7-flash",
]

_SUPPORTED_MODELS_CACHE: list[str] | None = None
_retry_lock = threading.Lock()


class GeminiServiceCoordinator:
    """Coordinates Gemini API calls across agents to prevent duplicate or simultaneous retry storms."""

    def __init__(self, cooldown_seconds: float = 30.0):
        self.cooldown_seconds = cooldown_seconds
        self._lock = threading.Lock()
        self._persistent_503_models: dict[str, float] = {}
        self._last_successful_model: str | None = None
        self._service_unavailable_until: float = 0.0

    def record_success(self, model: str) -> None:
        """Record that a model succeeded, clearing its degraded status."""
        clean_model = model.replace("models/", "").strip()
        with self._lock:
            self._last_successful_model = clean_model
            self._persistent_503_models.pop(clean_model, None)

    def record_persistent_503(self, model: str) -> None:
        """Record that a model has exhausted retries due to HTTP 503 UNAVAILABLE."""
        clean_model = model.replace("models/", "").strip()
        with self._lock:
            now = time.time()
            self._persistent_503_models[clean_model] = now
            self._service_unavailable_until = now + self.cooldown_seconds

    def is_model_degraded(self, model: str) -> bool:
        """Check whether a model is currently within a persistent 503 cooldown window."""
        clean_model = model.replace("models/", "").strip()
        with self._lock:
            ts = self._persistent_503_models.get(clean_model)
            if ts is None:
                return False
            if (time.time() - ts) < self.cooldown_seconds:
                return True
            self._persistent_503_models.pop(clean_model, None)
            return False

    def is_service_unavailable(self) -> bool:
        """Check whether the Gemini service was recently marked unavailable overall."""
        with self._lock:
            return time.time() < self._service_unavailable_until

    def get_last_successful_model(self) -> str | None:
        """Retrieve the last verified working model ID."""
        with self._lock:
            return self._last_successful_model

    def reset(self) -> None:
        """Reset all tracked state (used for test isolation)."""
        with self._lock:
            self._persistent_503_models.clear()
            self._last_successful_model = None
            self._service_unavailable_until = 0.0


_coordinator = GeminiServiceCoordinator()


def get_gemini_service_coordinator() -> GeminiServiceCoordinator:
    """Access the global Gemini service coordinator singleton."""
    return _coordinator


def reset_gemini_service_coordinator() -> None:
    """Reset service coordinator state (useful for test isolation)."""
    global _SUPPORTED_MODELS_CACHE
    _coordinator.reset()
    _SUPPORTED_MODELS_CACHE = None


def is_transient_gemini_error(exc: Exception) -> bool:
    """Detect whether an exception is a transient error suitable for retry.
    
    Includes HTTP 503 UNAVAILABLE, HTTP 429 RESOURCE_EXHAUSTED spikes, and dropped connections.
    Excludes non-transient errors like 400 Bad Request, 404 Model Not Found, and Invalid Key.
    """
    err_msg = str(exc).lower()

    # Check HTTP status code attributes if available on the exception object
    code = getattr(exc, "code", None) or getattr(exc, "status_code", None)
    status = str(getattr(exc, "status", "")).upper()

    # Non-transient errors: 400, 401, 403, 404 should never be treated as transient
    if code in (400, 401, 403, 404):
        return False
    if "404" in err_msg or "not_found" in err_msg or "model is not found" in err_msg:
        return False
    if "400" in err_msg or "invalid argument" in err_msg:
        return False
    if "api_key_invalid" in err_msg or "api key not valid" in err_msg:
        return False

    if code in (503, 429, 500, 502, 504):
        return True
    if status in ("UNAVAILABLE", "RESOURCE_EXHAUSTED"):
        return True

    transient_indicators = [
        "503",
        "unavailable",
        "high demand",
        "spikes in demand",
        "temporarily unavailable",
        "overloaded",
        "resource_exhausted",
        "429",
        "rate limit",
        "quota exceeded",
        "connection reset",
        "remotedisconnected",
        "connection refused",
        "timed out",
        "timeout",
    ]
    return any(indicator in err_msg for indicator in transient_indicators)


def format_user_friendly_gemini_error(
    exc: Exception, retries_attempted: int = 0, model_id: str | None = None
) -> str:
    """Format raw Gemini / GenAI exceptions into clean, academic and user-friendly error messages."""
    err_str = str(exc)

    if "503" in err_str or "UNAVAILABLE" in err_str or "high demand" in err_str.lower():
        retry_note = f" (after {retries_attempted} retries with exponential backoff)" if retries_attempted > 0 else ""
        return (
            f"Google Gemini service is temporarily unavailable due to high demand (HTTP 503 UNAVAILABLE){retry_note}. "
            "Please retry shortly or select an alternative model in the sidebar. "
            "In adherence to research ethics, legal analysis is not fabricated."
        )

    if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "quota exceeded" in err_str.lower():
        retry_note = f" (after {retries_attempted} retries)" if retries_attempted > 0 else ""
        return (
            f"Google Gemini API rate quota reached (HTTP 429 RESOURCE_EXHAUSTED){retry_note}. "
            "Free-tier rate limits may apply; please retry in a few moments or provide a custom API key. "
            "In adherence to research ethics, legal analysis is not fabricated."
        )

    if "404" in err_str or "NOT_FOUND" in err_str or "not found" in err_str.lower():
        model_clause = f" '{model_id}'" if model_id else ""
        return (
            f"The configured Gemini model{model_clause} was not found or is invalid (HTTP 404 NOT_FOUND). "
            "Please select an active model (such as gemini-3.8-flash or gemini-flash-lite-latest) in the sidebar. "
            "In adherence to research ethics, legal analysis is not fabricated."
        )

    if "API_KEY_INVALID" in err_str or "api key not valid" in err_str.lower():
        return "Invalid Google Gemini API key. Please verify the GEMINI_API_KEY value in your .env configuration."

    # Strip raw JSON dictionary dumps
    clean = re.sub(r"\{'error':.*?\}", "", err_str).strip()
    clean = re.sub(r"\s+", " ", clean).strip()
    return f"Gemini API request failed: {clean or err_str[:150]}"


def get_supported_gemini_models(api_key: str | None = None, force_refresh: bool = False) -> list[str]:
    """Retrieve verified supported Gemini model IDs using the installed SDK official listing mechanism.
    
    Filters out deprecated (404), audio-only (TTS), image-only, and non-text models.
    Caches the discovered list for performance.
    """
    global _SUPPORTED_MODELS_CACHE
    if _SUPPORTED_MODELS_CACHE is not None and not force_refresh:
        return list(_SUPPORTED_MODELS_CACHE)

    key = api_key or config.get_gemini_api_key()
    if not key:
        return list(VERIFIED_OFFICIAL_GEMINI_MODELS)

    try:
        from google import genai
        client = genai.Client(api_key=key)
        discovered = []
        for m in client.models.list():
            actions = getattr(m, "supported_actions", None) or []
            if actions and "generateContent" not in actions:
                continue
            mid = getattr(m, "name", "").replace("models/", "").strip()
            if not mid:
                continue
            # Exclude non-text/specialized model families
            if any(kw in mid.lower() for kw in [
                "tts", "image", "banana", "computer-use", "clip",
                "transcribe", "argon", "lyria", "deep-research", "robotics"
            ]):
                continue
            # Keep official gemini models, excluding deprecated 2.5 which return 404
            if mid.startswith("gemini-") and not mid.startswith("gemini-2.5"):
                discovered.append(mid)

        if discovered:
            def sort_priority(name: str) -> int:
                if name == config.DEFAULT_GEMINI_MODEL:
                    return 0
                if "flash-lite" in name:
                    return 1
                if "flash" in name:
                    return 2
                if "pro" in name:
                    return 3
                return 4

            discovered.sort(key=sort_priority)
            _SUPPORTED_MODELS_CACHE = discovered
            return list(discovered)
    except Exception as exc:
        logger.warning("Failed to dynamically list models from Gemini API: %s", exc)

    return list(VERIFIED_OFFICIAL_GEMINI_MODELS)


def verify_gemini_model_id(client: Any, model_id: str) -> bool:
    """Verify whether a model ID is supported by Google GenAI using the installed SDK."""
    if not model_id or not isinstance(model_id, str):
        return False
    clean_id = model_id.replace("models/", "").strip()
    try:
        model = client.models.get(model=clean_id)
        actions = getattr(model, "supported_actions", None) or []
        if actions and "generateContent" not in actions:
            return False
        return True
    except Exception:
        # If client.models.get fails (e.g. 404 NOT_FOUND), model is invalid
        return False


def execute_gemini_with_retry(
    client: Any,
    primary_model: str,
    contents: str,
    max_retries: int = 3,
    initial_delay: float = 1.5,
    backoff_factor: float = 2.0,
    fallback_models: list[str] | None = None,
    avoid_retry_storm: bool = False,
    coordinator: GeminiServiceCoordinator | None = None,
) -> tuple[str, str, int]:
    """Execute Gemini generate_content with up to max_retries for transient errors.
    
    Prevents duplicate and simultaneous retry storms across Document Structure Analysis
    and Jurisprudential Reasoning using exponential backoff and coordinated state.
    
    Returns:
        tuple of (raw_response_text, model_used, total_retries_taken)
        
    Raises:
        Exception: if all retries and candidate fallbacks fail.
    """
    coord = coordinator or _coordinator
    last_exception = None
    total_retries = 0

    target_primary = primary_model.replace("models/", "").strip()
    known_healthy = coord.get_last_successful_model()
    is_primary_degraded = coord.is_model_degraded(target_primary)

    service_degraded = bool(avoid_retry_storm or is_primary_degraded or coord.is_service_unavailable())
    effective_max_retries = 0 if service_degraded else max_retries

    # If the primary model was already marked persistently 503 and a healthy alternative is known,
    # switch directly to the healthy alternative to prevent failing again
    if is_primary_degraded and known_healthy and known_healthy != target_primary:
        target_primary = known_healthy

    # Use lock to prevent simultaneous retry storms across threads
    with _retry_lock:
        # 1. Attempt target primary model with exponential backoff retries
        for attempt in range(effective_max_retries + 1):
            try:
                response = client.models.generate_content(
                    model=target_primary,
                    contents=contents,
                )
                text = getattr(response, "text", "") or ""
                if text.strip():
                    coord.record_success(target_primary)
                    return text, target_primary, total_retries
                else:
                    raise ValueError("Gemini returned an empty response string.")
            except Exception as exc:
                last_exception = exc
                if attempt < effective_max_retries and is_transient_gemini_error(exc):
                    total_retries += 1
                    sleep_duration = initial_delay * (backoff_factor ** attempt)
                    time.sleep(sleep_duration)
                else:
                    break

        if last_exception and is_transient_gemini_error(last_exception):
            coord.record_persistent_503(target_primary)

        # 2. If target model exhausted retries due to a transient error, try distinct fallback models
        # When avoid_retry_storm / service_degraded is active, do not repeat a storm across all fallbacks
        if fallback_models and last_exception and is_transient_gemini_error(last_exception) and not service_degraded:
            distinct_fallbacks = [
                m.replace("models/", "").strip()
                for m in fallback_models
                if m.replace("models/", "").strip() != target_primary
                and m.replace("models/", "").strip() != primary_model.replace("models/", "").strip()
            ]
            # Prioritize known healthy model if present in fallbacks
            if known_healthy and known_healthy in distinct_fallbacks:
                distinct_fallbacks.remove(known_healthy)
                distinct_fallbacks.insert(0, known_healthy)

            for fb_model in distinct_fallbacks:
                try:
                    response = client.models.generate_content(
                        model=fb_model,
                        contents=contents,
                    )
                    text = getattr(response, "text", "") or ""
                    if text.strip():
                        coord.record_success(fb_model)
                        return text, fb_model, total_retries
                except Exception:
                    continue

    if last_exception:
        raise last_exception
    raise RuntimeError("Gemini content generation failed with no response.")
