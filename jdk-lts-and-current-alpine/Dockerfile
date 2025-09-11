FROM eclipse-temurin:21-jdk-alpine

COPY --from=eclipse-temurin:24-jdk-alpine /opt/java/openjdk /opt/java/openjdk24
RUN set -o errexit -o nounset \
    && ln -s /opt/java/openjdk /opt/java/openjdk21
ENV JAVA_CURRENT_HOME=/opt/java/openjdk24
ENV JAVA_LTS_HOME=/opt/java/openjdk21

CMD ["gradle"]

ENV GRADLE_HOME=/opt/gradle

RUN set -o errexit -o nounset \
    && echo "Adding gradle user and group" \
    && addgroup --system --gid 1000 gradle \
    && adduser --system --ingroup gradle --uid 1000 --shell /bin/ash gradle \
    && mkdir /home/gradle/.gradle \
    && chown -R gradle:gradle /home/gradle \
    \
    && echo "Symlinking root Gradle cache to gradle Gradle cache" \
    && ln -s /home/gradle/.gradle /root/.gradle \
   \
   && echo "Ensuring Gradle detects installed JDKs" \
   && echo "org.gradle.java.installations.auto-detect=false" > /home/gradle/.gradle/gradle.properties \
   && echo "org.gradle.java.installations.auto-download=false" >> /home/gradle/.gradle/gradle.properties \
   && echo "org.gradle.java.installations.fromEnv=JAVA_LTS_HOME,JAVA_CURRENT_HOME" >> /home/gradle/.gradle/gradle.properties

VOLUME /home/gradle/.gradle

WORKDIR /home/gradle

RUN set -o errexit -o nounset \
    && apk add --no-cache \
      # common utilities
      curl \
      make \
      \
      # VCSes
      breezy \
      py3-tzlocal \
      git \
      git-lfs \
      mercurial \
      subversion \
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
    && echo "${GRADLE_DOWNLOAD_SHA256} *gradle.zip" | sha256sum -c - \
    \
    && echo "Installing Gradle" \
    && unzip gradle.zip \
    && rm gradle.zip \
    && mv "gradle-${GRADLE_VERSION}" "${GRADLE_HOME}/" \
    && ln -s "${GRADLE_HOME}/bin/gradle" /usr/bin/gradle

USER gradle

RUN set -o errexit -o nounset \
    && echo "Testing Gradle installation" \
    && gradle --version

USER root
