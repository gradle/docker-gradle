#!/usr/bin/env bash
set -o errexit -o nounset -o pipefail

image="${1}"
expectedGradleVersion="${2}"

if [[ $(id -u) -eq "1000" ]]; then
    user="gradle"
    home="/home/gradle"
else
    user="root"
    home="/root"
fi

version=$(docker run --user "${user}" --rm "${image}" gradle --version --quiet | grep --extended-regexp "^Gradle .+$" | cut -d ' ' -f2)
if [[ "${version}" != "${expectedGradleVersion}" ]]; then
    echo "version '${version}' does not match expected version '${expectedGradleVersion}'" >&2
    exit 1
fi

echo "Building Graal project"

blockedCerts="$(cd "$(dirname "${BASH_SOURCE[0]}")/../blocked-certs" && pwd)"
case "$(uname -s)" in
  CYGWIN*|MINGW32*|MSYS*|MINGW*)
    pwd=$(cygpath --windows "${PWD}")
    blockedCerts=$(cygpath --windows "${blockedCerts}")
    ;;
  *)
    pwd="${PWD}"
    ;;
esac
if [[ $(docker run --user "${user}" --rm --volume "${pwd}:${home}/project" --workdir "${home}/project" "${image}" gradle clean nativeCompile | grep "BUILD SUCCESSFUL") == "" ]]; then
    echo "Test failed" >&2
    exit 1
fi

echo "Checking blocked certificates"

if ! docker run --user "${user}" --rm --volume "${blockedCerts}:/blocked-certs:ro" "${image}" sh /blocked-certs/test/check.sh; then
    echo "Test failed" >&2
    exit 1
fi

echo "All tests succeeded"
