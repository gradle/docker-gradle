FROM ubuntu:jammy

CMD ["gradle"]

ENV GRADLE_HOME=/opt/gradle

RUN set -o errexit -o nounset \
    && echo "Adding gradle user and group" \
    && groupadd --system --gid 1000 gradle \
    && useradd --system --gid gradle --uid 1000 --shell /bin/bash --create-home gradle \
    && mkdir /home/gradle/.gradle \
    && chown --recursive gradle:gradle /home/gradle \
    && chmod --recursive o+rwx /home/gradle \
    \
    && echo "Symlinking root Gradle cache to gradle Gradle cache" \
    && ln --symbolic /home/gradle/.gradle /root/.gradle

VOLUME /home/gradle/.gradle

WORKDIR /home/gradle

RUN set -o errexit -o nounset \
    && export DEBIAN_FRONTEND=noninteractive \
    && apt-get update \
    && apt-get install --yes --no-install-recommends \
        # common utilities
        make \
        \
        # Gradle & Dockerfile dependencies
        binutils \
        ca-certificates \
        curl \
        fontconfig \
        locales \
        p11-kit \
        tzdata \
        unzip \
        wget \
        \
        # build dependencies
        gcc \
        libc-dev \
        libz-dev \
        zlib1g-dev \
        \
        # VCSes
        brz \
        git \
        git-lfs \
        mercurial \
        openssh-client \
        subversion \
    && rm --recursive --force /var/lib/apt/lists/* \
    \
    && echo "Testing common utilities" \
    && which awk \
    && which curl \
    && which cut \
    && which grep \
    && which gunzip \
    && which sha256sum \
    && which sed \
    && which tar \
    && which tr \
    && which unzip \
    && which wget \
    \
    && echo "Testing VCSes" \
    && which brz \
    && which git \
    && which git-lfs \
    && which hg \
    && which svn

ENV JAVA_HOME=/opt/java/graalvm
ENV JAVA_VERSION=21.0.2
RUN set -o errexit -o nounset \
    && mkdir /opt/java \
    \
    && echo "Downloading GraalVM" \
    && GRAALVM_AMD64_DOWNLOAD_SHA256=b048069aaa3a99b84f5b957b162cc181a32a4330cbc35402766363c5be76ae48 \
    && GRAALVM_AARCH64_DOWNLOAD_SHA256=a34be691ce68f0acf4655c7c6c63a9a49ed276a11859d7224fd94fc2f657cd7a \
    && ARCHITECTURE=$(dpkg --print-architecture) \
    && if [ "${ARCHITECTURE}" = "amd64" ]; then GRAALVM_ARCHITECTURE=linux-x64; fi \
    && if [ "${ARCHITECTURE}" = "arm64" ]; then GRAALVM_ARCHITECTURE=linux-aarch64; fi \
    && GRAALVM_PKG=https://github.com/graalvm/graalvm-ce-builds/releases/download/jdk-${JAVA_VERSION}/graalvm-community-jdk-${JAVA_VERSION}_${GRAALVM_ARCHITECTURE}_bin.tar.gz \
    && wget --no-verbose --output-document=graalvm.tar.gz "${GRAALVM_PKG}" \
    \
    && echo "Checking GraalVM download hash" \
    && if [ "${ARCHITECTURE}" = "amd64" ]; then GRAALVM_DOWNLOAD_SHA256="${GRAALVM_AMD64_DOWNLOAD_SHA256}"; fi \
    && if [ "${ARCHITECTURE}" = "arm64" ]; then GRAALVM_DOWNLOAD_SHA256="${GRAALVM_AARCH64_DOWNLOAD_SHA256}"; fi \
    && echo "${GRAALVM_DOWNLOAD_SHA256} *graalvm.tar.gz" | sha256sum --check - \
    \
    && echo "Installing GraalVM" \
    && tar --extract --gunzip --file graalvm.tar.gz \
    && rm graalvm.tar.gz \
    && mv graalvm-* "${JAVA_HOME}" \
    && for bin in "$JAVA_HOME/bin/"*; do \
        base="$(basename "$bin")"; \
        [ ! -e "/usr/bin/$base" ]; \
        update-alternatives --install "/usr/bin/${base}" "${base}" "${bin}" 1; \
    done \
    \
    && echo "Testing GraalVM installation" \
    && java --version \
    && javac --version \
    && native-image --version

ENV GRADLE_VERSION=9.0.0
ARG GRADLE_DOWNLOAD_SHA256=8fad3d78296ca518113f3d29016617c7f9367dc005f932bd9d93bf45ba46072b
RUN set -o errexit -o nounset \
    && echo "Downloading Gradle" \
    && wget --no-verbose --output-document=gradle.zip "https://services.gradle.org/distributions/gradle-${GRADLE_VERSION}-bin.zip" \
    \
    && echo "Checking Gradle download hash" \
    && echo "${GRADLE_DOWNLOAD_SHA256} *gradle.zip" | sha256sum --check - \
    \
    && echo "Installing Gradle" \
    && unzip gradle.zip \
    && rm gradle.zip \
    && mv "gradle-${GRADLE_VERSION}" "${GRADLE_HOME}/" \
    && ln --symbolic "${GRADLE_HOME}/bin/gradle" /usr/bin/gradle

USER gradle

RUN set -o errexit -o nounset \
    && echo "Testing Gradle installation" \
    && gradle --version

USER root
