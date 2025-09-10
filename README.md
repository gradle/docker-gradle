# Gradle Docker Image

[![Project Status: Active](https://www.repostatus.org/badges/latest/active.svg)](https://www.repostatus.org/#active)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](/LICENSE)
[![Build status](https://github.com/gradle/docker-gradle/workflows/GitHub%20CI/badge.svg)](https://github.com/gradle/docker-gradle/actions?query=workflow%3A%22GitHub+CI%22)

The official Docker image for [Gradle](https://gradle.org/).
Maintained by the [Gradle team](https://github.com/gradle/docker-gradle) as an [Official Image](https://github.com/docker-library/official-images). Thanks to [@keeganwitt](https://github.com/keeganwitt) for his years of stewardship.

[Gradle](https://gradle.org/) is a fast, dependable, and adaptable open-source build automation tool with an elegant and extensible declarative build language.

## Supported Tags

- **JDK 8** → [`jdk8`, `jdk8-jammy`](https://github.com/gradle/docker-gradle/blob/8/jdk8-jammy/Dockerfile), [`jdk8-corretto`](https://github.com/gradle/docker-gradle/blob/8/jdk8-corretto/Dockerfile), [`jdk8-ubi9`](https://github.com/gradle/docker-gradle/tree/8/jdk8-ubi9/Dockerfile)
- **JDK 11** → [`jdk11`, `jdk11-noble`](https://github.com/gradle/docker-gradle/tree/8/jdk11-noble/Dockerfile), [`jdk11-jammy`](https://github.com/gradle/docker-gradle/tree/8/jdk11-jammy/Dockerfile), [`jdk11-alpine`](https://github.com/gradle/docker-gradle/tree/8/jdk11-alpine/Dockerfile), [`jdk11-corretto`](https://github.com/gradle/docker-gradle/tree/8/jdk11-corretto/Dockerfile), [`jdk11-ubi9`](https://github.com/gradle/docker-gradle/tree/8/jdk11-ubi9/Dockerfile)
- **JDK 17** → [`jdk17`, `jdk17-noble`](jdk17-noble/Dockerfile), [`jdk17-jammy`](jdk17-jammy/Dockerfile), [`jdk17-alpine`](jdk17-alpine/Dockerfile), [`jdk17-corretto`](jdk17-corretto/Dockerfile), [`jdk17-ubi9`](jdk17-ubi9/Dockerfile), [`jdk17-noble-graal`](jdk17-noble-graal/Dockerfile)
- **JDK 21 (LTS)** → [`jdk21`, `jdk21-noble`, `latest`](jdk21-noble/Dockerfile), [`jdk21-jammy`](jdk21-jammy/Dockerfile), [`jdk21-alpine`, `alpine`](jdk21-alpine/Dockerfile), [`jdk21-corretto`, `corretto`](jdk21-corretto/Dockerfile), [`jdk21-ubi9`, `ubi`](jdk21-ubi9/Dockerfile), [`jdk21-graal`](jdk21-noble-graal/Dockerfile)
- **JDK 24 (Current)** → [`jdk24`, `jdk24-noble`](jdk24/Dockerfile), [`jdk24-alpine`](jdk24-alpine/Dockerfile), [`jdk24-corretto`](jdk24-corretto/Dockerfile), [`jdk24-graal`](jdk24-noble-graal/Dockerfile)

See all tags on [Docker Hub](https://hub.docker.com/_/gradle/tags).

### Combo images

Combo images are images where two different JDK versions are made available to Gradle: the latest LTS JDK and the latest (LTS or non-LTS) JDK. Gradle runs on the LTS JDK, while toolchains can target the latest JDK.

- **Combo Images** → [`jdk-lts-and-current`](jdk-lts-and-current/Dockerfile), [`jdk-lts-and-current-alpine`](jdk-lts-and-current-alpine/Dockerfile), [`jdk-lts-and-current-corretto`](jdk-lts-and-current-corretto/Dockerfile), [`jdk-lts-and-current-graal`](jdk-lts-and-current-graal/Dockerfile)

To achieve this, the following appears in the  `/home/gradle/.gradle/gradle.properties` file of the image:

```properties
org.gradle.java.installations.auto-detect=false
org.gradle.java.installations.auto-download=false
org.gradle.java.installations.fromEnv=JAVA_LTS_HOME,JAVA_CURRENT_HOME
```

Available environment variables:

- `JAVA_LTS_HOME` → path to the latest LTS JDK
- `JAVA_CURRENT_HOME` → path to the latest current JDK

These may point to the same path if the latest JDK is an LTS release.

## Usage

### Build a Gradle project

```bash
docker run --rm -u gradle \
  -v "$PWD":/home/gradle/project \
  -w /home/gradle/project \
  gradle:latest gradle <task>
```

Replace `<task>` with your desired Gradle task, e.g., `build`.

### Reusing the Gradle User Home

To persist the [Gradle User Home](https://docs.gradle.org/current/userguide/directory_layout.html#dir:gradle_user_home) (including Gradle caches) between runs:

```bash
docker volume create --name gradle-cache
docker run --rm -u gradle \
  -v gradle-cache:/home/gradle/.gradle \
  -v "$PWD":/home/gradle/project \
  -w /home/gradle/project gradle:latest gradle build
```

Note that sharing between concurrently running containers doesn't work currently
(see [#851](https://github.com/gradle/gradle/issues/851)).

Currently, it is [not possible](https://github.com/moby/moby/issues/3465) to override the volume declaration of the parent.
If you are using this image as a base image and want the Gradle cache to be written into the next layer, you will need to use a new user (or use the `--gradle-user-home`/`-g` argument) so that a new cache is created that isn't mounted to a volume.

## License

[Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0).

© [Gradle Inc.](https://gradle.com) 2025
