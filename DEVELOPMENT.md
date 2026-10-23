# Developer Documentation

This repository contains the infrastructure for building and maintaining official Gradle Docker images.

## Maintenance Scripts

The following Python scripts are used for repository maintenance:

*   `update.py`: Fetches the latest Gradle and GraalVM versions and updates all `Dockerfile`s and CI configurations accordingly.
*   `generate-stackbrew-library.py`: Generates the library manifest file in the format required by the Docker official images repository.

### Prerequisites

These scripts require Python 3 and the `requests` library. To avoid environment inconsistencies, it is recommended to run them using the provided toolbox.

### Using the Toolbox

The `toolbox.sh` script is a wrapper that builds and runs a Docker-based environment containing all necessary tools (Python 3, `requests`, `git`, `bashbrew`).

To run a script via the toolbox:

```bash
./toolbox.sh update.py
./toolbox.sh generate-stackbrew-library.py
```

Arguments can be passed to the scripts as well:

```bash
./toolbox.sh generate-stackbrew-library.py --substitute <old_sha> <new_sha>
```

The manifest generator selects its remote in this order: explicit `--remote <name>`, the current branch's tracking remote, `origin`, then a remote pointing to `gradle/docker-gradle`. Detached HEAD checkouts skip tracking-remote selection. All release branches must be fetched from the selected remote; local branches are not used as fallbacks.

```bash
./toolbox.sh generate-stackbrew-library.py --remote origin
```

## Toolbox Docker Image

The toolbox image is defined in `toolbox/Dockerfile`. It is based on `python:3-alpine` and includes:

*   `git` for interacting with the repository.
*   `curl` for downloading tools.
*   `bashbrew` for manifest generation and architecture lookups.
*   The `requests` Python library.

The `toolbox.sh` script handles the building of this image automatically.

## Integration Tests

To verify changes to the Docker images, you can run the integration tests:

```bash
./test/run.sh <image_tag> <expected_gradle_version>
./test-graal/run.sh <image_tag> <expected_gradle_version>
```

Example:

```bash
docker build -t gradle-test ./jdk21-noble
./test/run.sh gradle-test 8.12.1
```

## Releasing

Publish new images after every Gradle GA or patch release. Release candidates and milestones are never published: `update.py` only picks up final versions.

The current Gradle major lives on `master`, older majors on a branch named after them (e.g. `8`). Each branch's `version.txt` holds the major it tracks.

### 1. Update the branch

Repeat for each major that got a release:

```bash
git fetch origin
git switch -c gradle-<version> origin/<branch>   # <branch> is master or the specific major
./toolbox.sh update.py                           # requires a running container runtime
```

`update.py` sets `GRADLE_VERSION` and `GRADLE_DOWNLOAD_SHA256` in every `Dockerfile`, `expectedGradleVersion` in `.github/workflows/ci.yaml`, and bumps the GraalVM versions and checksums. Set `GITHUB_TOKEN` to avoid GitHub API rate limits.

Review the diff: the Gradle version and checksum change in every `Dockerfile`, GraalVM changes are expected only when GraalVM released too. Commit it as `Gradle <version>` and open a PR against `<branch>`.

### 2. Review the PR

* **GitHub CI** builds every image directory and runs the integration tests against `expectedGradleVersion`.
* **Official Images Updates** generates the library file; a follow-up workflow comments the diff against the currently published `library/gradle`, ignoring commit IDs. Check that only the expected tags changed.

Merge once both are green.

### 3. Submit to Docker Official Images

Every push to a release branch runs **Official Images Updates**, which uploads the generated manifest as the `library-gradle` artifact. The manifest covers all release branches at once, so take it from the run of the last merge. If multiple majors were released, merge all PRs first and submit once.

```bash
run_id=$(gh run list -R gradle/docker-gradle -w "Official Images Updates" -e push -L 1 --json databaseId --jq '.[0].databaseId')
artifact_id=$(gh api repos/gradle/docker-gradle/actions/runs/$run_id/artifacts --jq '.artifacts[] | select(.name == "library-gradle") | .id')
gh api repos/gradle/docker-gradle/actions/artifacts/$artifact_id/zip > library-gradle
```

The artifact is uploaded unzipped, so `gh run download` cannot extract it; the API call above returns the file itself.

Copy it over `library/gradle` in a fork of [docker-library/official-images](https://github.com/docker-library/official-images) and open a PR titled `Gradle <version>`. Do not submit a manifest from a PR run: it substitutes commit IDs and starts with a warning saying so.

A bot comments the resulting diff on the PR. A Gradle image maintainer, as listed under `Maintainers` in the upstream [`library/gradle`](https://github.com/docker-library/official-images/blob/master/library/gradle) file, has to review it and approve with a comment, for example. A comment on the PR pings them, but asking them directly may be preferred. The PR is then approved and merged by an Official Images program maintainer.

### 4. Verify

Once the official-images PR is merged, Docker's build infrastructure builds and pushes the images, which can take a few hours. Check that the new tags appear on [Docker Hub](https://hub.docker.com/_/gradle/tags) with all expected architectures:

```bash
docker buildx imagetools inspect gradle:<version>
```

### Java version changes

When a Gradle release adds support for a new Java version, update the images alongside the version bump:

* **New non-LTS Java:** rename the previous non-LTS `jdk<N>-*` directories to the new version (`git mv`) and update their `FROM` lines. Only add variants whose base image exists upstream; drop those that don't.
* **New LTS Java:** add new `jdk<N>-*` directories next to the existing LTS ones, including `-graal` variants, and add `<N>` to `lts_jdks` in `generate-stackbrew-library.py` and the GraalVM section of `update.py`.
* **Combo images:** point `jdk-lts-and-current*` at the new current JDK (`COPY --from` and `JAVA_CURRENT_HOME`), and for a new LTS also at the new LTS.
* Update the `ci.yaml` matrix and the supported tags in `README.md`.
* To stop publishing a tag that a branch would still generate, add it to `retired_tags` in `generate-stackbrew-library.py`.

The official-images PR description should list added, removed and renamed variants.
