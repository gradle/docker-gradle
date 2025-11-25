#!/bin/sh

if ! build_output=$(docker build --pull --tag gradle-dockerhub-toolbox -f toolbox/Dockerfile toolbox 2>&1); then
	echo "$build_output" >&2
	echo "Failed to build gradle-dockerhub-toolbox image" >&2
	exit 1
fi

exec docker run --rm -ti \
	-v "$(pwd):/workspace" \
	-w /workspace \
	gradle-dockerhub-toolbox \
	bash "$@"
