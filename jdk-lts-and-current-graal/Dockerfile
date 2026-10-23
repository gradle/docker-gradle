FROM ubuntu:resolute

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
    && ln --symbolic /home/gradle/.gradle /root/.gradle \
   \
   && echo "Ensuring Gradle detects installed JDKs" \
   && echo "org.gradle.java.installations.auto-detect=false" > /home/gradle/.gradle/gradle.properties \
   && echo "org.gradle.java.installations.auto-download=false" >> /home/gradle/.gradle/gradle.properties \
   && echo "org.gradle.java.installations.fromEnv=JAVA_LTS_HOME,JAVA_CURRENT_HOME" >> /home/gradle/.gradle/gradle.properties

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
ENV JAVA_LTS_HOME=/opt/java/graalvm25
ENV JAVA_CURRENT_HOME=/opt/java/graalvm25
RUN set -o errexit -o nounset \
    && mkdir /opt/java \
    \
    && echo "Downloading LTS Liberica NIK" \
    && JAVA_LTS_VERSION=25.0.4.1+2 \
    && LIBERICA_NIK_LTS_AMD64_DOWNLOAD_SHA256=66f1fb47df32c7c81e0a1adca5546ddcf208b31311d95638e2fc38e8fa610a21 \
    && LIBERICA_NIK_LTS_AARCH64_DOWNLOAD_SHA256=9ebc5f8b6fbd3a17b762e416ea267f3b239b0c91ff020572d1c6753aaaaa696b \
    && ARCHITECTURE=$(dpkg --print-architecture) \
    && if [ "${ARCHITECTURE}" = "amd64" ]; then LIBERICA_NIK_ARCHITECTURE=amd64; fi \
    && if [ "${ARCHITECTURE}" = "arm64" ]; then LIBERICA_NIK_ARCHITECTURE=aarch64; fi \
    && LIBERICA_NIK_LTS_RELEASE_TAG=25.0.4.1+1-25.0.4.1+2 \
    && LIBERICA_NIK_LTS_VERSION=25.0.4.1+1 \
    && LIBERICA_NIK_PKG=https://github.com/bell-sw/LibericaNIK/releases/download/${LIBERICA_NIK_LTS_RELEASE_TAG}/bellsoft-liberica-vm-openjdk${JAVA_LTS_VERSION}-${LIBERICA_NIK_LTS_VERSION}-linux-${LIBERICA_NIK_ARCHITECTURE}.tar.gz \
    && wget --no-verbose --output-document=liberica-nik.tar.gz "${LIBERICA_NIK_PKG}" \
    \
    && echo "Checking LTS Liberica NIK download hash" \
    && if [ "${ARCHITECTURE}" = "amd64" ]; then LIBERICA_NIK_DOWNLOAD_SHA256="${LIBERICA_NIK_LTS_AMD64_DOWNLOAD_SHA256}"; fi \
    && if [ "${ARCHITECTURE}" = "arm64" ]; then LIBERICA_NIK_DOWNLOAD_SHA256="${LIBERICA_NIK_LTS_AARCH64_DOWNLOAD_SHA256}"; fi \
    && echo "${LIBERICA_NIK_DOWNLOAD_SHA256} *liberica-nik.tar.gz" | sha256sum --check - \
    \
    && echo "Installing LTS Liberica NIK" \
    && mkdir "${JAVA_LTS_HOME}" \
    && tar --extract --gunzip --file liberica-nik.tar.gz --strip-components=1 --directory "${JAVA_LTS_HOME}" \
    && rm liberica-nik.tar.gz \
    \
    && echo "Downloading current Liberica NIK" \
    && JAVA_CURRENT_VERSION=25.0.4.1+2 \
    && LIBERICA_NIK_CURRENT_AMD64_DOWNLOAD_SHA256=66f1fb47df32c7c81e0a1adca5546ddcf208b31311d95638e2fc38e8fa610a21 \
    && LIBERICA_NIK_CURRENT_AARCH64_DOWNLOAD_SHA256=9ebc5f8b6fbd3a17b762e416ea267f3b239b0c91ff020572d1c6753aaaaa696b \
    && if [ "${JAVA_LTS_VERSION}" != "${JAVA_CURRENT_VERSION}" ]; then \
      ARCHITECTURE=$(dpkg --print-architecture) \
      && if [ "${ARCHITECTURE}" = "amd64" ]; then LIBERICA_NIK_ARCHITECTURE=amd64; fi \
      && if [ "${ARCHITECTURE}" = "arm64" ]; then LIBERICA_NIK_ARCHITECTURE=aarch64; fi \
      && LIBERICA_NIK_CURRENT_RELEASE_TAG=25.0.4.1+1-25.0.4.1+2 \
      && LIBERICA_NIK_CURRENT_VERSION=25.0.4.1+1 \
      && LIBERICA_NIK_PKG=https://github.com/bell-sw/LibericaNIK/releases/download/${LIBERICA_NIK_CURRENT_RELEASE_TAG}/bellsoft-liberica-vm-openjdk${JAVA_CURRENT_VERSION}-${LIBERICA_NIK_CURRENT_VERSION}-linux-${LIBERICA_NIK_ARCHITECTURE}.tar.gz \
      && wget --no-verbose --output-document=liberica-nik.tar.gz "${LIBERICA_NIK_PKG}" \
      \
      && echo "Checking current Liberica NIK download hash" \
      && if [ "${ARCHITECTURE}" = "amd64" ]; then LIBERICA_NIK_DOWNLOAD_SHA256="${LIBERICA_NIK_CURRENT_AMD64_DOWNLOAD_SHA256}"; fi \
      && if [ "${ARCHITECTURE}" = "arm64" ]; then LIBERICA_NIK_DOWNLOAD_SHA256="${LIBERICA_NIK_CURRENT_AARCH64_DOWNLOAD_SHA256}"; fi \
      && echo "${LIBERICA_NIK_DOWNLOAD_SHA256} *liberica-nik.tar.gz" | sha256sum --check - \
      \
      && echo "Installing current Liberica NIK" \
      && mkdir "${JAVA_CURRENT_HOME}" \
      && tar --extract --gunzip --file liberica-nik.tar.gz --strip-components=1 --directory "${JAVA_CURRENT_HOME}" \
      && rm liberica-nik.tar.gz; \
    fi \
    \
    && echo "Default Java to LTS Liberica NIK" \
    && ln --symbolic "${JAVA_LTS_HOME}" /opt/java/graalvm \
    && for bin in "$JAVA_LTS_HOME/bin/"*; do \
        base="$(basename "$bin")"; \
        [ ! -e "/usr/bin/$base" ]; \
        update-alternatives --install "/usr/bin/${base}" "${base}" "${bin}" 1; \
    done \
    \
    && echo "Testing Liberica NIK installation" \
    && java --version \
    && javac --version \
    && native-image --version

ENV GRADLE_VERSION=9.8.2
ARG GRADLE_DOWNLOAD_SHA256=21bd5da2de49b642904077f38c0efdc7778e92b3ed0889392dca61b97e389607
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
