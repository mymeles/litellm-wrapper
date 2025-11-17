# Railway Setup Guide for GHCR Image

## Issue: Container failed to start - Registry access denied

Railway can't pull your private image from GitHub Container Registry.

---

## Solution 1: Make the Image Public (Recommended & Easiest)

1. Go to your GitHub package page:
   ```
   https://github.com/users/mymeles/packages/container/litellm-wrapper/settings
   ```

2. Scroll down to **"Danger Zone"**

3. Click **"Change visibility"**

4. Select **"Public"**

5. Type the repository name to confirm: `litellm-wrapper`

6. Click **"I understand, change package visibility"**

7. Go back to Railway and redeploy with the image:
   ```
   ghcr.io/mymeles/litellm-wrapper:latest
   ```

---

## Solution 2: Add GitHub Container Registry Credentials to Railway

If you want to keep the image private:

### Step 1: Create a GitHub Personal Access Token (PAT)

1. Go to: https://github.com/settings/tokens/new
2. Give it a name: `Railway GHCR Access`
3. Select scopes:
   - ✅ `read:packages` (required)
4. Click **"Generate token"**
5. **Copy the token** (you won't see it again!)

### Step 2: Add credentials to Railway

Railway doesn't have a built-in way to add registry credentials via the UI for custom registries.

You have two options:

#### Option 2A: Use Railway CLI to set registry credentials

```bash
# Install Railway CLI if you haven't
npm i -g @railway/cli

# Login to Railway
railway login

# Link to your project
railway link

# Set the registry credentials as environment variables
railway variables set DOCKER_REGISTRY_USER=mymeles
railway variables set DOCKER_REGISTRY_TOKEN=ghp_your_token_here
```

Then update your Railway service to use these credentials.

#### Option 2B: Deploy via Railway GitHub Integration (Recommended for private images)

Instead of using a pre-built image, let Railway build the image for you:

1. In Railway, create a new service
2. Choose **"Deploy from GitHub repo"**
3. Select your `mymeles/litellm-wrapper` repository
4. Railway will automatically:
   - Clone your repo
   - Build the Dockerfile
   - Deploy the container
5. Set your environment variables in Railway

This way, Railway builds the image internally and doesn't need to pull from GHCR.

---

## Recommended Approach

**For your use case, I recommend Solution 1 (make it public)** because:
- ✅ Simplest setup
- ✅ No credential management needed
- ✅ Faster deployments (no build time)
- ✅ The image doesn't contain secrets (secrets are in env vars)

Your `.evn` file with sensitive data is **NOT** included in the Docker image (it's not in the Dockerfile COPY commands), so making the image public is safe.

---

## After Making the Image Public

1. In Railway, go to your service
2. Settings → Image
3. Enter: `ghcr.io/mymeles/litellm-wrapper:latest`
4. Deploy

The image should pull successfully!

