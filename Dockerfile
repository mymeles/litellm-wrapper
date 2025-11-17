# Dockerfile
FROM ghcr.io/berriai/litellm:main-stable

WORKDIR /app

# Add custom callback module and config
COPY custom_callbacks.py ./custom_callbacks.py
COPY config.yaml ./config.yaml

# Set Python path so LiteLLM can import custom_callbacks
ENV PYTHONPATH=/app:$PYTHONPATH

# Tell the proxy where to find our config so callbacks & settings load even when models live in the DB
ENV CONFIG_FILE_PATH=/app/config.yaml

# Point to config file (this will load callbacks)
ENV LITELLM_CONFIG=/app/config.yaml
