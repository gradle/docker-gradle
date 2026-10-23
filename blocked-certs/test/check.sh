#!/bin/sh
# Runs inside an image. Checks every JDK in the image:
# - offline: its lib/security/blocked.certs has every fingerprint in ../blocked.certs
# - online: it rejects TLS connections to the eMudhra test hosts and still connects to services.gradle.org
set -o errexit -o nounset

dir="$(cd "$(dirname "$0")" && pwd)"
fingerprints="$(grep -E '^[0-9A-F]{64}$' "${dir}/../blocked.certs")"
expected=$(echo "${fingerprints}" | wc -l)

blocked_hosts="
    dv-g3b-aaa-emudhra.we-have-a-problem.com
    dv-g3b-aaa-noct-emudhra.we-have-a-problem.com
    dv-g3b-emudhra.we-have-a-problem.com
    dv-g3b-noct-emudhra.we-have-a-problem.com
    dv-g3c-aaa-emudhra.we-have-a-problem.com
    dv-g3c-emudhra.we-have-a-problem.com
    ev-g3b-aaa-emudhra.we-have-a-problem.com
    ev-g3b-emudhra.we-have-a-problem.com
    ev-g3c-aaa-emudhra.we-have-a-problem.com
    ev-g3c-emudhra.we-have-a-problem.com
    ov-g3b-aaa-emudhra.we-have-a-problem.com
    ov-g3b-emudhra.we-have-a-problem.com
    ov-g3c-aaa-emudhra.we-have-a-problem.com
    ov-g3c-emudhra.we-have-a-problem.com
"
allowed_hosts="services.gradle.org"

# Every JDK on the filesystem, by the real path of its blocked.certs, plus the ones the environment points at
jdks=""
for java_home in ${JAVA_HOME:-} ${JAVA_LTS_HOME:-} ${JAVA_CURRENT_HOME:-}; do
    if [ ! -f "${java_home}/lib/security/blocked.certs" ]; then
        echo "FAIL    ${java_home}/lib/security/blocked.certs not found" >&2
        exit 1
    fi
done
for file in ${JAVA_HOME:+${JAVA_HOME}/lib/security/blocked.certs} \
        ${JAVA_LTS_HOME:+${JAVA_LTS_HOME}/lib/security/blocked.certs} \
        ${JAVA_CURRENT_HOME:+${JAVA_CURRENT_HOME}/lib/security/blocked.certs} \
        $(find / -xdev \( -path /proc -o -path /sys \) -prune -o -path '*/lib/security/blocked.certs' -print 2>/dev/null); do
    java_home="$(dirname "$(dirname "$(dirname "$(readlink -f "${file}")")")")"
    case " ${jdks} " in
        *" ${java_home} "*) ;;
        *) jdks="${jdks} ${java_home}" ;;
    esac
done
if [ -z "${jdks}" ]; then
    echo "FAIL    no JDK found" >&2
    exit 1
fi

failed=0
for java_home in ${jdks}; do
    echo "Checking ${java_home}"
    if [ ! -x "${java_home}/bin/java" ]; then
        echo "FAIL    ${java_home}/bin/java not found"
        failed=1
        continue
    fi

    present=0
    for fingerprint in ${fingerprints}; do
        if grep -qxF "${fingerprint}" "${java_home}/lib/security/blocked.certs"; then
            present=$((present + 1))
        else
            echo "FAIL    ${fingerprint} missing from ${java_home}/lib/security/blocked.certs"
        fi
    done
    duplicates=$(grep -E '^[0-9A-F]{64}$' "${java_home}/lib/security/blocked.certs" | sort | uniq -d | wc -l)
    if [ "${present}" -eq "${expected}" ] && [ "${duplicates}" -eq 0 ]; then
        echo "OK      blocked.certs has all ${expected} fingerprints, no duplicates"
    else
        echo "FAIL    blocked.certs has ${present} of ${expected} fingerprints, ${duplicates} duplicated"
        failed=1
    fi

    # shellcheck disable=SC2086
    if ! "${java_home}/bin/java" "${dir}/BlockedCertsProbe.java" --blocked ${blocked_hosts} --allowed ${allowed_hosts}; then
        failed=1
    fi
done

if [ "${failed}" -ne 0 ]; then
    echo "Blocked certificates check failed" >&2
    exit 1
fi
