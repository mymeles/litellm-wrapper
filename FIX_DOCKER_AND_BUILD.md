# Fix Docker and Build for Railway

## Issue
You're getting a Docker daemon I/O error. This needs Docker Desktop to be restarted.

---

## Steps to Fix and Build

### 1. Restart Docker Desktop

**Option A: Via GUI**
- Click the Docker icon in your menu bar (top right)
- Click "Restart"
- Wait for Docker to fully restart (whale icon should be steady, not animated)

**Option B: Via Terminal**
```bash
# Quit Docker
osascript -e 'quit app "Docker"'

# Wait a few seconds
sleep 5

# Start Docker
open -a Docker

# Wait for Docker to be ready (this may take 30-60 seconds)
```

### 2. Verify Docker is Running

```bash
docker ps
```

You should see output without errors.

### 3. Build and Push for Railway (linux/amd64)

Once Docker is running, use this command:

```bash
docker buildx build --platform linux/amd64 \
  -t ghcr.io/mymeles/litellm-wrapper:v1.0.0 \
  -t ghcr.io/mymeles/litellm-wrapper:latest \
  --push .
```

**Or use the updated script:**

```bash
./build-and-push.sh v1.0.0 --push
```

---

## Why This Happened

You're on Apple Silicon (ARM64), but Railway uses Intel/AMD (x86_64/amd64) architecture.

When you build without specifying `--platform linux/amd64`, Docker builds for ARM64, which causes the "Exec format error" on Railway.

The updated `build-and-push.sh` script now always builds for `linux/amd64` to prevent this issue.

---

## After Successful Build

Once the build completes and pushes successfully, go to Railway and:

1. Make sure your service is using: `ghcr.io/mymeles/litellm-wrapper:v1.0.0`
2. Redeploy
3. Check the logs - you should see:
   ```
   INFO:     Uvicorn running on http://0.0.0.0:4000
   ```

And when you make an API call, you'll see:
```
[SupabaseUsageLogger] 📤 Sending success event to Supabase
```

---

## Quick Commands Summary

```bash
# 1. Restart Docker (if needed)
osascript -e 'quit app "Docker"' && sleep 5 && open -a Docker

# 2. Wait for Docker to start, then verify
docker ps

# 3. Build and push
docker buildx build --platform linux/amd64 \
  -t ghcr.io/mymeles/litellm-wrapper:v1.0.0 \
  -t ghcr.io/mymeles/litellm-wrapper:latest \
  --push .
```

