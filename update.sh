#!/usr/bin/env bash
set -o errexit -o nounset -o pipefail

_sed() {
  if sed --version > /dev/null 2>&1; then
    # GNU sed
    sed --regexp-extended --in-place "$@"
  else
    # BSD sed
    sed -Ei '' "$@"
  fi
}

gradleVersion=6.9.4
sha=$(curl --fail --show-error --silent --location "https://downloads.gradle.org/distributions/gradle-${gradleVersion}-bin.zip.sha256")

_sed "s/ENV GRADLE_VERSION=.+$/ENV GRADLE_VERSION=${gradleVersion}/" ./*/Dockerfile
_sed "s/GRADLE_DOWNLOAD_SHA256=.+$/GRADLE_DOWNLOAD_SHA256=${sha}/" ./*/Dockerfile
_sed "s/expectedGradleVersion: .+$/expectedGradleVersion: '${gradleVersion}'/" .github/workflows/ci.yaml

graal17Version=$(curl --silent --location 'https://api.github.com/repos/graalvm/graalvm-ce-builds/releases?per_page=20&page=1' | jq --raw-output 'map(select(.tag_name | contains("jdk-17"))) | .[0].tag_name | sub("jdk-"; "")' | tr -d '\r')
graal17amd64Sha=$(curl --fail --location --silent "https://github.com/graalvm/graalvm-ce-builds/releases/download/jdk-${graal17Version}/graalvm-community-jdk-${graal17Version}_linux-x64_bin.tar.gz" | sha256sum | cut -d' ' -f1)
graal17aarch64Sha=$(curl --fail --location --silent "https://github.com/graalvm/graalvm-ce-builds/releases/download/jdk-${graal17Version}/graalvm-community-jdk-${graal17Version}_linux-aarch64_bin.tar.gz" | sha256sum | cut -d' ' -f1)

_sed "s/JAVA_VERSION=[^ ]+/JAVA_VERSION=${graal17Version}/" ./jdk17-noble-graal/Dockerfile
_sed "s/GRAALVM_AMD64_DOWNLOAD_SHA256=[^ ]+/GRAALVM_AMD64_DOWNLOAD_SHA256=${graal17amd64Sha}/" ./jdk17-noble-graal/Dockerfile
_sed "s/GRAALVM_AARCH64_DOWNLOAD_SHA256=[^ ]+/GRAALVM_AARCH64_DOWNLOAD_SHA256=${graal17aarch64Sha}/" ./jdk17-noble-graal/Dockerfile

_sed "s/JAVA_VERSION=[^ ]+/JAVA_VERSION=${graal17Version}/" ./jdk17-jammy-graal/Dockerfile
_sed "s/GRAALVM_AMD64_DOWNLOAD_SHA256=[^ ]+/GRAALVM_AMD64_DOWNLOAD_SHA256=${graal17amd64Sha}/" ./jdk17-jammy-graal/Dockerfile
_sed "s/GRAALVM_AARCH64_DOWNLOAD_SHA256=[^ ]+/GRAALVM_AARCH64_DOWNLOAD_SHA256=${graal17aarch64Sha}/" ./jdk17-jammy-graal/Dockerfile

graal21Version=$(curl --silent --location 'https://api.github.com/repos/graalvm/graalvm-ce-builds/releases?per_page=20&page=1' | jq --raw-output 'map(select(.tag_name | contains("jdk-21"))) | .[0].tag_name | sub("jdk-"; "")' | tr -d '\r')
graal21amd64Sha=$(curl --fail --location --silent "https://github.com/graalvm/graalvm-ce-builds/releases/download/jdk-${graal21Version}/graalvm-community-jdk-${graal21Version}_linux-x64_bin.tar.gz" | sha256sum | cut -d' ' -f1)
graal21aarch64Sha=$(curl --fail --location --silent "https://github.com/graalvm/graalvm-ce-builds/releases/download/jdk-${graal21Version}/graalvm-community-jdk-${graal21Version}_linux-aarch64_bin.tar.gz" | sha256sum | cut -d' ' -f1)

_sed "s/JAVA_VERSION=[^ ]+/JAVA_VERSION=${graal21Version}/" ./jdk21-noble-graal/Dockerfile
_sed "s/GRAALVM_AMD64_DOWNLOAD_SHA256=[^ ]+/GRAALVM_AMD64_DOWNLOAD_SHA256=${graal21amd64Sha}/" ./jdk21-noble-graal/Dockerfile
_sed "s/GRAALVM_AARCH64_DOWNLOAD_SHA256=[^ ]+/GRAALVM_AARCH64_DOWNLOAD_SHA256=${graal21aarch64Sha}/" ./jdk21-noble-graal/Dockerfile

