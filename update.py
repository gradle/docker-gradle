#!/usr/bin/env python3
import requests
import re
import os
import sys
import hashlib
from urllib.parse import urlparse

def github_headers(url):
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        return {}
    host = urlparse(url).hostname or ""
    if host == "api.github.com" or host == "github.com" or host.endswith(".github.com") or host == "objects.githubusercontent.com":
        return {"Authorization": f"Bearer {token}"}
    return {}

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
    with requests.get(url, stream=True, timeout=300, headers=github_headers(url)) as r:
        r.raise_for_status()
        for chunk in r.iter_content(chunk_size=8192):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def get_sha256(url):
    try:
        response = requests.get(url, timeout=10, headers=github_headers(url))
        response.raise_for_status()
        return response.text.strip()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404 and url.endswith(".sha256"):
            binary_url = url[:-7]
            print(f"SHA256 file not found at {url}. Calculating from {binary_url}...", file=sys.stderr)
            return calculate_sha256(binary_url)
        raise

GRAALVM_RELEASES_URL = "https://api.github.com/repos/graalvm/graalvm-ce-builds/releases?per_page=100"
GRAALVM_ASSET_PATTERN = re.compile(
    r"^graalvm-community-jdk-(?P<artifact_version>.+)_linux-(?P<architecture>x64|aarch64)_bin\.tar\.gz$"
)
GRAALVM_TAG_PATTERN = re.compile(r"^(?:jdk|graal)-(?P<version>\d+(?:\.\d+)+)$")

def get_graalvm_info(jdk_version):
    matching_releases = []
    url = f"{GRAALVM_RELEASES_URL}&page=1"
    while url:
        response = requests.get(url, timeout=10, headers=github_headers(url))
        response.raise_for_status()
        releases = response.json()
        url = response.links.get('next', {}).get('url')
        for release in releases:
            if release.get('draft') or release.get('prerelease'):
                continue
            tag_match = GRAALVM_TAG_PATTERN.match(release['tag_name'])
            if not tag_match:
                continue
            matching_assets = {}
            for asset in release.get('assets', []):
                match = GRAALVM_ASSET_PATTERN.match(asset['name'])
                if not match:
                    continue
                artifact_version = match.group('artifact_version')
                jdk_release_version = artifact_version.rsplit('-', 1)[-1]
                if jdk_release_version == jdk_version or jdk_release_version.startswith(f"{jdk_version}."):
                    matching_assets[match.group('architecture')] = (asset, artifact_version, jdk_release_version)
            if {'x64', 'aarch64'} <= matching_assets.keys():
                amd64_asset, artifact_version, jdk_release_version = matching_assets['x64']
                aarch64_asset, aarch64_artifact_version, aarch64_jdk_release_version = matching_assets['aarch64']
                if artifact_version != aarch64_artifact_version or jdk_release_version != aarch64_jdk_release_version:
                    continue
                version = tuple(int(part) for part in tag_match.group('version').split('.'))
                matching_releases.append((version, release['tag_name'], artifact_version, jdk_release_version, amd64_asset, aarch64_asset))
    if not matching_releases:
        raise Exception(f"No GraalVM release found for JDK {jdk_version}")

    _, tag_name, artifact_version, jdk_release_version, amd64_asset, aarch64_asset = max(matching_releases, key=lambda release: release[0])
    return tag_name, artifact_version, jdk_release_version, amd64_asset['browser_download_url'], aarch64_asset['browser_download_url']

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

BLOCKED_CERTS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "blocked-certs", "blocked.certs")
BLOCKED_CERTS_PATTERN = r'^([ \t]*&& BLOCKED_CERTS_SHA256=" \\\n)(?:[^"\n]*\\\n)*([ \t]*" \\)$'

