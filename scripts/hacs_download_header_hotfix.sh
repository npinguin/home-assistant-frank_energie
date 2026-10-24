#!/bin/sh
# Temporary HACS 2.0.5 workaround for oversized GitHub CSP headers.
# See https://github.com/hacs/integration/issues/5643
# and https://github.com/hacs/integration/pull/5644
#
# Run in the Home Assistant Terminal & SSH add-on (where /config is mounted):
#   sh /config/hacs_download_header_hotfix.sh apply
#   sh /config/hacs_download_header_hotfix.sh status
#   sh /config/hacs_download_header_hotfix.sh rollback
#
# HACS_BASE_FILE and HACS_STATE_DIR may be overridden for offline tests.
# HACS_NO_RESTART=1 skips 'ha core restart'; restart HA Core manually then.
set -eu

ACTION="${1:-apply}"
TARGET="${HACS_BASE_FILE:-/config/custom_components/hacs/base.py}"
STATE_DIR="${HACS_STATE_DIR:-/config/.hacs-download-header-hotfix}"
ORIGINAL="$STATE_DIR/base.py.original"
APPLIED_HASH="$STATE_DIR/base.py.patched.sha256"
TMP=""
NEEDS_RESTART=0

notice() { printf '%s\n' "[hacs-hotfix] $*"; }
fail() { printf '%s\n' "[hacs-hotfix] ERROR: $*" >&2; exit 1; }
cleanup() {
    if [ -n "$TMP" ] && [ -f "$TMP" ]; then rm -f "$TMP"; fi
}
trap 'cleanup' EXIT
trap 'exit 1' HUP INT TERM

case "$ACTION" in
    apply|status|rollback) ;;
    *) fail "Usage: $0 {apply|status|rollback}" ;;
esac

[ -f "$TARGET" ] || fail "Missing HACS file: $TARGET. Use Home Assistant Terminal & SSH with /config mounted."
[ ! -L "$TARGET" ] || fail "Refusing to replace symlink: $TARGET"
command -v sha256sum >/dev/null 2>&1 || fail "sha256sum not installed; no safe rollback verification."
command -v awk >/dev/null 2>&1 || fail "awk not installed."

hash_file() { sha256sum "$1" | awk '{print $1}'; }

restart_core() {
    if [ "${HACS_NO_RESTART:-0}" = "1" ]; then
        notice "Restart skipped by HACS_NO_RESTART=1. Restart Home Assistant Core manually."
    elif command -v ha >/dev/null 2>&1; then
        notice "Restarting Home Assistant Core via 'ha core restart'..."
        ha core restart || fail "Patch installed, but 'ha core restart' failed. Restart Core manually."
    else
        notice "The 'ha' CLI is unavailable. Restart Home Assistant Core manually."
    fi
}

case "$ACTION" in
    status)
        if grep -Eq 'max_field_size[[:space:]]*=' "$TARGET"; then
            notice "HACS download header-size fix is present in $TARGET."
        else
            notice "HACS download header-size fix is NOT present in $TARGET."
        fi
        if [ -f "$ORIGINAL" ] && [ -f "$APPLIED_HASH" ]; then
            if [ "$(hash_file "$TARGET")" = "$(cat "$APPLIED_HASH")" ]; then
                notice "Tracked local hotfix is intact; rollback is available."
            else
                notice "HACS file changed since local hotfix; rollback is intentionally blocked."
            fi
        fi
        exit 0
        ;;
    rollback)
        [ -f "$ORIGINAL" ] && [ -f "$APPLIED_HASH" ] || fail "No tracked local hotfix to roll back."
        [ "$(hash_file "$TARGET")" = "$(cat "$APPLIED_HASH")" ] ||
            fail "HACS was changed after the hotfix; refusing to restore an old version over newer code."
        TMP="$(mktemp "${TARGET}.rollback.XXXXXX")"
        cp -p "$ORIGINAL" "$TMP"
        mv "$TMP" "$TARGET"
        TMP=""
        rm -f "$ORIGINAL" "$APPLIED_HASH"
        notice "Original HACS base.py restored. No custom integrations were modified."
        restart_core
        exit 0
        ;;
    apply)
        # An official HACS release may already contain this change.
        if grep -Eq 'max_field_size[[:space:]]*=' "$TARGET"; then
            notice "Already fixed or patched; no files changed and no restart required."
            exit 0
        fi
        # Refuse to overwrite an original backup if HACS has since been upgraded.
        [ ! -e "$ORIGINAL" ] && [ ! -e "$APPLIED_HASH" ] ||
            fail "Previous hotfix state exists but current HACS code differs; inspect HACS version before applying."
        [ "$(grep -Fc 'async def async_download_file(' "$TARGET")" = "1" ] ||
            fail "Unexpected HACS implementation: async_download_file anchor is not unique."
        [ "$(grep -Fc 'request = await self.session.get(' "$TARGET")" = "1" ] ||
            fail "Unexpected HACS implementation: session.get anchor is not unique."
        [ "$(grep -Fc 'headers=headers,' "$TARGET")" = "1" ] ||
            fail "Unexpected HACS implementation: headers argument is not unique."

        mkdir -p "$STATE_DIR"
        chmod 700 "$STATE_DIR"
        cp -p "$TARGET" "$ORIGINAL"
        TMP="$(mktemp "${TARGET}.hotfix.XXXXXX")"
        cp -p "$TARGET" "$TMP"
        awk '
            /async def async_download_file\(/ { in_method=1 }
            in_method && /request = await self\.session\.get\(/ { in_request=1 }
            in_request && /^[[:space:]]*headers=headers,[[:space:]]*$/ {
                print
                match($0, /[^[:space:]]/)
                indent=substr($0, 1, RSTART-1)
                print indent "max_field_size=64 * 1024,"
                count++
                in_request=0
                next
            }
            { print }
            END { if (count != 1) exit 4 }
        ' "$TARGET" > "$TMP" || fail "Patch anchor mismatch; original HACS file untouched."
        [ "$(grep -Fc 'max_field_size=64 * 1024,' "$TMP")" = "1" ] ||
            fail "Post-patch verification failed; original HACS file untouched."
        if command -v python3 >/dev/null 2>&1; then
            python3 -c 'import ast,sys; ast.parse(open(sys.argv[1], encoding="utf-8").read())' "$TMP" ||
                fail "Python syntax verification failed; original HACS file untouched."
        fi
        PATCHED_SHA="$(hash_file "$TMP")"
        mv "$TMP" "$TARGET"
        TMP=""
        printf '%s\n' "$PATCHED_SHA" > "$APPLIED_HASH"
        notice "Applied scoped 64 KiB aiohttp field limit to HACS downloads."
        notice "Original preserved in $ORIGINAL; rollback command is available."
        notice "No changes to Frank Energie, DeltaSol, other integrations or Home Assistant global HTTP settings."
        restart_core
        ;;
esac
