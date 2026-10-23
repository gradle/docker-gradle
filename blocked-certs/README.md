# Blocked certificates

Every image adds the SHA-256 fingerprints in [`blocked.certs`](blocked.certs) to each of its JDKs'
`lib/security/blocked.certs`, so the JVM rejects any certificate chain that contains one of these certificates,
whichever trust store is used. Entries that a JDK already has are skipped, so the step does nothing once a JDK ships
them. The build fails if a JDK has no `blocked.certs`.

## eMudhra intermediates

[`emudhra/`](emudhra) holds the 16 compromised eMudhra intermediate CA certificates, revoked for CA compromise on
2026-10-18 and 2026-10-19: 8 issued by the emSign Root TLS/CS CA - G3 roots, and their 8 cross-signs by Sectigo's
AAA Certificate Services. OpenJDK blocked the same 16 certificates for CVE-2026-91403 (commit `8395142: CA Enhancements`,
17.0.21.0.2, 21.0.13.0.2, 25.0.5.0.2, 27.0.1.0.2); Temurin, Corretto and GraalVM releases don't include it yet.

`blocked.certs` has 48 fingerprints for them, because the JVM compares the SHA-256 of each certificate's DER encoding as
received. A copy of a certificate with the outer `signatureAlgorithm` NULL parameters toggled, or with an ECDSA
signature `s` replaced by `n - s`, still verifies and can be made without the CA key, so each needs its own entry: 2 per
RSA-signed certificate and 4 per ECDSA-signed one, 8 × 4 + 8 × 2 = 48. This is what OpenJDK's
`BlockedCertsConverter` generates from the PEMs:

```bash
# BlockedCertsConverter.java from openjdk make/jdk/src/classes/build/tools/blockedcertsconverter/
javac --add-exports java.base/sun.security.util=ALL-UNNAMED -d out BlockedCertsConverter.java
( echo '#! java BlockedCertsConverter SHA-256'; cat blocked-certs/emudhra/*.pem ) \
    | java --add-exports java.base/sun.security.util=ALL-UNNAMED -cp out build.tools.blockedcertsconverter.BlockedCertsConverter \
    > blocked-certs/blocked.certs
```

## Changing the list

Each image directory is its own Docker build context, so the Dockerfiles can't copy this file. Instead, each one
has the list inline, in its `BLOCKED_CERTS_SHA256` block, which `update.py` rewrites from `blocked.certs` on every run.
After changing `blocked.certs`, run `./toolbox.sh update.py`.

## Tests

`test/run.sh` and `test-graal/run.sh` run [`test/check.sh`](test/check.sh) in the image. For every JDK in the image, it
checks that `blocked.certs` has all fingerprints, then uses [`BlockedCertsProbe`](test/BlockedCertsProbe.java) to
connect to test hosts that serve chains through each of the 16 intermediates. Every connection has to fail because a
certificate is blocked, or because the JDK trusts none of the chain's issuers. A connection to services.gradle.org must
still succeed.
