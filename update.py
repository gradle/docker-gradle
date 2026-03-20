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
    graal17_version = get_graalvm_info("17")
    graal17_amd64_sha = get_sha256(f"https://github.com/graalvm/graalvm-ce-builds/releases/download/jdk-{graal17_version}/graalvm-community-jdk-{graal17_version}_linux-x64_bin.tar.gz.sha256")
    graal17_aarch64_sha = get_sha256(f"https://github.com/graalvm/graalvm-ce-builds/releases/download/jdk-{graal17_version}/graalvm-community-jdk-{graal17_version}_linux-aarch64_bin.tar.gz.sha256")

    for dir_name in ["jdk17-noble-graal", "jdk17-jammy-graal"]:
        filepath = os.path.join(dir_name, "Dockerfile")
        update_file(filepath, r"ENV JAVA_VERSION=\S+", f"ENV JAVA_VERSION={graal17_version}")
        update_file(filepath, r"GRAALVM_AMD64_DOWNLOAD_SHA256=\S+", f"GRAALVM_AMD64_DOWNLOAD_SHA256={graal17_amd64_sha}")
        update_file(filepath, r"GRAALVM_AARCH64_DOWNLOAD_SHA256=\S+", f"GRAALVM_AARCH64_DOWNLOAD_SHA256={graal17_aarch64_sha}")

    print(f"Latest Graal 17 version is {graal17_version}")
    print(f"Graal 17 AMD64 hash is {graal17_amd64_sha}")
    print(f"Graal 17 AARCH64 hash is {graal17_aarch64_sha}")
    print()

    if base_version < 8:
        return

    graal21_version = get_graalvm_info("21")
    graal21_amd64_sha = get_sha256(f"https://github.com/graalvm/graalvm-ce-builds/releases/download/jdk-{graal21_version}/graalvm-community-jdk-{graal21_version}_linux-x64_bin.tar.gz.sha256")
    graal21_aarch64_sha = get_sha256(f"https://github.com/graalvm/graalvm-ce-builds/releases/download/jdk-{graal21_version}/graalvm-community-jdk-{graal21_version}_linux-aarch64_bin.tar.gz.sha256")

    for dir_name in ["jdk21-noble-graal", "jdk21-jammy-graal"]:
        filepath = os.path.join(dir_name, "Dockerfile")
        update_file(filepath, r"ENV JAVA_VERSION=\S+", f"ENV JAVA_VERSION={graal21_version}")
        update_file(filepath, r"GRAALVM_AMD64_DOWNLOAD_SHA256=\S+", f"GRAALVM_AMD64_DOWNLOAD_SHA256={graal21_amd64_sha}")
        update_file(filepath, r"GRAALVM_AARCH64_DOWNLOAD_SHA256=\S+", f"GRAALVM_AARCH64_DOWNLOAD_SHA256={graal21_aarch64_sha}")

    print(f"Latest Graal 21 version is {graal21_version}")
    print(f"Graal 21 AMD64 hash is {graal21_amd64_sha}")
    print(f"Graal 21 AARCH64 hash is {graal21_aarch64_sha}")
    print()

    if base_version < 9:
        graal24_version = get_graalvm_info("24")
        graal24_amd64_sha = get_sha256(f"https://github.com/graalvm/graalvm-ce-builds/releases/download/jdk-{graal24_version}/graalvm-community-jdk-{graal24_version}_linux-x64_bin.tar.gz.sha256")
        graal24_aarch64_sha = get_sha256(f"https://github.com/graalvm/graalvm-ce-builds/releases/download/jdk-{graal24_version}/graalvm-community-jdk-{graal24_version}_linux-aarch64_bin.tar.gz.sha256")

        for dir_name in ["jdk24-noble-graal"]:
            filepath = os.path.join(dir_name, "Dockerfile")
            update_file(filepath, r"ENV JAVA_VERSION=\S+", f"ENV JAVA_VERSION={graal24_version}")
            update_file(filepath, r"GRAALVM_AMD64_DOWNLOAD_SHA256=\S+", f"GRAALVM_AMD64_DOWNLOAD_SHA256={graal24_amd64_sha}")
            update_file(filepath, r"GRAALVM_AARCH64_DOWNLOAD_SHA256=\S+", f"GRAALVM_AARCH64_DOWNLOAD_SHA256={graal24_aarch64_sha}")

        filepath = os.path.join("jdk-lts-and-current-graal", "Dockerfile")
        update_file(filepath, r"JAVA_21_VERSION=\S+", f"JAVA_21_VERSION={graal21_version}")
        update_file(filepath, r"GRAALVM_21_AMD64_DOWNLOAD_SHA256=\S+", f"GRAALVM_21_AMD64_DOWNLOAD_SHA256={graal21_amd64_sha}")
        update_file(filepath, r"GRAALVM_21_AARCH64_DOWNLOAD_SHA256=\S+", f"GRAALVM_21_AARCH64_DOWNLOAD_SHA256={graal21_aarch64_sha}")
        update_file(filepath, r"JAVA_24_VERSION=\S+", f"JAVA_24_VERSION={graal24_version}")
        update_file(filepath, r"GRAALVM_24_AMD64_DOWNLOAD_SHA256=\S+", f"GRAALVM_24_AMD64_DOWNLOAD_SHA256={graal24_amd64_sha}")
        update_file(filepath, r"GRAALVM_24_AARCH64_DOWNLOAD_SHA256=\S+", f"GRAALVM_24_AARCH64_DOWNLOAD_SHA256={graal24_aarch64_sha}")

        print(f"Latest Graal 24 version is {graal24_version}")
        print(f"Graal 24 AMD64 hash is {graal24_amd64_sha}")
        print(f"Graal 24 AARCH64 hash is {graal24_aarch64_sha}")
        print()
    else:
        graal25_version = get_graalvm_info("25")
        graal25_amd64_sha = get_sha256(f"https://github.com/graalvm/graalvm-ce-builds/releases/download/jdk-{graal25_version}/graalvm-community-jdk-{graal25_version}_linux-x64_bin.tar.gz.sha256")
        graal25_aarch64_sha = get_sha256(f"https://github.com/graalvm/graalvm-ce-builds/releases/download/jdk-{graal25_version}/graalvm-community-jdk-{graal25_version}_linux-aarch64_bin.tar.gz.sha256")

        for dir_name in ["jdk25-noble-graal"]:
            filepath = os.path.join(dir_name, "Dockerfile")
            update_file(filepath, r"ENV JAVA_VERSION=\S+", f"ENV JAVA_VERSION={graal25_version}")
            update_file(filepath, r"GRAALVM_AMD64_DOWNLOAD_SHA256=\S+", f"GRAALVM_AMD64_DOWNLOAD_SHA256={graal25_amd64_sha}")
            update_file(filepath, r"GRAALVM_AARCH64_DOWNLOAD_SHA256=\S+", f"GRAALVM_AARCH64_DOWNLOAD_SHA256={graal25_aarch64_sha}")

        filepath = os.path.join("jdk-lts-and-current-graal", "Dockerfile")
        update_file(filepath, r"JAVA_LTS_VERSION=\S+", f"JAVA_LTS_VERSION={graal25_version}")
        update_file(filepath, r"GRAALVM_LTS_AMD64_DOWNLOAD_SHA256=\S+", f"GRAALVM_LTS_AMD64_DOWNLOAD_SHA256={graal25_amd64_sha}")
        update_file(filepath, r"GRAALVM_LTS_AARCH64_DOWNLOAD_SHA256=\S+", f"GRAALVM_LTS_AARCH64_DOWNLOAD_SHA256={graal25_aarch64_sha}")
        update_file(filepath, r"JAVA_CURRENT_VERSION=\S+", f"JAVA_CURRENT_VERSION={graal25_version}")
        update_file(filepath, r"GRAALVM_CURRENT_AMD64_DOWNLOAD_SHA256=\S+", f"GRAALVM_CURRENT_AMD64_DOWNLOAD_SHA256={graal25_amd64_sha}")
        update_file(filepath, r"GRAALVM_CURRENT_AARCH64_DOWNLOAD_SHA256=\S+", f"GRAALVM_CURRENT_AARCH64_DOWNLOAD_SHA256={graal25_aarch64_sha}")

        print(f"Latest Graal 25 version is {graal25_version}")
        print(f"Graal 25 AMD64 hash is {graal25_amd64_sha}")
        print(f"Graal 25 AARCH64 hash is {graal25_aarch64_sha}")
        print()

if __name__ == "__main__":
    main()
