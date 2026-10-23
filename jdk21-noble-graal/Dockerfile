FROM ubuntu:noble

CMD ["gradle"]

ENV GRADLE_HOME=/opt/gradle

RUN set -o errexit -o nounset \
    && echo "Renaming ubuntu user and group to gradle" \
    && groupmod --new-name gradle ubuntu \
    && mkdir /home/gradle \
    && usermod --login gradle --home /home/gradle --groups gradle ubuntu \
    && chown gradle /home/gradle \
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
ENV JAVA_VERSION=21.0.12.1+2
RUN set -o errexit -o nounset \
    && mkdir /opt/java \
    \
    && echo "Downloading Liberica NIK" \
    && LIBERICA_NIK_AMD64_DOWNLOAD_SHA256=2d8dea534797f5056155ea34415a9ea6cb95f1c0e0bd372f286709d6424b0823 \
    && LIBERICA_NIK_AARCH64_DOWNLOAD_SHA256=64ca37db6eab667bc3b822e1f7b49249997637e21d72b41469ae85d40f689e7c \
    && ARCHITECTURE=$(dpkg --print-architecture) \
    && if [ "${ARCHITECTURE}" = "amd64" ]; then LIBERICA_NIK_ARCHITECTURE=amd64; fi \
    && if [ "${ARCHITECTURE}" = "arm64" ]; then LIBERICA_NIK_ARCHITECTURE=aarch64; fi \
    && LIBERICA_NIK_RELEASE_TAG=23.1.12.1+1-21.0.12.1+2 \
    && LIBERICA_NIK_VERSION=23.1.12.1+1 \
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

ENV GRADLE_VERSION=8.14.6
ARG GRADLE_DOWNLOAD_SHA256=7988ed071b2a07900e2ec715fca15c6ab72bce6db433af301fa7fa7e9407bd24
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
