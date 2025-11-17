# Railway Callback Setup Guide

## Problem
When LiteLLM models are managed through the UI/database (not in `config.yaml`), the `config.yaml` callbacks are ignored.

## Solution
Use environment variables to register the callback instead.

---

## 🚀 Setup Steps

### 1. Rebuild and Push the Docker Image

The Dockerfile has been updated to only copy `custom_callbacks.py` and set `PYTHONPATH`.

> The image now exports `CONFIG_FILE_PATH=/app/config.yaml`, so LiteLLM always loads your `config.yaml` (callbacks + settings) even when deployments are managed via the database/UI.

```bash
docker buildx build --platform linux/amd64 \
  -t ghcr.io/mymeles/litellm-wrapper:v1.0.1 \
  -t ghcr.io/mymeles/litellm-wrapper:latest \
  --push .
```

### 2. Add Environment Variable in Railway

Go to your Railway service → **Variables** tab and add:

**Variable Name:**
```
LITELLM_CALLBACKS
```

**Variable Value:**
```
custom_callbacks.supabase_usage_logger
```

This tells LiteLLM to import and use the `supabase_usage_logger` instance from the `custom_callbacks` module.

### 3. Make Sure This Variable is Also Set

**Variable Name:**
```
SUPABASE_LITELLM_USAGE_URL
```

**Variable Value:**
```
https://your-project.supabase.co/functions/v1/litellm-usage
```

Replace with your actual Supabase edge function URL.

> 🔐 Edge functions require either the anon key or the service role key. Add one of these in Railway as well (the logger will default to the anon key if both exist):
> - `SUPABASE_ANON_KEY`
> - `SUPABASE_SERVICE_ROLE_KEY`
>
> The callback automatically sends the key in both the `Authorization` and `apikey` headers so Supabase accepts the request.

### 4. Redeploy

After adding the environment variables, redeploy your Railway service with the new image:
```
ghcr.io/mymeles/litellm-wrapper:v1.0.1
```

---

## ✅ Verification

After deployment, check the Railway logs. When you make an API call to `/v1/chat/completions`, you should see:

```
[SupabaseUsageLogger] 📤 Sending success event to Supabase
[SupabaseUsageLogger] Payload: {...}
[SupabaseUsageLogger] ✅ Successfully sent to Supabase (status: 200)
```

If you see:
```
[SupabaseUsageLogger] ⚠️  SUPABASE_LITELLM_USAGE_URL not set, skipping
```

Then the `SUPABASE_LITELLM_USAGE_URL` environment variable is missing.

---

## 📝 Expected Payload Format

Your Supabase edge function should expect this JSON structure:

```json
{
  "id": "litellm-call-id-12345",
  "model": "gpt-4o",
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 20,
    "total_tokens": 30
  },
  "response_cost": 0.0015,
  "metadata": {
    "user_api_key": "sk-...",
    "user_api_key_user_id": "user-123"
  },
  "request_id": "chatcmpl-xyz",
  "status": "success"
}
```

The `status` field will be either `"success"` or `"failure"`.

---

## 🔍 Troubleshooting

### Callback not firing?

1. **Check Railway logs** for import errors:
   ```
   ModuleNotFoundError: No module named 'custom_callbacks'
   ```
   → Make sure `PYTHONPATH=/app:$PYTHONPATH` is set in Dockerfile

2. **Check if callback is registered:**
   Look for this in startup logs:
   ```
   INFO: Registered callbacks: ['custom_callbacks.supabase_usage_logger']
   ```

3. **Test with a real API call:**
   ```bash
   curl -X POST https://your-railway-app.railway.app/v1/chat/completions \
     -H "Authorization: Bearer sk-your-litellm-key" \
     -H "Content-Type: application/json" \
     -d '{
       "model": "gpt-4o",
       "messages": [{"role": "user", "content": "Hello!"}]
     }'
   ```

### Supabase function not receiving data?

1. **Check the function URL** is correct and publicly accessible
2. **Check Supabase function logs** for incoming requests
3. **Verify the function accepts POST requests** with JSON body
4. **Check for CORS issues** if calling from browser

---

## 📚 References

- [LiteLLM Callbacks Documentation](https://docs.litellm.ai/docs/observability/custom_callback)
- [LiteLLM Environment Variables](https://docs.litellm.ai/docs/proxy/configs#environment-variables)
