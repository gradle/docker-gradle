FROM eclipse-temurin:21-jdk-noble

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