_sed "s/JAVA_VERSION=[^ ]+/JAVA_VERSION=${graal21Version}/" ./jdk21-jammy-graal/Dockerfile
_sed "s/GRAALVM_AMD64_DOWNLOAD_SHA256=[^ ]+/GRAALVM_AMD64_DOWNLOAD_SHA256=${graal21amd64Sha}/" ./jdk21-jammy-graal/Dockerfile
_sed "s/GRAALVM_AARCH64_DOWNLOAD_SHA256=[^ ]+/GRAALVM_AARCH64_DOWNLOAD_SHA256=${graal21aarch64Sha}/" ./jdk21-jammy-graal/Dockerfile

graal24Version=$( curl --silent --location 'https://api.github.com/repos/graalvm/graalvm-ce-builds/releases?per_page=20&page=1' | jq --raw-output 'map(select(.tag_name | contains("jdk-24"))) | .[0].tag_name | sub("jdk-"; "")' | tr -d '\r')
graal24amd64Sha=$(curl --fail --location --silent "https://github.com/graalvm/graalvm-ce-builds/releases/download/jdk-${graal24Version}/graalvm-community-jdk-${graal24Version}_linux-x64_bin.tar.gz" | sha256sum | cut -d' ' -f1)
graal24aarch64Sha=$(curl --fail --location --silent "https://github.com/graalvm/graalvm-ce-builds/releases/download/jdk-${graal24Version}/graalvm-community-jdk-${graal24Version}_linux-aarch64_bin.tar.gz" | sha256sum | cut -d' ' -f1)

_sed "s/JAVA_VERSION=[^ ]+/JAVA_VERSION=${graal24Version}/" ./jdk24-noble-graal/Dockerfile
_sed "s/GRAALVM_AMD64_DOWNLOAD_SHA256=[^ ]+/GRAALVM_AMD64_DOWNLOAD_SHA256=${graal24amd64Sha}/" ./jdk24-noble-graal/Dockerfile
_sed "s/GRAALVM_AARCH64_DOWNLOAD_SHA256=[^ ]+/GRAALVM_AARCH64_DOWNLOAD_SHA256=${graal24aarch64Sha}/" ./jdk24-noble-graal/Dockerfile

_sed "s/JAVA_21_VERSION=[^ ]+/JAVA_21_VERSION=${graal21Version}/" ./jdk-lts-and-current-graal/Dockerfile
_sed "s/GRAALVM_21_AMD64_DOWNLOAD_SHA256=[^ ]+/GRAALVM_21_AMD64_DOWNLOAD_SHA256=${graal21amd64Sha}/" ./jdk-lts-and-current-graal/Dockerfile
_sed "s/GRAALVM_21_AARCH64_DOWNLOAD_SHA256=[^ ]+/GRAALVM_21_AARCH64_DOWNLOAD_SHA256=${graal21aarch64Sha}/" ./jdk-lts-and-current-graal/Dockerfile
_sed "s/JAVA_24_VERSION=[^ ]+/JAVA_24_VERSION=${graal24Version}/" ./jdk-lts-and-current-graal/Dockerfile
_sed "s/GRAALVM_24_AMD64_DOWNLOAD_SHA256=[^ ]+/GRAALVM_24_AMD64_DOWNLOAD_SHA256=${graal24amd64Sha}/" ./jdk-lts-and-current-graal/Dockerfile
_sed "s/GRAALVM_24_AARCH64_DOWNLOAD_SHA256=[^ ]+/GRAALVM_24_AARCH64_DOWNLOAD_SHA256=${graal24aarch64Sha}/" ./jdk-lts-and-current-graal/Dockerfile

echo "Latest Gradle version is ${gradleVersion}"
echo "Latest Graal 17 version is ${graal17Version}"
echo "Latest Graal 21 version is ${graal21Version}"
echo "Latest Graal 24 version is ${graal24Version}"

echo "Graal 17 AMD64 hash is ${graal17amd64Sha}"
echo "Graal 17 AARCH64 hash is ${graal17aarch64Sha}"
echo "Graal 21 AMD64 hash is ${graal21amd64Sha}"
echo "Graal 21 AARCH64 hash is ${graal21aarch64Sha}"
echo "Graal 24 AMD64 hash is ${graal24amd64Sha}"
echo "Graal 24 AARCH64 hash is ${graal24aarch64Sha}"
