#!/usr/bin/env python3
import subprocess
import sys
import os
import re
import argparse


def run_command(command, input_str=None):
    result = subprocess.run(command, input=input_str, capture_output=True, text=True, shell=False, check=False)
    if result.returncode != 0:
        print(f"Error running command: {command}", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        result.check_returncode()
    return result.stdout

def get_git_remote():
    output = run_command(["git", "remote", "-v"])
    remotes = []
    for line in output.splitlines():
        parts = line.split()
        if len(parts) < 2:
            continue
        name, url = parts[0], parts[1]
        remotes.append((name, url))

    # Prefer remotes whose URL matches the original, specific pattern.
    for name, url in remotes:
        if "gradle/docker-gradle" in url:
            return name

    # Fallback: remotes whose URL matches a broader pattern (e.g., forks).
    for name, url in remotes:
        if "docker-gradle" in url:
            return name

    # Next preference: a remote explicitly named "upstream", if present.
    for name, _ in remotes:
        if name == "upstream":
            return name

    # Final fallback: assume "origin" is the appropriate remote.
    return "origin"

def get_directories(commit):
    output = run_command(["git", "ls-tree", "-r", "--name-only", commit])
    files = output.splitlines()
    dirs = [os.path.dirname(f) for f in files if f.endswith("/Dockerfile") and not f.startswith("toolbox/") and not f.startswith(".")]

    def sort_key(d):
        jdk_part = d.split('-')[0].replace("jdk", "")
        if jdk_part == "":
            jdk_val = 999 # jdk-lts-and-current
        else:
            jdk_val = int(jdk_part)

        lts_jdks = [25, 21, 17, 11, 8]
        is_lts = 0 if jdk_val in lts_jdks else 1

        jdk_sort_val = jdk_val if jdk_val == 999 else -jdk_val

        variant_score = 0
        if "alpine" in d: variant_score = 1
        elif "corretto" in d: variant_score = 2
        elif "ubi" in d: variant_score = 3
        elif "graal" in d: variant_score = 4

        ubuntu_score = -2
        if "jammy" in d: ubuntu_score = -1

        return (is_lts, jdk_sort_val, variant_score, ubuntu_score, d)

    dirs.sort(key=sort_key)
    return dirs

def get_arches(image, cache):
    if image in cache:
        return cache[image]

    # In the original script: bashbrew cat --format '{{ join ", " .TagEntry.Architectures }}' "https://github.com/docker-library/official-images/raw/HEAD/library/$from"
    # Note: bashbrew might not be available in the environment where this runs during development,
    # but it should be in the toolbox image.
    output = run_command([
        "bashbrew",
        "cat",
        "--format",
        '{{ join ", " .TagEntry.Architectures }}',
        f"https://github.com/docker-library/official-images/raw/HEAD/library/{image}",
    ])
    arches = output.strip()
    cache[image] = arches
    return arches

def intersect_arches(arches1, arches2):
    a = set(arch.strip() for arch in arches1.split(",") if arch.strip())
    b = set(arch.strip() for arch in arches2.split(",") if arch.strip())
    common = a.intersection(b)
    # Maintain some sort of order if possible, though sets are unordered.
    # Let's sort them to be deterministic.
    return ", ".join(sorted(list(common)))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--substitute", nargs=2, action='append', help="Substitute <source_sha> <replacement_sha>")
    args = parser.parse_args()

    substitutions = {}
    if args.substitute:
        for src, repl in args.substitute:
            substitutions[src] = repl
            print("WARNING: using substitution, the result can't be submitted to the official images repository", file=sys.stderr)

    branches = ['master', '8', '7', '6']
    retired_tags = {
        'jdk24-corretto-al2023': True,
        'jdk24-graal-noble': True
    }

    git_remote = get_git_remote()

    print("Maintainers: Louis Jacomet <louis@gradle.com> (@ljacomet),")
    print("             Christoph Obexer <cobexer@gradle.com> (@cobexer),")
    print("             Keegan Witt <keeganwitt@gmail.com> (@keeganwitt)")
    print("GitRepo: https://github.com/gradle/docker-gradle.git")

    used_tags = {}
    arches_lookup_cache = {}

    for branch in branches:
        major = '9' if branch == 'master' else branch

        try:
            commit = run_command(["git", "rev-parse", f"refs/remotes/{git_remote}/{branch}"]).strip()
        except subprocess.CalledProcessError:
            # Fallback for local testing or if remote ref doesn't exist
            commit = run_command(["git", "rev-parse", branch]).strip()

        if commit in substitutions:
            commit = substitutions[commit]
            print(f"note: substituting commit {commit} for branch {branch}", file=sys.stderr)

        print(f"\n# Gradle {major}.x")

        directories = get_directories(commit)

        first_version = None
        for dir_path in directories:
            dockerfile = run_command(["git", "show", f"{commit}:{dir_path}/Dockerfile"])

            # Extract FROM
            from_match = re.search(r"^\s*FROM\s+(\S+)", dockerfile, re.MULTILINE | re.IGNORECASE)
            from_image = from_match.group(1) if from_match else ""

            # Extract GRADLE_VERSION
            version_match = re.search(r"^\s*ENV\s+GRADLE_VERSION=(\S+)", dockerfile, re.MULTILINE)
            version = version_match.group(1) if version_match else ""

            if re.match(r"^[0-9]+\.[0-9]+$", version):
                version += ".0"

            if not version.startswith(f"{major}."):
                print(f"error: version mismatch in {dir_path} on {branch} (version {version} is not {major}.x)", file=sys.stderr)
                sys.exit(1)

            if first_version is None:
                first_version = version
            elif version != first_version:
                print(f"error: {dir_path} on {branch} contains {version} (compared to {first_version} in {directories[0]})", file=sys.stderr)
                sys.exit(1)

            from_tag = from_image.split(":")[-1]
            suite = from_tag.replace("-jdk", "").replace("-minimal", "")
            if "-" in suite:
                suite = suite.split("-")[-1]

            jdk = dir_path.split("-")[0]
            if dir_path.startswith("jdk-lts-and-current"):
                jdk = 'jdk-lts-and-current'

            variant = ''
            if "-alpine" in dir_path: variant = 'alpine'
            elif "-corretto" in dir_path: variant = 'corretto'
            elif "-ubi" in dir_path: variant = 'ubi'
            elif "-graal" in dir_path: variant = 'graal'

            tags = []
            v_parts = version.split(".")
            versions = [
                version,
                ".".join(v_parts[:2]),
                v_parts[0],
                ''
            ]

            suffix = f"-{jdk}" + (f"-{variant}" if variant else "")
            for v in versions:
                tags.append(f"{v}{suffix}".lstrip("-"))

            if variant == '':
                for v in versions:
                    tags.append(f"{v}-{jdk}-{suite}".lstrip("-"))
                tags.append('latest')
                for v in versions:
                    tags.append(f"{v}-jdk".lstrip("-"))
                for v in versions:
                    if v: tags.append(v)
                for v in versions:
                    tags.append(f"{v}-jdk-{suite}".lstrip("-"))
                for v in versions:
                    tags.append(f"{v}-{suite}".lstrip("-"))
            elif variant == 'alpine':
                for v in versions:
                    tags.append(f"{v}-jdk-alpine".lstrip("-"))
                for v in versions:
                    tags.append(f"{v}-alpine".lstrip("-"))
            elif variant == 'corretto':
                tags.append('corretto')
                for v in versions:
                    tags.append(f"{v}-{jdk}-corretto-{suite}".lstrip("-"))
                tags.append(f"corretto-{suite}")
            elif variant == 'ubi':
                tags.append('ubi')
                for v in versions:
                    tags.append(f"{v}-{jdk}-{suite}".lstrip("-"))
                tags.append(suite)
            elif variant == 'graal':
                for v in versions:
                    tags.append(f"{v}-jdk-graal".lstrip("-"))
                for v in versions:
                    tags.append(f"{v}-graal".lstrip("-"))
                for v in versions:
                    tags.append(f"{v}-{jdk}-graal-{suite}".lstrip("-"))
                for v in versions:
                    tags.append(f"{v}-jdk-graal-{suite}".lstrip("-"))
                for v in versions:
                    tags.append(f"{v}-graal-{suite}".lstrip("-"))

            if jdk == 'jdk-lts-and-current':
                lts = ""
                current = ""
                if variant == 'graal':
                    lts_match = re.search(r"JAVA_LTS_VERSION=(\S+)", dockerfile)
                    current_match = re.search(r"JAVA_CURRENT_VERSION=(\S+)", dockerfile)
                    if lts_match: lts = lts_match.group(1).split(".")[0]
                    if current_match: current = current_match.group(1).split(".")[0]

                    # Fallback to HOME if VERSION not found (unlikely but safer)
                    if not lts:
                        lts_match = re.search(r"^\s*ENV\s+JAVA_LTS_HOME=.*?(\d+)\s*$", dockerfile, re.MULTILINE)
                        if lts_match: lts = lts_match.group(1)
                    if not current:
                        current_match = re.search(r"^\s*ENV\s+JAVA_CURRENT_HOME=.*?(\d+)\s*$", dockerfile, re.MULTILINE)
                        if current_match: current = current_match.group(1)
                else:
                    lts = from_tag.split("-")[0]
                    copy_from_match = re.search(r"^\s*COPY\s+--from=(\S+)", dockerfile, re.MULTILINE | re.IGNORECASE)
                    if copy_from_match:
                        current_from = copy_from_match.group(1)
                        current = current_from.split(":")[-1].split("-")[0]
                    else:
                        current = lts

                new_versioned_tags = []
                for t in tags:
                    new_versioned_tags.append(t.replace('jdk-lts-and-current', f'jdk-{lts}-and-{current}'))
                tags.extend(new_versioned_tags)

            actual_tags = []
            for tag in tags:
                if not tag or tag in used_tags:
                    continue
                if tag in retired_tags:
                    print(f"not generating retired tag '{tag}' for {dir_path} on branch {branch}", file=sys.stderr)
                    continue
                used_tags[tag] = True
                actual_tags.append(tag)

            if not actual_tags:
                continue

            if variant == 'graal':
                arches = 'amd64, arm64v8'
            else:
                arches = get_arches(from_image, arches_lookup_cache)

            if jdk == 'jdk-lts-and-current' and variant != 'graal':
                copy_from_match = re.search(r"^\s*COPY\s+--from=(\S+)", dockerfile, re.MULTILINE | re.IGNORECASE)
                copy_from = copy_from_match.group(1) if copy_from_match else from_image
                copy_from_arches = get_arches(copy_from, arches_lookup_cache)

                if arches != copy_from_arches:
                        new_arches = intersect_arches(arches, copy_from_arches)
                    if not new_arches:
                        print(f"error: arches mismatch between {from_image} and {copy_from} in {dir_path} on branch {branch} ('{arches}' vs '{copy_from_arches}' results in an empty intersection)", file=sys.stderr)
                        sys.exit(1)
                    arches = new_arches

            print(f"\nTags: {', '.join(actual_tags)}")
            print(f"Architectures: {arches}")
            print(f"GitFetch: refs/heads/{branch}")
            print(f"GitCommit: {commit}")
            print(f"Directory: {dir_path}")

if __name__ == "__main__":
    main()
