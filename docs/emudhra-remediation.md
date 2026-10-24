# eMudhra TLS remediation (2026-10-24)

**尚未部署，正式站仍是原版本。** This branch changes source/build inputs only.
It does not modify Windows trust, Caddy, production containers, networks or DBs.

## Evidence and scope

Official sources:
- [Render advisory](https://render.com/docs/advisory-emudhra): certifi >=2026.10.19;
  Node >=22.23.4/24.22.1/26.12.1; rustls-webpki >=0.103.16.
- [PSF guidance](https://discuss.python.org/t/information-for-python-users-regarding-emudhra-emsign-ca-certificate-security-incident/109576):
  pip >=26.2.2, uv >=0.13.4. The Docker/CI bootstrap wheel is SHA256-pinned.
- [Mozilla incident and cross-signs](https://bugzilla.mozilla.org/show_bug.cgi?id=2083449).
- [certifi removal fingerprints](https://github.com/certifi/python-certifi/pull/437/files)
  and [restoration of unaffected roots](https://github.com/certifi/python-certifi/pull/440).

The image removes only exact emSign ECC Root CA - G3 and AAA Certificate Services
fingerprints from distro CA files, then rebuilds the hashed CA directory. AAA is
an alternate cross-sign path, not itself a leaked key. G1/C1/C3 are not blanket-deleted.
The installed-artifact gate checks certifi, pip's vendored bundle, Playwright's
actual Node version/default roots, and both Linux system bundle and CApath.
Docker installs runtime requirements from uv.lock with artifact hashes.

The SSRF adapter now delegates the TLS handshake to urllib3, retaining DNS/IP
pinning but honoring Requests' CA selection, hostname checks and verification
bookkeeping. Explicit CAfile selection also fixes the SMTP context's system-CA
fallback. The internal gateway public CA is still appended to certifi at startup;
the resulting bundle is validated and remains selected when trust_env is disabled.

## Search mitigation and limitations

As of 2026-10-24 PyPI's latest primp is still 2.0.1; there is no verified patched
wheel to select. Upgrading a version declaration would not fix its Rust verifier.
Instead, our only search entry points use DDGS parsers through Requests transport,
with an explicit bundle and no primp Client construction. Brave/Yahoo text and
DuckDuckGo videos retain their request payloads/result parsing. Unknown or automatic
backends fail closed. No global monkey-patching is used. DDGS is pinned to 9.16.1
because this adapter depends on its private engine factory.

primp remains installed as DDGS's transitive dependency, **not claimed patched**.
Do not introduce direct DDGS/primp network calls. Offline tests fail if primp.Client
is constructed and exercise all three supported parsers. Requests does not spoof
browser TLS fingerprints, so live search providers may rate-limit differently;
external provider acceptance remains a deployment validation item. Once upstream
publishes verified patched wheels, re-evaluate this adapter and its tests.

Playwright 1.64.1's installed Node must pass the gate (24.22.1 on the tested wheel).
This does not certify browser binaries; install/validate patched browsers in an
isolated environment before enabling browser scraping. Existing content/image scraping contexts now enforce HTTPS certificate validation;
previous ignore_https_errors=True bypasses have been removed.

## Windows Caddy (separate, approval required)

The
[Go fix](https://go.dev/doc/devel/release#go1.26.10) requires Go >=1.26.10 or >=1.27.3.
Select an official checksum-verified Caddy build and inspect `caddy build-info`;
the Caddy version number alone is insufficient. The installer now refuses a binary
below that Go floor before writing its config/starting a service. It does not
automatically replace an existing binary. Windows CTL/revocation and the actual
running binary's rejection behavior are still unverified. No Windows changes are made by this PR.

## Review, deployment and rollback

1. Review CI's TLS trust regression image logs and the Web quality checks. The
   TLS job uses sparse source data, no secrets/production volumes, `--network none`
   for verification, and never publishes its image. It is evidence for installed
   TLS dependencies, not a full production deployment rehearsal.
2. Obtain separate approval for deployment/restart and any host security changes.
   Record the current container/image IDs, dependency report and gateway public-CA
   fingerprint again; keep a known-good image and compose/env configuration intact.
3. In an isolated build environment build the complete release image, run
   `python -m exchange_info.tls_audit --system`, then test startup with a **test**
   internal CA. Confirm internal gateway TLS and normal public HTTPS using only
   non-sensitive test traffic. Do not use compromised-key test endpoints.
4. Only after approval, deploy the new immutable image. Verify running package
   versions, effective CA bundle, internal connectivity and search/browser behavior.
   Never set verify=False, ignore_https_errors or restore G3/AAA to resolve errors.
5. If a release fails, stop the rollout and restore the recorded prior image/config
   through the approved deployment process. This restores availability but also
   reintroduces the documented TLS gaps; restrict affected workflows until a fixed
   release is ready. Host Caddy/Windows changes need their own backup and rollback.

No intrusion investigation or malicious-endpoint testing is part of this work.
