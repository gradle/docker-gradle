FROM bash:5

WORKDIR /ws

# See https://github.com/docker-library/bashbrew?tab=readme-ov-file#installing
RUN apk add --no-cache \
    ca-certificates \
    curl \
    git \
    jq \
    && git config --global --add safe.directory '*'

ARG BASHBREW_VERSION=0.1.13
RUN curl -fsSL -o /usr/local/bin/bashbrew "https://github.com/docker-library/bashbrew/releases/download/v${BASHBREW_VERSION}/bashbrew-amd64" && \
    chmod +x /usr/local/bin/bashbrew && \
    bashbrew --version