def read_blocked_certs():
    with open(BLOCKED_CERTS_FILE, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    if not lines or lines[0] != "Algorithm=SHA-256":
        raise RuntimeError(f"{BLOCKED_CERTS_FILE} must start with 'Algorithm=SHA-256'")
    fingerprints = lines[1:]
    for fingerprint in fingerprints:
        if not re.fullmatch(r"[0-9A-F]{64}", fingerprint):
            raise RuntimeError(f"{BLOCKED_CERTS_FILE} has an invalid SHA-256 fingerprint: '{fingerprint}'")
    if len(set(fingerprints)) != len(fingerprints):
        raise RuntimeError(f"{BLOCKED_CERTS_FILE} has duplicate fingerprints")
    return sorted(fingerprints)

def update_blocked_certs_dockerfiles():
    fingerprints = read_blocked_certs()
    for dir_name in sorted(os.listdir('.')):
        filepath = os.path.join(dir_name, "Dockerfile")
        if not dir_name.startswith("jdk") or not os.path.exists(filepath):
            continue
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        if len(re.findall(BLOCKED_CERTS_PATTERN, content, flags=re.MULTILINE)) != 1:
            raise RuntimeError(f"{filepath} must have exactly one BLOCKED_CERTS_SHA256 block")
        update_file(filepath, BLOCKED_CERTS_PATTERN,
                    lambda m: m.group(1) + "".join(f"        {fingerprint} \\\n" for fingerprint in fingerprints) + m.group(2))
    print(f"Blocked certificates: {len(fingerprints)} fingerprints from {BLOCKED_CERTS_FILE}")
    print()

def fetch_graalvm_release_info(jdk_version):
    tag_name, artifact_version, jdk_release_version, amd64_url, aarch64_url = get_graalvm_info(jdk_version)
    amd64_sha = get_sha256(f"{amd64_url}.sha256")
    aarch64_sha = get_sha256(f"{aarch64_url}.sha256")

    print(f"Latest Graal {jdk_version} release is {tag_name}")
    print(f"Graal {jdk_version} AMD64 hash is {amd64_sha}")
    print(f"Graal {jdk_version} AARCH64 hash is {aarch64_sha}")
    print()

    return jdk_release_version, tag_name, artifact_version, amd64_sha, aarch64_sha

def update_graalvm_dockerfiles(dir_names, version, tag_name, artifact_version, amd64_sha, aarch64_sha, env_prefix=""):
    for dir_name in dir_names:
        filepath = os.path.join(dir_name, "Dockerfile")
        if env_prefix:
            java_version = f"${{JAVA_{env_prefix}_VERSION}}"
            update_file(filepath, rf"JAVA_{env_prefix}_VERSION=\S+", f"JAVA_{env_prefix}_VERSION={version}")
            update_file(filepath, rf"GRAALVM_{env_prefix}_AMD64_DOWNLOAD_SHA256=\S+", f"GRAALVM_{env_prefix}_AMD64_DOWNLOAD_SHA256={amd64_sha}")
            update_file(filepath, rf"GRAALVM_{env_prefix}_AARCH64_DOWNLOAD_SHA256=\S+", f"GRAALVM_{env_prefix}_AARCH64_DOWNLOAD_SHA256={aarch64_sha}")
        else:
            java_version = "${JAVA_VERSION}"
            update_file(filepath, r"ENV JAVA_VERSION=\S+", f"ENV JAVA_VERSION={version}")
            update_file(filepath, r"GRAALVM_AMD64_DOWNLOAD_SHA256=\S+", f"GRAALVM_AMD64_DOWNLOAD_SHA256={amd64_sha}")
            update_file(filepath, r"GRAALVM_AARCH64_DOWNLOAD_SHA256=\S+", f"GRAALVM_AARCH64_DOWNLOAD_SHA256={aarch64_sha}")
        package_pattern = r"(?:GRAALVM_RELEASE_TAG=\S+ \\\n\s*&& GRAALVM_ARTIFACT_(?:VERSION|PREFIX)=\S+ \\\n\s*&& )?GRAALVM_PKG=https://github\.com/graalvm/graalvm-ce-builds/releases/download/[^\s]+"
        if tag_name == f"jdk-{version}" and artifact_version == version:
            package_replacement = f"GRAALVM_PKG=https://github.com/graalvm/graalvm-ce-builds/releases/download/jdk-{java_version}/graalvm-community-jdk-{java_version}_${{GRAALVM_ARCHITECTURE}}_bin.tar.gz"
        else:
            package_replacement = f"GRAALVM_RELEASE_TAG={tag_name} \\\n    && GRAALVM_ARTIFACT_VERSION={artifact_version} \\\n    && GRAALVM_PKG=https://github.com/graalvm/graalvm-ce-builds/releases/download/${{GRAALVM_RELEASE_TAG}}/graalvm-community-jdk-${{GRAALVM_ARTIFACT_VERSION}}_${{GRAALVM_ARCHITECTURE}}_bin.tar.gz"
        update_file(filepath, package_pattern, package_replacement)

def main():
    version_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'version.txt')
    if os.path.exists(version_file):
        with open(version_file, 'r', encoding='utf-8') as f:
            base_version_str = f.read().strip()
    else:
        print(f"Error: {version_file} not found. Please ensure the script is run from the correct directory or the file exists.", file=sys.stderr)
        sys.exit(1)

    base_version = int(base_version_str)

    update_blocked_certs_dockerfiles()

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
    graal17_info = fetch_graalvm_release_info("17")
    update_graalvm_dockerfiles(["jdk17-noble-graal", "jdk17-resolute-graal", "jdk17-jammy-graal"], *graal17_info)

    if base_version < 8:
        return

    graal21_info = fetch_graalvm_release_info("21")
    update_graalvm_dockerfiles(["jdk21-noble-graal", "jdk21-resolute-graal", "jdk21-jammy-graal"], *graal21_info)

    if base_version < 9:
        graal24_info = fetch_graalvm_release_info("24")
        update_graalvm_dockerfiles(["jdk24-noble-graal"], *graal24_info)

        update_graalvm_dockerfiles(["jdk-lts-and-current-graal"], *graal21_info, env_prefix="21")
        update_graalvm_dockerfiles(["jdk-lts-and-current-graal"], *graal24_info, env_prefix="24")
    else:
        graal25_info = fetch_graalvm_release_info("25")
        update_graalvm_dockerfiles(["jdk25-noble-graal", "jdk25-resolute-graal"], *graal25_info)

        update_graalvm_dockerfiles(["jdk-lts-and-current-graal"], *graal25_info, env_prefix="LTS")
        update_graalvm_dockerfiles(["jdk-lts-and-current-graal"], *graal25_info, env_prefix="CURRENT")

if __name__ == "__main__":
    main()
