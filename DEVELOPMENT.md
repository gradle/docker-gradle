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
