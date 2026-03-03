FROM python:3-alpine

WORKDIR /ws

# See https://github.com/docker-library/bashbrew?tab=readme-ov-file#installing
RUN apk add --no-cache \
    bash \
    ca-certificates \
    curl \
    git \
    && git config --global --add safe.directory '*'

RUN pip install --no-cache-dir requests

ARG BASHBREW_VERSION=0.1.13
RUN curl -fsSL -o /usr/local/bin/bashbrew "https://github.com/docker-library/bashbrew/releases/download/v${BASHBREW_VERSION}/bashbrew-amd64" && \
    chmod +x /usr/local/bin/bashbrew && \
    bashbrew --version
