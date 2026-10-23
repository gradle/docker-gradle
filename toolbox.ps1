$buildOutput = & docker build --pull --tag gradle-dockerhub-toolbox -f toolbox/Dockerfile toolbox 2>&1

if ($LASTEXITCODE -ne 0) {
    [Console]::Error.WriteLine(($buildOutput -join [Environment]::NewLine))
    [Console]::Error.WriteLine('Failed to build gradle-dockerhub-toolbox image')
    exit 1
}

& docker run --rm -ti `
    -v "$($PWD.Path):/workspace" `
    -e GITHUB_TOKEN `
    -w /workspace `
    gradle-dockerhub-toolbox `
    python3 @args

exit $LASTEXITCODE
