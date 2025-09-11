# Gradle Docker Image

[![Project Status: Active](https://www.repostatus.org/badges/latest/active.svg)](https://www.repostatus.org/#active)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](/LICENSE)
[![Build status](https://github.com/gradle/docker-gradle/workflows/GitHub%20CI/badge.svg)](https://github.com/gradle/docker-gradle/actions?query=workflow%3A%22GitHub+CI%22)

The official Docker image for [Gradle](https://gradle.org/).
Maintained by the [Gradle team](https://github.com/gradle/docker-gradle) as an [Official Image](https://github.com/docker-library/official-images). Thanks to [@keeganwitt](https://github.com/keeganwitt) for his years of stewardship.

[Gradle](https://gradle.org/) is a fast, dependable, and adaptable open-source build automation tool with an elegant and extensible declarative build language.

## Supported Tags

- **JDK 8** → [`jdk8`, `jdk8-jammy`](jdk8-jammy/Dockerfile), [`jdk8-corretto`](jdk8-corretto/Dockerfile), [`jdk8-ubi9`](jdk8-ubi9/Dockerfile)
- **JDK 11** → [`jdk11`, `jdk11-jammy`](jdk11-jammy/Dockerfile), [`jdk11-alpine`](jdk11-alpine/Dockerfile), [`jdk11-corretto`](jdk11-corretto/Dockerfile), [`jdk11-ubi9`](jdk11-ubi9/Dockerfile)

See all tags on [Docker Hub](https://hub.docker.com/_/gradle/tags).

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
