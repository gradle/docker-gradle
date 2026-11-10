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
        curl \
        wget \
        tar \
        \
        # Gradle & Dockerfile dependencies
        binutils \
        ca-certificates \
        fontconfig \
        locales \
        p11-kit \
        tzdata \
        unzip \
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
ENV JAVA_VERSION=17.0.21.0.3+6
RUN set -o errexit -o nounset \
    && mkdir /opt/java \
    \
    && echo "Downloading Liberica NIK" \
    && LIBERICA_NIK_AMD64_DOWNLOAD_SHA256=0e6b739f30701397534bd75119d2ede5ffad0dc7b26d48d6c28e7aa88f8cde30 \
    && LIBERICA_NIK_AARCH64_DOWNLOAD_SHA256=fd0b2796c7cfba8f1425e4c77d5a2043e0504b4e59b87a0d8a6eddf440aeea3c \
    && ARCHITECTURE=$(dpkg --print-architecture) \
    && if [ "${ARCHITECTURE}" = "amd64" ]; then LIBERICA_NIK_ARCHITECTURE=amd64; fi \
    && if [ "${ARCHITECTURE}" = "arm64" ]; then LIBERICA_NIK_ARCHITECTURE=aarch64; fi \
    && LIBERICA_NIK_RELEASE_TAG=23.0.14+1-17.0.21.0.3+6 \
    && LIBERICA_NIK_VERSION=23.0.14+1 \
    && LIBERICA_NIK_PKG=https://github.com/bell-sw/LibericaNIK/releases/download/${LIBERICA_NIK_RELEASE_TAG}/bellsoft-liberica-vm-openjdk${JAVA_VERSION}-${LIBERICA_NIK_VERSION}-linux-${LIBERICA_NIK_ARCHITECTURE}.tar.gz \
    && wget --no-verbose --output-document=liberica-nik.tar.gz "${LIBERICA_NIK_PKG}" \
    \
    && echo "Checking Liberica NIK download hash" \
    && if [ "${ARCHITECTURE}" = "amd64" ]; then LIBERICA_NIK_DOWNLOAD_SHA256="${LIBERICA_NIK_AMD64_DOWNLOAD_SHA256}"; fi \
    && if [ "${ARCHITECTURE}" = "arm64" ]; then LIBERICA_NIK_DOWNLOAD_SHA256="${LIBERICA_NIK_AARCH64_DOWNLOAD_SHA256}"; fi \
    && echo "${LIBERICA_NIK_DOWNLOAD_SHA256} *liberica-nik.tar.gz" | sha256sum --check - \
    \
    && echo "Installing Liberica NIK" \
    && mkdir "${JAVA_HOME}" \
    && tar --extract --gunzip --file liberica-nik.tar.gz --strip-components=1 --directory "${JAVA_HOME}" \
    && rm liberica-nik.tar.gz \
    && for bin in "$JAVA_HOME/bin/"*; do \
        base="$(basename "$bin")"; \
        [ ! -e "/usr/bin/$base" ]; \
        update-alternatives --install "/usr/bin/${base}" "${base}" "${bin}" 1; \
    done \
    \
    && echo "Testing Liberica NIK installation" \
    && java --version \
    && javac --version \
    && native-image --version

ENV GRADLE_VERSION=9.9.1
ARG GRADLE_DOWNLOAD_SHA256=d8a18a7a841dd5df825d35a685fad6f2d7f12ac0c280e57b67c27b4a520ba228
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
    && gradle --stacktrace --debug --version

USER root
