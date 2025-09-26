#!/usr/bin/env pwsh
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# NOTE: run something like `git fetch origin` before this script to ensure all remote branch references are up-to-date!

# front-load the "command-not-found" notices
bashbrew --version > $null

$branches = @(
 'master'
 '8'
 '7'
 '6'
)

$gitRemote = (git remote -v | Select-String 'gradle/docker-gradle' | ForEach-Object { $_.Line.Split()[0] })[0]

@"
Maintainers: Louis Jacomet <louis@gradle.com> (@ljacomet),
             Christoph Obexer <cobexer@gradle.com> (@cobexer),
             Keegan Witt <keeganwitt@gmail.com> (@keeganwitt)
GitRepo: https://github.com/gradle/docker-gradle.git
"@

$usedTags = @{}
$archesLookupCache = @{}
foreach ($branch in $branches) {
    switch ($branch) {
        'master' { $major = '9' }
        default { $major = $branch }
    }

    $commit = git rev-parse "refs/remotes/$gitRemote/$branch"
    $common = @"
GitFetch: refs/heads/$branch
GitCommit: $commit
"@

    @"


# Gradle $major.x
"@

    $allDirectories = git ls-tree -r --name-only "$commit" |
                     Where-Object { $_ -match '/Dockerfile$' } |
                     ForEach-Object { $_ -replace '/Dockerfile$', '' }

    $directoriesWithSortKeys = @()
    foreach ($dir in $allDirectories) {
        $jdkPart = ($dir -split '-')[0] -replace 'jdk', ''
        $jdkNum = if ($jdkPart -eq "" -or $dir -match 'jdk-lts-and-current') { 999 } else { [int]$jdkPart }

        $primaryJdkSort = if ($jdkNum -in @(25, 21, 17, 11, 8)) { 0 } else { 1 }
        $secondaryJdkSort = if ($jdkNum -eq 999) { $jdkNum } else { -$jdkNum }

        $variantSort = 0 # Default for plain
        if ($dir -match 'alpine') { $variantSort = 1 }
        elseif ($dir -match 'corretto') { $variantSort = 2 }
        elseif ($dir -match 'ubi') { $variantSort = 3 }
        elseif ($dir -match 'graal') { $variantSort = 4 }

        $suiteSort = -2 # Default (noble or unspecified)
        if ($dir -match 'jammy') { $suiteSort = -1 }

        $directoriesWithSortKeys += [PSCustomObject]@{
            Directory = $dir
            SortKeys = @($primaryJdkSort, $secondaryJdkSort, $variantSort, $suiteSort, $dir)
        }
    }

    $directories = $directoriesWithSortKeys |
                   Sort-Object -Property { $_.SortKeys[0] }, { $_.SortKeys[1] }, { $_.SortKeys[2] }, { $_.SortKeys[3] }, { $_.SortKeys[4] } |
                   Select-Object -ExpandProperty Directory

    $firstVersion = $null
    foreach ($dir in $directories) {
        $dockerfile = git show "${commit}:$dir/Dockerfile"

        $from = $dockerfile | Select-String -Pattern '^FROM ' | ForEach-Object { $_.Line -split ' ' | Select-Object -Last 1 }
        $version = $dockerfile | Select-String -Pattern '^ENV GRADLE_VERSION' | ForEach-Object { $_.Line -split '=' | Select-Object -Last 1 }
        if ($version -match '^\d+\.\d+$') {
            $version = "$version.0"
        }

        if ($version -notmatch "^$major\..*") {
            Write-Error "version mismatch in $dir on $branch (version $version is not $major.x)"
        }

        if (-not $firstVersion) {
            $firstVersion = $version
        }
        if ($version -ne $firstVersion) {
            Write-Error "$dir on $branch contains $version (compared to $firstVersion in $($directories[0]))"
        }

        $fromTag = $from.Split(':')[-1]
        $suite = $fromTag -replace '-jdk$', '' -replace '.*-', ''

        $jdk = $dir.Split('-')[0]
        if ($dir -match 'jdk-lts-and-current') {
            $jdk = 'jdk-lts-and-current'
        }

        switch -wildcard ($dir) {
            '*-alpine'   { $variant = 'alpine' }
            '*-corretto' { $variant = 'corretto' }
            '*-ubi*'     { $variant = 'ubi' }
            '*-graal'    { $variant = 'graal' }
            default      { $variant = '' }
        }

        $tags = @()
        $versions = @(
            "$version",
            "$($version -replace '\.\d+$')",
            "$($version -replace '\.\d+\.\d+$')",
            ''
        )

        $tags += $versions | ForEach-Object {
            if ($variant) {
                "$_-$jdk-$variant"
            } else {
                "$_-$jdk"
            }
        }

        switch ($variant) {
            '' {
                $tags += $versions | ForEach-Object { "$_-$jdk-$suite" }
                $tags += 'latest'
                $tags += $versions | ForEach-Object { "$_-jdk" }
                $tags += $versions
                $tags += $versions | ForEach-Object { "$_-jdk-$suite" }
                $tags += $versions | ForEach-Object { "$_-$suite" }
            }
            'alpine' {
                $tags += $versions | ForEach-Object { "$_-jdk-alpine" }
                $tags += $versions | ForEach-Object { "$_-alpine" }
            }
            'corretto' {
                $tags += 'corretto'
                $tags += $versions | ForEach-Object { "$_-$jdk-corretto-$suite" }
                $tags += "corretto-$suite"
            }
            'ubi' {
                $tags += 'ubi'
                $tags += $versions | ForEach-Object { "$_-$jdk-ubi-$suite" }
                $tags += "ubi-$suite"
            }
            'graal' {
                $tags += $versions | ForEach-Object { "$_-jdk-graal" }
                $tags += $versions | ForEach-Object { "$_-graal" }
                $tags += $versions | ForEach-Object { "$_-$jdk-graal-$suite" }
                $tags += $versions | ForEach-Object { "$_-jdk-graal-$suite" }
                $tags += $versions | ForEach-Object { "$_-graal-$suite" }
            }
        }

        # Handle jdk-lts-and-current special case
        if ($jdk -eq 'jdk-lts-and-current') {
            switch ($variant) {
                'graal' {
                    $lts = $dockerfile |
                           Select-String -Pattern '^ENV JAVA_LTS_HOME' |
                           ForEach-Object { ($_.Line -split '=')[1] -replace '^[^\d]*', '' }
                    $current = $dockerfile |
                              Select-String -Pattern '^ENV JAVA_CURRENT_HOME' |
                              ForEach-Object { ($_.Line -split '=')[1] -replace '^[^\d]*', '' }
                }
                default {
                    $lts = $fromTag.Split('-')[0]
                    $copyFromLine = $dockerfile | Select-String -Pattern '^COPY\s+--from=' | Select-Object -First 1
                    if ($copyFromLine -match '--from=([^\s]+)') {
                        $currentFrom = $matches[1]
                        $currentFromTag = $currentFrom.Split(':')[-1]
                        $current = $currentFromTag.Split('-')[0]
                    }
                }
            }
            # Takes all tags and creates new ones with jdk-lts-and-current replaced with specific versions
            $tags += $tags | ForEach-Object { $_ -replace 'jdk-lts-and-current', "jdk-$lts-and-$current" }
        }

        $actualTags = @()
        foreach ($tag in $tags) {
            $tag = $tag -replace '^-', '' # remove leading hyphen if any
            if (-not $tag -or $usedTags.ContainsKey($tag)) {
                continue
            }
            $usedTags[$tag] = 1
            $actualTags += $tag
        }
        $actualTagsString = $actualTags -join ', '

        if ($variant -eq 'graal') {
            $arches = 'amd64, arm64v8'
        } else {
            # Cache values to avoid excessive lookups for repeated base images
            $arches = $archesLookupCache[$from]
            if (-not $arches) {
                # Using backtick as delimiter in Go template avoids issues with comma in join function
                $arches = (bashbrew cat --format '{{ join `, ` .TagEntry.Architectures }}' "https://github.com/docker-library/official-images/raw/HEAD/library/$from")
                $archesLookupCache[$from] = $arches
            }
        }

        # Check architecture compatibility for the special jdk-lts-and-current case
        if ($jdk -eq 'jdk-lts-and-current' -and $variant -ne 'graal') {
            $copyFromLine = $dockerfile | Select-String -Pattern '^COPY\s+--from=' | Select-Object -First 1
            # Extract the image name correctly
            if ($copyFromLine -match '--from=([^\s]+)') {
                $copyFrom = $matches[1]
                $copyFromArches = $archesLookupCache[$copyFrom]
                if (-not $copyFromArches) {
                    $copyFromArches = (bashbrew cat --format '{{ join `, ` .TagEntry.Architectures }}' "https://github.com/docker-library/official-images/raw/HEAD/library/$copyFrom")
                    $archesLookupCache[$copyFrom] = $copyFromArches
                }
                if ($arches -ne $copyFromArches) {
                    Write-Error "arches mismatch between $from and $copyFrom in $dir on branch $branch ('$arches' vs '$copyFromArches')"
                }
            }
        }

        @"

Tags: $actualTagsString
Architectures: $arches
$common
Directory: $dir
"@
    }
}
