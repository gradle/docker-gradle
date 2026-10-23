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

LIBERICA_NIK_RELEASES_URL = "https://api.github.com/repos/bell-sw/LibericaNIK/releases?per_page=100"
LIBERICA_NIK_ASSET_PATTERN = re.compile(
    r"^bellsoft-liberica-vm-openjdk(?P<java_version>\d+(?:\.\d+)*\+\d+)-"
    r"(?P<nik_version>\d+(?:\.\d+)*\+\d+)-linux-(?P<architecture>amd64|aarch64)\.tar\.gz$"
)

def get_liberica_nik_releases():
    releases = []
    url = LIBERICA_NIK_RELEASES_URL
    while url:
        response = requests.get(url, timeout=30, headers=github_headers(url))
        response.raise_for_status()
        releases.extend(response.json())
        url = response.links.get('next', {}).get('url')
    return releases

def nik_version_key(version):
    release, build = version.split('+')
    parts = [int(part) for part in release.split('.')]
    return tuple(parts + [0] * (4 - len(parts))), int(build)

def get_liberica_nik_info(jdk_version, releases):
    candidates = []
    for release in releases:
        if release.get('draft') or release.get('prerelease'):
            continue
        bundles = {}
        for asset in release.get('assets', []):
            match = LIBERICA_NIK_ASSET_PATTERN.fullmatch(asset['name'])
            if not match:
                continue
            java_version = match['java_version']
            if java_version.split('+')[0].split('.')[0] != jdk_version:
                continue
            nik_version = match['nik_version']
            bundles.setdefault((java_version, nik_version), {})[match['architecture']] = asset
        for (java_version, nik_version), assets in bundles.items():
            if {'amd64', 'aarch64'} <= assets.keys():
                key = (nik_version_key(java_version), nik_version_key(nik_version))
                candidates.append((key, java_version, release['tag_name'], nik_version, assets))
    if not candidates:
        raise RuntimeError(f"No Liberica NIK standard Linux release for both architectures found for JDK {jdk_version}")
    _, java_version, tag_name, nik_version, assets = max(candidates, key=lambda candidate: candidate[0])
    return java_version, tag_name, nik_version, assets

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

def fetch_liberica_nik_release_info(jdk_version, releases):
    java_version, tag_name, nik_version, assets = get_liberica_nik_info(jdk_version, releases)
    hashes = []
    for architecture in ('amd64', 'aarch64'):
        asset = assets[architecture]
        digest = asset.get('digest') or ''
        if re.fullmatch(r'sha256:[0-9a-fA-F]{64}', digest):
            sha = digest.split(':')[1].lower()
        else:
            sha = calculate_sha256(asset['browser_download_url'])
        hashes.append(sha)
    print(f"Latest Liberica NIK for JDK {jdk_version}: {nik_version} (Java {java_version})")
    return java_version, tag_name, nik_version, *hashes

def update_liberica_nik_dockerfiles(dir_names, version, tag_name, nik_version, amd64_sha, aarch64_sha):
    for dir_name in dir_names:
        filepath = os.path.join(dir_name, "Dockerfile")
        for name, value in (
            ("JAVA_VERSION", version),
            ("LIBERICA_NIK_AMD64_DOWNLOAD_SHA256", amd64_sha),
            ("LIBERICA_NIK_AARCH64_DOWNLOAD_SHA256", aarch64_sha),
            ("LIBERICA_NIK_RELEASE_TAG", tag_name),
            ("LIBERICA_NIK_VERSION", nik_version),
        ):
            update_file(filepath, rf"{name}=\S+", f"{name}={value}")

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

    # Liberica NIK updates
    nik_releases = get_liberica_nik_releases()
    nik17_info = fetch_liberica_nik_release_info("17", nik_releases)
    update_liberica_nik_dockerfiles(["jdk17-noble-graal", "jdk17-jammy-graal"], *nik17_info)

    if base_version < 8:
        return

    nik21_info = fetch_liberica_nik_release_info("21", nik_releases)
    update_liberica_nik_dockerfiles(["jdk21-noble-graal", "jdk21-jammy-graal"], *nik21_info)

if __name__ == "__main__":
    main()
