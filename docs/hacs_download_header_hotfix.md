# Temporary HACS download hotfix — automated local deployment

**Scope:** HACS itself; applies to *all* HACS downloads, including Frank Energie, DeltaSol KM2, EV Smart Charging and others. It does not modify these integrations or their release archives.

**Why:** As of 2026-10-24, GitHub's `Content-Security-Policy` response header may exceed `aiohttp`'s default 8,190-byte per-field limit. HACS 2.0.5 then aborts with `LineTooLong` from `custom_components/hacs/base.py`, before downloading release content.

- [Upstream HACS issue #5643](https://github.com/hacs/integration/issues/5643)
- [Upstream patch PR #5644](https://github.com/hacs/integration/pull/5644)
- [Our tracked operational issue #6](https://github.com/npinguin/home-assistant-frank_energie/issues/6)
- [Tested installer script](../scripts/hacs_download_header_hotfix.sh)
- [Script CI regression test](https://github.com/npinguin/home-assistant-frank_energie/actions/workflows/hacs_download_header_hotfix_test.yml)

## One-time deployment on Home Assistant OS

Run **in the Home Assistant Terminal & SSH add-on**, not a command-line console on a different PC. The add-on must expose `/config` and have write access. The installer calls `ha core restart` if the `ha` CLI is available.

```sh
wget -qO /config/hacs_download_header_hotfix.sh https://raw.githubusercontent.com/npinguin/home-assistant-frank_energie/main/scripts/hacs_download_header_hotfix.sh && sh /config/hacs_download_header_hotfix.sh apply
```

This performs one idempotent, scoped patch in `/config/custom_components/hacs/base.py`:

```diff
 request = await self.session.get(
     url=url,
     timeout=ClientTimeout(total=60),
     headers=headers,
+    max_field_size=64 * 1024,
 )
```

The installer checks for the exact HACS 2.0.5 call pattern, makes a permanent local backup in `/config/.hacs-download-header-hotfix/`, checks the patched source, records its SHA-256, atomically replaces the file and restarts Home Assistant Core (if `ha` is available). It fails closed if it sees an unfamiliar downloader or a changed previous installation, rather than corrupting HACS. **The GitHub Action validates the script but cannot deploy to your Home Assistant without a connected local runner or credentials.** The one-time command must be executed on the HA host.

For installations without Home Assistant `ha` command, restart HA Core through the web UI after installation. If you want to choose when to restart:

```sh
HACS_NO_RESTART=1 sh /config/hacs_download_header_hotfix.sh apply
```

## Verify and retry

```sh
sh /config/hacs_download_header_hotfix.sh status
```

Retry the HACS installation/update after Home Assistant Core restart:

- Frank Energie: [v2026.10.23.1](https://github.com/npinguin/home-assistant-frank_energie/releases/tag/v2026.10.23.1), `frank_energie.zip`.
- DeltaSol KM2: [1.2.6](https://github.com/npinguin/hass-Deltasol-KM2/releases/tag/1.2.6), `deltasol.zip`.

These are **two different integration repositories**, but the same central HACS downloader. The patch enables ongoing automated updates through HACS; no per-integration patching or manual ZIP copying is needed. Actual download and runtime success still require verification on the device.

If you also see a URL such as `.../archive/refs/heads/v2.6.0-rc.6.zip` for EV Smart Charging, that is an *additional* branch-versus-tag selection problem: this ref is a tag, not an existing branch, and will still need correcting even after HACS can read oversized headers.

## Rollback

```sh
sh /config/hacs_download_header_hotfix.sh rollback
```

Only restores the backed-up HACS `base.py` if the current file still exactly matches the patched SHA-256. If HACS itself has been updated, rollback **refuses to overwrite the newer file**. After the official HACS fix is installed, stop using this workaround; an official version with `max_field_size` is detected as already fixed.

## Engineering validation

`sh scripts/test_hacs_download_header_hotfix.sh` exercises clean install, repeat/idempotent invocation, prevention of unsafe rollback after foreign edits, valid rollback, official-patch no-op and rejecting unknown HACS file structures. The CI workflow executes it on every relevant script change. This is a file-installation test, not proof of live Home Assistant deployment.

**Security:** review the GitHub script before running; only run it from the intended repository. It does not request GitHub credentials, modify .storage registries, install Python packages, disable certificate checks or change the global Home Assistant HTTP parser configuration.
