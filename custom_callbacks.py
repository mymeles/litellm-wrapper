# custom_callbacks.py
import os
import json
import asyncio
from typing import Any, Dict, Optional

import httpx
from litellm.integrations.custom_logger import CustomLogger

# Supabase Edge Function URL – set this as an env var in Railway
SUPABASE_FUNCTION_URL = os.getenv("SUPABASE_LITELLM_USAGE_URL")
# Optional: Supabase anon key (default auth for public edge function)
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
# Optional: Supabase service role key for authenticated edge functions
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")


class SupabaseUsageLogger(CustomLogger):
    """
    Custom LiteLLM logger which forwards usage data to a Supabase Edge Function.

    This runs after each request (success/failure) and sends a payload like:
    {
      "id": "litellm-call-id",
      "model": "gpt-4o",
      "usage": {
        "prompt_tokens": 10,
        "completion_tokens": 20,
        "total_tokens": 30
      },
      "response_cost": 0.0015,
      "metadata": {...},
      "request_id": "provider-request-id",
      "status": "success" | "failure"
    }
    """

    # --------- Async entrypoints that LiteLLM calls ----------

    async def async_log_success_event(
        self,
        kwargs: Dict[str, Any],
        response_obj: Any,
        start_time: float,
        end_time: float,
    ):
        print("[SupabaseUsageLogger] 🔔 async_log_success_event called!")
        await self._send_event("success", kwargs, response_obj)

    async def async_log_failure_event(
        self,
        kwargs: Dict[str, Any],
        response_obj: Any,
        start_time: float,
        end_time: float,
    ):
        print("[SupabaseUsageLogger] 🔔 async_log_failure_event called!")
        await self._send_event("failure", kwargs, response_obj)

    # Optional sync versions (LiteLLM may call these in some paths)
    def log_success_event(
        self,
        kwargs: Dict[str, Any],
        response_obj: Any,
        start_time: float,
        end_time: float,
    ):
        print("[SupabaseUsageLogger] 🔔 log_success_event (sync) called!")
        self._run_sync("success", kwargs, response_obj)

    def log_failure_event(
        self,
        kwargs: Dict[str, Any],
        response_obj: Any,
        start_time: float,
        end_time: float,
    ):
        print("[SupabaseUsageLogger] 🔔 log_failure_event (sync) called!")
        self._run_sync("failure", kwargs, response_obj)

    # --------- Internal helpers ----------

    async def _send_event(
        self,
        status: str,
        kwargs: Dict[str, Any],
        response_obj: Any,
    ):
        # If env var isn’t set, just do nothing
        if not SUPABASE_FUNCTION_URL:
            print("[SupabaseUsageLogger] ⚠️  SUPABASE_LITELLM_USAGE_URL not set, skipping")
            return

        try:
            payload = self._build_payload(status, kwargs, response_obj)
            print(f"[SupabaseUsageLogger] 📤 Sending {status} event to Supabase")
            print(f"[SupabaseUsageLogger] Payload: {json.dumps(payload, indent=2)}")
        except Exception as e:
            print(f"[SupabaseUsageLogger] ❌ Error building payload: {e}")
            return

        try:
            # Build headers - add auth if service / anon key is provided
            headers = {"Content-Type": "application/json"}
            # Prefer the anon key unless the service role key is explicitly required
            supabase_auth_key = SUPABASE_ANON_KEY or SUPABASE_SERVICE_ROLE_KEY
            if supabase_auth_key:
                headers["Authorization"] = f"Bearer {supabase_auth_key}"
                headers["apikey"] = supabase_auth_key

            async with httpx.AsyncClient(timeout=5.0) as client:
                r = await client.post(SUPABASE_FUNCTION_URL, json=payload, headers=headers)
                if r.status_code >= 400:
                    print(
                        f"[SupabaseUsageLogger] ❌ Supabase returned {r.status_code}: {r.text}"
                    )
                else:
                    print(f"[SupabaseUsageLogger] ✅ Successfully sent to Supabase (status: {r.status_code})")
        except Exception as e:
            # Don’t break user requests if logging fails
            print(f"[SupabaseUsageLogger] ❌ Error sending to Supabase: {e}")

    def _build_payload(
        self,
        status: str,
        kwargs: Dict[str, Any],
        response_obj: Any,
    ) -> Dict[str, Any]:
        # LiteLLM usually passes these fields in kwargs
        usage = kwargs.get("usage") or {}
        response_cost = kwargs.get("response_cost", 0)
        model = (
            kwargs.get("model")
            or kwargs.get("complete_model")
            or kwargs.get("litellm_params", {}).get("model")
            or "unknown"
        )

        # Metadata can be passed in different places
        metadata = (
            kwargs.get("metadata")
            or kwargs.get("litellm_params", {}).get("metadata")
            or {}
        )

        # LiteLLM-generated ID for this call
        litellm_call_id = kwargs.get("litellm_call_id")

        # Try to extract provider request id from response_obj
        provider_request_id: Optional[str] = None
        try:
            if isinstance(response_obj, dict):
                provider_request_id = response_obj.get("id")
            else:
                # Some SDKs use attribute-style access
                provider_request_id = getattr(response_obj, "id", None)
        except Exception:
            provider_request_id = None

        # Build usage structure, with fallback to response_obj if needed
        if not usage:
            try:
                if isinstance(response_obj, dict):
                    usage = response_obj.get("usage", {}) or {}
                else:
                    usage = getattr(response_obj, "usage", {}) or {}
            except Exception:
                usage = {}

        payload: Dict[str, Any] = {
            "id": litellm_call_id,
            "model": model,
            "usage": {
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
            },
            "response_cost": float(response_cost or 0),
            "metadata": metadata,
            "request_id": provider_request_id,
            "status": status,
        }

        # Optional: include raw kwargs for debugging (comment out if you want it lean)
        # payload["raw"] = {
        #     "kwargs": kwargs,
        # }

        return payload

    def _run_sync(self, status: str, kwargs: Dict[str, Any], response_obj: Any):
        """
        Helper to bridge sync callbacks when we're already inside an event loop (uvicorn).
        """
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            asyncio.run(self._send_event(status, kwargs, response_obj))
            return

        loop.create_task(self._send_event(status, kwargs, response_obj))


# Instance that LiteLLM will reference in config:
supabase_usage_logger = SupabaseUsageLogger()
