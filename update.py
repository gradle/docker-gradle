#!/usr/bin/env python3
import requests
import re
import os
import sys
import hashlib

def get_gradle_version(base_version):
    response = requests.get(f"https://services.gradle.org/versions/{base_version}", timeout=10)
    response.raise_for_status()
    versions = response.json()
    # Filter versions
    filtered_versions = [
        v['version'] for v in versions
        if not v['snapshot'] and not v['nightly'] and not v['broken'] and v['milestoneFor'] == "" and v['rcFor'] == ""
    ]
    # Version sort
    filtered_versions.sort(key=lambda s: [int(u) for u in s.split('.')])
    if not filtered_versions:
        raise RuntimeError(
            f"No stable Gradle versions found for base version '{base_version}' "
            f"from https://services.gradle.org/versions/{base_version}"
        )
    return filtered_versions[-1]

def calculate_sha256(url):
    sha256_hash = hashlib.sha256()
    with requests.get(url, stream=True, timeout=300) as r:
        r.raise_for_status()
        for chunk in r.iter_content(chunk_size=8192):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def get_sha256(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text.strip()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404 and url.endswith(".sha256"):
            binary_url = url[:-7]
            print(f"SHA256 file not found at {url}. Calculating from {binary_url}...", file=sys.stderr)
            return calculate_sha256(binary_url)
        raise

def get_graalvm_info(jdk_version):
    response = requests.get("https://api.github.com/repos/graalvm/graalvm-ce-builds/releases?per_page=20&page=1", timeout=10)
    response.raise_for_status()
    releases = response.json()

    tag_prefix = f"jdk-{jdk_version}"
    matching_releases = [r for r in releases if tag_prefix in r['tag_name']]
    if not matching_releases:
        raise Exception(f"No GraalVM release found for JDK {jdk_version}")

    tag_name = matching_releases[0]['tag_name']
    version = tag_name.replace("jdk-", "")

    return version

def update_file(filepath, pattern, replacement):
    if not os.path.exists(filepath):
        print(f"Warning: target file '{filepath}' does not exist. Skipping update.", file=sys.stderr)
        return
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    new_content = re.sub(pattern, replacement, content, flags=re.MULTILINE)

    if content != new_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)

def fetch_graalvm_release_info(jdk_version):
    version = get_graalvm_info(jdk_version)
    amd64_sha = get_sha256(f"https://github.com/graalvm/graalvm-ce-builds/releases/download/jdk-{version}/graalvm-community-jdk-{version}_linux-x64_bin.tar.gz.sha256")
    aarch64_sha = get_sha256(f"https://github.com/graalvm/graalvm-ce-builds/releases/download/jdk-{version}/graalvm-community-jdk-{version}_linux-aarch64_bin.tar.gz.sha256")

    print(f"Latest Graal {jdk_version} version is {version}")
    print(f"Graal {jdk_version} AMD64 hash is {amd64_sha}")
    print(f"Graal {jdk_version} AARCH64 hash is {aarch64_sha}")
    print()

    return version, amd64_sha, aarch64_sha

def update_graalvm_dockerfiles(dir_names, version, amd64_sha, aarch64_sha, env_prefix=""):
    for dir_name in dir_names:
        filepath = os.path.join(dir_name, "Dockerfile")
        if env_prefix:
            update_file(filepath, rf"JAVA_{env_prefix}_VERSION=\S+", f"JAVA_{env_prefix}_VERSION={version}")
            update_file(filepath, rf"GRAALVM_{env_prefix}_AMD64_DOWNLOAD_SHA256=\S+", f"GRAALVM_{env_prefix}_AMD64_DOWNLOAD_SHA256={amd64_sha}")
            update_file(filepath, rf"GRAALVM_{env_prefix}_AARCH64_DOWNLOAD_SHA256=\S+", f"GRAALVM_{env_prefix}_AARCH64_DOWNLOAD_SHA256={aarch64_sha}")
        else:
            update_file(filepath, r"ENV JAVA_VERSION=\S+", f"ENV JAVA_VERSION={version}")
            update_file(filepath, r"GRAALVM_AMD64_DOWNLOAD_SHA256=\S+", f"GRAALVM_AMD64_DOWNLOAD_SHA256={amd64_sha}")
            update_file(filepath, r"GRAALVM_AARCH64_DOWNLOAD_SHA256=\S+", f"GRAALVM_AARCH64_DOWNLOAD_SHA256={aarch64_sha}")

def main():
    version_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'version.txt')
    if os.path.exists(version_file):
        with open(version_file, 'r', encoding='utf-8') as f:
            base_version_str = f.read().strip()
    else:
        print(f"Error: {version_file} not found. Please ensure the script is run from the correct directory or the file exists.", file=sys.stderr)
        sys.exit(1)

    base_version = int(base_version_str)
    gradle_version = get_gradle_version(base_version_str)

    print(f"Base version: {base_version_str}")
    print(f"Latest version: {gradle_version}")

    gradle_sha = get_sha256(f"https://downloads.gradle.org/distributions/gradle-{gradle_version}-bin.zip.sha256")

    # Update all Dockerfiles
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file == 'Dockerfile':
                filepath = os.path.join(root, file)
                update_file(filepath, r"ENV GRADLE_VERSION=.+$", f"ENV GRADLE_VERSION={gradle_version}")
                update_file(filepath, r"GRADLE_DOWNLOAD_SHA256=.+$", f"GRADLE_DOWNLOAD_SHA256={gradle_sha}")

    # Update CI workflow
    update_file(".github/workflows/ci.yaml", r"expectedGradleVersion: .+$", f"expectedGradleVersion: '{gradle_version}'")

    if base_version < 7:
        return

    # GraalVM updates
    graal17_version, graal17_amd64_sha, graal17_aarch64_sha = fetch_graalvm_release_info("17")
    update_graalvm_dockerfiles(["jdk17-noble-graal", "jdk17-jammy-graal"], graal17_version, graal17_amd64_sha, graal17_aarch64_sha)

    if base_version < 8:
        return

    graal21_version, graal21_amd64_sha, graal21_aarch64_sha = fetch_graalvm_release_info("21")
    update_graalvm_dockerfiles(["jdk21-noble-graal", "jdk21-jammy-graal"], graal21_version, graal21_amd64_sha, graal21_aarch64_sha)

    if base_version < 9:
        graal24_version, graal24_amd64_sha, graal24_aarch64_sha = fetch_graalvm_release_info("24")
        update_graalvm_dockerfiles(["jdk24-noble-graal"], graal24_version, graal24_amd64_sha, graal24_aarch64_sha)

        update_graalvm_dockerfiles(["jdk-lts-and-current-graal"], graal21_version, graal21_amd64_sha, graal21_aarch64_sha, env_prefix="21")
        update_graalvm_dockerfiles(["jdk-lts-and-current-graal"], graal24_version, graal24_amd64_sha, graal24_aarch64_sha, env_prefix="24")
    else:
        graal25_version, graal25_amd64_sha, graal25_aarch64_sha = fetch_graalvm_release_info("25")
        update_graalvm_dockerfiles(["jdk25-noble-graal"], graal25_version, graal25_amd64_sha, graal25_aarch64_sha)

        update_graalvm_dockerfiles(["jdk-lts-and-current-graal"], graal25_version, graal25_amd64_sha, graal25_aarch64_sha, env_prefix="LTS")
        update_graalvm_dockerfiles(["jdk-lts-and-current-graal"], graal25_version, graal25_amd64_sha, graal25_aarch64_sha, env_prefix="CURRENT")
if __name__ == "__main__":
    main()
