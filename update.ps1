#!/usr/bin/env pwsh
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$gradleVersion = '6.9.4'
$sha = $(Invoke-RestMethod -Uri "https://downloads.gradle.org/distributions/gradle-${gradleVersion}-bin.zip.sha256")

$wc = [System.Net.WebClient]::new()
$graal17Version = $(((Invoke-WebRequest "https://api.github.com/repos/graalvm/graalvm-ce-builds/releases?per_page=20&page=1" | ConvertFrom-Json).tag_name | Select-String -Pattern "jdk-17" | Select-Object -First 1).ToString().Replace("jdk-", ""))
$graal17amd64Hash = (Get-FileHash -Algorithm SHA256 -InputStream ($wc.OpenRead("https://github.com/graalvm/graalvm-ce-builds/releases/download/jdk-${graal17Version}/graalvm-community-jdk-${graal17Version}_linux-x64_bin.tar.gz"))).Hash.ToLower()
$graal17aarch64Hash = (Get-FileHash -Algorithm SHA256 -InputStream ($wc.OpenRead("https://github.com/graalvm/graalvm-ce-builds/releases/download/jdk-${graal17Version}/graalvm-community-jdk-${graal17Version}_linux-aarch64_bin.tar.gz"))).Hash.ToLower()

$graal21Version = $(((Invoke-WebRequest "https://api.github.com/repos/graalvm/graalvm-ce-builds/releases?per_page=20&page=1" | ConvertFrom-Json).tag_name | Select-String -Pattern "jdk-21" | Select-Object -First 1).ToString().Replace("jdk-", ""))
$graal21amd64Hash = (Get-FileHash -Algorithm SHA256 -InputStream ($wc.OpenRead("https://github.com/graalvm/graalvm-ce-builds/releases/download/jdk-${graal21Version}/graalvm-community-jdk-${graal21Version}_linux-x64_bin.tar.gz"))).Hash.ToLower()
$graal21aarch64Hash = (Get-FileHash -Algorithm SHA256 -InputStream ($wc.OpenRead("https://github.com/graalvm/graalvm-ce-builds/releases/download/jdk-${graal21Version}/graalvm-community-jdk-${graal21Version}_linux-aarch64_bin.tar.gz"))).Hash.ToLower()

$graal24Version = $(((Invoke-WebRequest "https://api.github.com/repos/graalvm/graalvm-ce-builds/releases?per_page=20&page=1" | ConvertFrom-Json).tag_name | Select-String -Pattern "jdk-24" | Select-Object -First 1).ToString().Replace("jdk-", ""))
$graal24amd64Hash = (Get-FileHash -Algorithm SHA256 -InputStream ($wc.OpenRead("https://github.com/graalvm/graalvm-ce-builds/releases/download/jdk-${graal24Version}/graalvm-community-jdk-${graal24Version}_linux-x64_bin.tar.gz"))).Hash.ToLower()
$graal24aarch64Hash = (Get-FileHash -Algorithm SHA256 -InputStream ($wc.OpenRead("https://github.com/graalvm/graalvm-ce-builds/releases/download/jdk-${graal24Version}/graalvm-community-jdk-${graal24Version}_linux-aarch64_bin.tar.gz"))).Hash.ToLower()

Write-Host "Latest Gradle version is $gradleVersion"
Write-Host "Latest Graal 17 version is $graal17Version"
Write-Host "Latest Graal 21 version is $graal21Version"
Write-Host "Latest Graal 24 version is $graal24Version"

Write-Host "Graal 17 AMD64 hash is $graal17amd64Hash"
Write-Host "Graal 17 AARCH64 hash is $graal17aarch64Hash"
Write-Host "Graal 21 AMD64 hash is $graal21amd64Hash"
Write-Host "Graal 21 AARCH64 hash is $graal21aarch64Hash"
Write-Host "Graal 24 AMD64 hash is $graal24amd64Hash"
Write-Host "Graal 24 AARCH64 hash is $graal24aarch64Hash"

