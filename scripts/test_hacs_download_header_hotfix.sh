#!/bin/sh
# Offline executable smoke/regression test for the temporary HACS hotfix.
set -eu
ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
PATCHER="$ROOT/scripts/hacs_download_header_hotfix.sh"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
export HACS_BASE_FILE="$WORK/base.py"
export HACS_STATE_DIR="$WORK/state"
export HACS_NO_RESTART=1

cat > "$HACS_BASE_FILE" <<'PY'
class HacsBase:
    async def async_download_file(self, url, headers=None):
        request = await self.session.get(
            url=url,
            timeout=ClientTimeout(total=60),
            headers=headers,
        )
        if request.status == 200:
            return await request.read()
PY
cp "$HACS_BASE_FILE" "$WORK/original.py"
sh "$PATCHER" status
sh "$PATCHER" apply
grep -Fq 'max_field_size=64 * 1024,' "$HACS_BASE_FILE"
test "$(grep -Fc 'max_field_size=64 * 1024,' "$HACS_BASE_FILE")" = 1
sha256sum "$HACS_BASE_FILE" | awk '{print $1}' > "$WORK/first.sha"
sh "$PATCHER" apply
sha256sum "$HACS_BASE_FILE" | awk '{print $1}' > "$WORK/second.sha"
cmp "$WORK/first.sha" "$WORK/second.sha"
sh "$PATCHER" status
cp "$HACS_BASE_FILE" "$WORK/patched.py"
printf '\n# unexpected upgrade\n' >> "$HACS_BASE_FILE"
if sh "$PATCHER" rollback; then
    echo "FAIL: unsafe rollback was not blocked" >&2
    exit 1
fi
cp "$HACS_BASE_FILE" "$WORK/changed.py"
# A refused rollback must not modify the user's updated HACS source.
cmp "$WORK/changed.py" "$HACS_BASE_FILE"
cp "$WORK/patched.py" "$HACS_BASE_FILE"
sh "$PATCHER" rollback
cmp "$WORK/original.py" "$HACS_BASE_FILE"
[ ! -e "$HACS_STATE_DIR/base.py.patched.sha256" ]
[ ! -e "$HACS_STATE_DIR/base.py.original" ]
# Already-fixed version must be untouched and must not be rolled back.
cat > "$HACS_BASE_FILE" <<'PY'
async def async_download_file(self, url, headers=None):
    request = await self.session.get(
        url=url,
        headers=headers,
        max_field_size=64 * 1024,
    )
PY
cp "$HACS_BASE_FILE" "$WORK/official.py"
sh "$PATCHER" apply
cmp "$WORK/official.py" "$HACS_BASE_FILE"
# An unexpected HACS implementation must fail without altering source.
printf '%s\n' 'async def some_other_downloader():' '    pass' > "$HACS_BASE_FILE"
cp "$HACS_BASE_FILE" "$WORK/unknown.py"
if sh "$PATCHER" apply; then
    echo "FAIL: unsupported HACS source was patched" >&2
    exit 1
fi
cmp "$WORK/unknown.py" "$HACS_BASE_FILE"
echo "PASS: apply, idempotency, integrity guard, rollback, upstream-fixed noop and fail-closed behavior"
