#!/usr/bin/env bash
set -o errexit -o nounset -o pipefail

# NOTE: run something like `git fetch origin` before this script to ensure all remote branch references are up-to-date!

# usage: ./generate-stackbrew-library.sh > ../official-images/library/gradle

# front-load the "command-not-found" notices
jq --version > /dev/null
bashbrew --version > /dev/null

branches=(
	'master'
	'8'
	'7'
	'6'
)

gitRemote="$(git remote -v | awk '/gradle\/docker-gradle/ { print $1; exit }')"

cat <<-'EOH'
	Maintainers: Louis Jacomet <louis@gradle.com> (@ljacomet),
	             Christoph Obexer <cobexer@gradle.com> (@cobexer),
	             Keegan Witt <keeganwitt@gmail.com> (@keeganwitt)
	GitRepo: https://github.com/gradle/docker-gradle.git
EOH

declare -A usedTags=() archesLookupCache=()
for branch in "${branches[@]}"; do
	case "$branch" in
		master) major='9' ;;
		*) major="$branch" ;;
	esac

	commit="$(git rev-parse "refs/remotes/$gitRemote/$branch")"
	common="$(
		cat <<-EOC
			GitFetch: refs/heads/$branch
			GitCommit: $commit
		EOC
	)"

	cat <<-EOC


		# Gradle $major.x
	EOC

	directories="$(
		git ls-tree -r --name-only "$commit" | jq --raw-input --null-input --raw-output '
			# convert "git ls-tree" output to a list of directories that contain a Dockerfile
			[
				inputs
				| select(endswith("/Dockerfile"))
				| rtrimstr("/Dockerfile")
			]
			| sort_by(
				# sort the list:
				# - LTS JDK versions in descending order
				# - non-LTS JDK versions in descending order
				# - plain (temurin) variants above alpine above corretto above ubi above graal
				# - Ubuntu versions in descending release order
				# (presorting the list makes tag calculation easier later because we can simply generate a list of tags each combination *could* have and let the first one to try get it, being careful not to reuse any)
				(
					ltrimstr("jdk")
					| split("-")[0]
					| if . == "" then
						# "jdk-lts-and-current" is a special case
						999
					else
						tonumber
					end
				) as $jdk
				| [
					# LTS JDK versions above non-LTS
					(
						if $jdk | IN(25, 21, 17, 11, 8) then 0
						else 1 end
					),
					# JDK versions in descending version order
					(
						if $jdk == 999 then $jdk # "jdk-lts-and-current" is a special case we want to always be last
						else -$jdk end # negative so they sort in reverse order
					),
					# plain vs alpine vs corretto vs graal
					(
						if contains("alpine") then 1
						elif contains("corretto") then 2
						elif contains("ubi") then 3
						elif contains("graal") then 4
						else 0 end
					),
					# ubuntu versions in descending order
					(
						# if unspecified, we assume "latest" (currently "noble")
						if contains("jammy") then -1
						else -2 end
					),
					. # if all else fails, sort lexicographically
				]
			)
			# escape for passing to the shell (safely)
			| map(@sh)
			| join(" ")
		'
	)"
	eval "directories=( $directories )"

	firstVersion=
	for dir in "${directories[@]}"; do
		# shellcheck disable=SC2001
		dir="$(echo "$dir" | sed -e 's/[[:space:]]*$//')"

		dockerfile="$(git show "$commit:$dir/Dockerfile")"

		# extract "FROM" and "GRADLE_VERSION" from Dockerfile
		from="$(awk <<<"$dockerfile" 'toupper($1) == "FROM" { print $2; exit }')"
		version="$(awk <<<"$dockerfile" -F '[=[:space:]]+' 'toupper($1) == "ENV" && $2 == "GRADLE_VERSION" { print $3; exit }')"
		# add a patch version of 0 if missing
		if [[ "$version" =~ ^[0-9]+\.[0-9]+$ ]]; then
			version="${version}.0"
		fi

		# make sure the version we scraped matches what we expect to
		case "$version" in
			"$major".*) ;;
			*)
				echo >&2 "error: version mismatch in $dir on $branch (version $version is not $major.x)"
				exit 1
				;;
		esac

		# double-check that each version matches the first one for this major (they should all be updated in lock-step)
		[ -n "$firstVersion" ] || firstVersion="$version"
		if [ "$version" != "$firstVersion" ]; then
			echo >&2 "error: $dir on $branch contains $version (compared to $firstVersion in ${directories[0]})"
			exit 1
		fi

		fromTag="${from##*:}"
		suite="${fromTag%-jdk}"
		suite="${suite##*-}" # "noble", "jammy", "al2023", etc

		jdk="${dir%%-*}" # "jdk8", etc
		if [[ "$dir" == jdk-lts-and-current* ]]; then
			jdk='jdk-lts-and-current'
		fi

		# identify image "variant" so we can assign tags based on variant
		case "$dir" in
			*-alpine)   variant='alpine' ;;
			*-corretto) variant='corretto' ;;
			*-ubi*)     variant='ubi' ;;
			*-graal)    variant='graal' ;;
			*)          variant='' ;;
		esac

		# build up a list of tags we want to assign this directory, then filter out ones we've already used (a major benefit of our priority sorting above)
		tags=()
		versions=(
			# this assumes upstream's version numbers always have three parts - if that ever changes, this needs to become more complex
			"$version"        # X.Y.Z
			"${version%.*}"   # X.Y
			"${version%.*.*}" # X
			''                # this will lead to some tags that start with hyphen; we'll clean them up afterwards (it makes the logic easier to write correctly so we get all of "X.Y.Z-foo", "X.Y-foo", "X-foo", *and* "foo")
		)
		tags+=( "${versions[@]/%/-$jdk${variant:+-$variant}}" ) # "X.Y.Z-jdkNN-graal"
		case "$variant" in
			'')
				tags+=(
					"${versions[@]/%/-$jdk-$suite}" # "X.Y.Z-jdkNN-noble"
					'latest'
					"${versions[@]/%/-jdk}" # "X.Y.Z-jdk"
					"${versions[@]}" # "X.Y.Z"
					"${versions[@]/%/-jdk-$suite}" # "X.Y.Z-jdk-noble"
					"${versions[@]/%/-$suite}" # "X.Y.Z-noble"
				)
				;;
			alpine)
				tags+=(
					"${versions[@]/%/-jdk-alpine}" # "X.Y.Z-jdk-alpine"
					"${versions[@]/%/-alpine}" # "X.Y.Z-alpine"
				)
				;;
			corretto)
				tags+=(
					'corretto'
					"${versions[@]/%/-$jdk-corretto-$suite}" # "X.Y.Z-corretto-al2023"
					"corretto-$suite" # "corretto-al2023"
				)
				;;
			ubi)
				tags+=(
					'ubi'
					"${versions[@]/%/-$jdk-ubi-$suite}" # "X.Y.Z-ubi10"
					"ubi-$suite" # "ubi10"
				)
				;;
			graal)
				tags+=(
					"${versions[@]/%/-jdk-graal}" # "X.Y.Z-jdk-graal"
					"${versions[@]/%/-graal}" # "X.Y.Z-graal"
					"${versions[@]/%/-$jdk-graal-$suite}" # "X.Y.Z-jdkNN-graal-noble"
					"${versions[@]/%/-jdk-graal-$suite}" # "X.Y.Z-jdk-graal-noble"
					"${versions[@]/%/-graal-$suite}" # "X.Y.Z-graal-noble"
				)
				;;
		esac

		# the special "jdk-lts-and-current" variants need to resolve their respective JDK versions to get "jdk-21-and-23" style tags too
		if [ "$jdk" = 'jdk-lts-and-current' ]; then
			# scrape java versions from $dockerfile (complicated for graal)
			case "$variant" in
				graal)
					# TODO this is a little bit fiddly, but it works
					lts="$(awk <<<"$dockerfile" -F '[=[:space:]]+' 'toupper($1) == "ENV" && $2 == "JAVA_LTS_HOME" { gsub("^[^0-9]*", "", $3); print $3; exit }')"
					current="$(awk <<<"$dockerfile" -F '[=[:space:]]+' 'toupper($1) == "ENV" && $2 == "JAVA_CURRENT_HOME" { gsub("^[^0-9]*", "", $3); print $3; exit }')"
					;;
				*)
					lts="${fromTag%%-*}"
					currentFrom="$(awk <<<"$dockerfile" -F '[=[:space:]]+' 'toupper($1) == "COPY" && $2 == "--from" { print $3; exit }')"
					currentFromTag="${currentFrom##*:}"
					current="${currentFromTag%%-*}"
					;;
			esac
			# take all tags and append new tags replacing "jdk-lts-and-current" with the new versioned variation
			tags+=( "${tags[@]/jdk-lts-and-current/jdk-$lts-and-$current}" )
		fi

		actualTags=
		for tag in "${tags[@]}"; do
			tag="${tag#-}" # remove those errant hyphen prefixes mentioned above
			if [ -z "$tag" ] || [ -n "${usedTags[$tag]:-}" ]; then
				continue
			fi
			usedTags[$tag]=1
			actualTags="${actualTags:+$actualTags, }$tag"
		done

		if [ "$variant" = 'graal' ]; then
			arches='amd64, arm64v8'
		else
			# cache values to avoid excessive lookups for repeated base images
			arches="${archesLookupCache[$from]:-}"
			if [ -z "$arches" ]; then
				arches="$(bashbrew cat --format '{{ join ", " .TagEntry.Architectures }}' "https://github.com/docker-library/official-images/raw/HEAD/library/$from")"
				archesLookupCache[$from]="$arches"
			fi
		fi

		if [ "$jdk" = 'jdk-lts-and-current' ] && [ "$variant" != 'graal' ]; then
			# *technically*, we could re-use "currentFrom" that we scraped above, but there's a lot of conditional logic between here and there so it's safer to just re-scrape it
			copyFrom="$(awk <<<"$dockerfile" -F '[=[:space:]]+' 'toupper($1) == "COPY" && $2 == "--from" { print $3; exit }')"
			copyFromArches="${archesLookupCache[$copyFrom]:-}"
			if [ -z "$copyFromArches" ]; then
				copyFromArches="$(bashbrew cat --format '{{ join ", " .TagEntry.Architectures }}' "https://github.com/docker-library/official-images/raw/HEAD/library/$copyFrom")"
				archesLookupCache[$copyFrom]="$copyFromArches"
			fi
			if [ "$arches" != "$copyFromArches" ]; then
				# TODO implement set intersection logic here (only keeping arches supported by both)
				echo >&2 "error: arches mismatch between $from and $copyFrom in $dir on branch $branch ('$arches' vs '$copyFromArches')"
				exit 1
			fi
		fi

		cat <<-EOE

			Tags: $actualTags
			Architectures: $arches
			$common
			Directory: $dir
		EOE
	done
done