dir -Recurse -Filter Dockerfile | ForEach-Object {
    (Get-Content -Path $_.FullName) -replace "ENV GRADLE_VERSION=.+$", "ENV GRADLE_VERSION=${gradleVersion}" | Set-Content $_.FullName
    (Get-Content -Path $_.FullName) -replace "GRADLE_DOWNLOAD_SHA256=.+$", "GRADLE_DOWNLOAD_SHA256=${sha}" | Set-Content $_.FullName
    if ($((Get-Item $_.FullName).Directory.Name) -eq "jdk17-noble-graal" -Or $((Get-Item $_.FullName).Directory.Name) -eq "jdk17-jammy-graal")
    {
        (Get-Content -Path $_.FullName) -replace "JAVA_VERSION=[^ ]+", "JAVA_VERSION=${graal17Version}" | Set-Content $_.FullName
        (Get-Content -Path $_.FullName) -replace "GRAALVM_AMD64_DOWNLOAD_SHA256=[^ ]+", "GRAALVM_AMD64_DOWNLOAD_SHA256=${graal17amd64Hash}" | Set-Content $_.FullName
        (Get-Content -Path $_.FullName) -replace "GRAALVM_AARCH64_DOWNLOAD_SHA256=[^ ]+", "GRAALVM_AARCH64_DOWNLOAD_SHA256=${graal17aarch64Hash}" | Set-Content $_.FullName
    }
    elseif ($((Get-Item $_.FullName).Directory.Name) -eq "jdk21-noble-graal" -Or $((Get-Item $_.FullName).Directory.Name) -eq "jdk21-jammy-graal")
    {
        (Get-Content -Path $_.FullName) -replace "JAVA_VERSION=[^ ]+", "JAVA_VERSION=${graal21Version}" | Set-Content $_.FullName
        (Get-Content -Path $_.FullName) -replace "GRAALVM_AMD64_DOWNLOAD_SHA256=[^ ]+", "GRAALVM_AMD64_DOWNLOAD_SHA256=${graal21amd64Hash}" | Set-Content $_.FullName
        (Get-Content -Path $_.FullName) -replace "GRAALVM_AARCH64_DOWNLOAD_SHA256=[^ ]+", "GRAALVM_AARCH64_DOWNLOAD_SHA256=${graal21aarch64Hash}" | Set-Content $_.FullName
    }
    elseif ($((Get-Item $_.FullName).Directory.Name) -eq "jdk24-noble-graal")
    {
        (Get-Content -Path $_.FullName) -replace "JAVA_VERSION=[^ ]+", "JAVA_VERSION=${graal24Version}" | Set-Content $_.FullName
        (Get-Content -Path $_.FullName) -replace "GRAALVM_AMD64_DOWNLOAD_SHA256=[^ ]+", "GRAALVM_AMD64_DOWNLOAD_SHA256=${graal24amd64Hash}" | Set-Content $_.FullName
        (Get-Content -Path $_.FullName) -replace "GRAALVM_AARCH64_DOWNLOAD_SHA256=[^ ]+", "GRAALVM_AARCH64_DOWNLOAD_SHA256=${graal24aarch64Hash}" | Set-Content $_.FullName
    }
    elseif ($((Get-Item $_.FullName).Directory.Name) -eq "jdk-lts-and-current-graal")
    {
        (Get-Content -Path $_.FullName) -replace "JAVA_21_VERSION=[^ ]+", "JAVA_21_VERSION=${graal21Version}" | Set-Content $_.FullName
        (Get-Content -Path $_.FullName) -replace "GRAALVM_21_AMD64_DOWNLOAD_SHA256=[^ ]+", "GRAALVM_21_AMD64_DOWNLOAD_SHA256=${graal21amd64Hash}" | Set-Content $_.FullName
        (Get-Content -Path $_.FullName) -replace "GRAALVM_21_AARCH64_DOWNLOAD_SHA256=[^ ]+", "GRAALVM_21_AARCH64_DOWNLOAD_SHA256=${graal21aarch64Hash}" | Set-Content $_.FullName
        (Get-Content -Path $_.FullName) -replace "JAVA_24_VERSION=[^ ]+", "JAVA_24_VERSION=${graal24Version}" | Set-Content $_.FullName
        (Get-Content -Path $_.FullName) -replace "GRAALVM_24_AMD64_DOWNLOAD_SHA256=[^ ]+", "GRAALVM_24_AMD64_DOWNLOAD_SHA256=${graal24amd64Hash}" | Set-Content $_.FullName
        (Get-Content -Path $_.FullName) -replace "GRAALVM_24_AARCH64_DOWNLOAD_SHA256=[^ ]+", "GRAALVM_24_AARCH64_DOWNLOAD_SHA256=${graal24aarch64Hash}" | Set-Content $_.FullName
    }
}

(Get-Content -Path .github/workflows/ci.yaml) -replace "expectedGradleVersion: .+", "expectedGradleVersion: '${gradleVersion}'" | Set-Content .github/workflows/ci.yaml
