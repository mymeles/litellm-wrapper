# Dockerfile
FROM ghcr.io/berriai/litellm:main-stable

WORKDIR /app

# Add callback + config into the container
COPY custom_callbacks.py ./custom_callbacks.py
COPY config.yaml ./config.yaml

# Point LiteLLM to this config file
# This ONLY adds callbacks; your models are in Postgres.
ENV LITELLM_CONFIG=/app/config.yaml
