FROM eclipse-temurin:21-jdk-jammy

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
    && apt-get update \
    && apt-get install --yes --no-install-recommends \
        # common utilities
        make \
        \
        # Dockerfile dependencies
        unzip \
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

ENV GRADLE_VERSION=8.14.3
ARG GRADLE_DOWNLOAD_SHA256=bd71102213493060956ec229d946beee57158dbd89d0e62b91bca0fa2c5f3531
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
