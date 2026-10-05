#!/usr/bin/env bash
set -u

prefix=$1
python_bin=$2
downloader=$3
metadata=$4
model_id=$5
revision=$6
endpoint=$7
target=$8

log="${prefix}.log"
pid_file="${prefix}.pid"
monitor_pid_file="${prefix}.monitor_pid"
heartbeat="${prefix}.heartbeat"
status="${prefix}.status"
receipt="${prefix}.download_receipt.json"
clean_manifest="${prefix}.model_files.sha256"
full_manifest="${prefix}.sha256"

mkdir -p "$(dirname "$prefix")"
if [[ -e "$target" ]] && [[ -n "$(find "$target" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null)" ]]; then
  echo "target_not_empty target=$target" >&2
  exit 2
fi

{
  echo "MONITOR_PID=$$"
  echo "START=$(date --iso-8601=seconds)"
  echo "ENDPOINT=$endpoint"
  echo "TOKEN_SENT=false"
  echo "HF_HUB_DISABLE_XET=1"
  echo "HF_HUB_ENABLE_HF_TRANSFER=0"
  echo "TARGET=$target"
} > "$heartbeat"
echo "$$" > "$monitor_pid_file"

"$python_bin" "$downloader" \
  --metadata "$metadata" \
  --model-id "$model_id" \
  --revision "$revision" \
  --endpoint "$endpoint" \
  --target "$target" \
  --output "$receipt" > "$log" 2>&1 &
pid=$!
echo "$pid" > "$pid_file"
echo "DOWNLOAD_PID=$pid" >> "$heartbeat"

while kill -0 "$pid" 2>/dev/null; do
  {
    echo "HEARTBEAT=$(date --iso-8601=seconds)"
    df -h /
    free -h
    du -sh "$target" 2>/dev/null || true
    ps -o pid=,ppid=,stat=,etime=,cmd= -p "$pid"
  } >> "$heartbeat"
  sleep 300
done

set +e
wait "$pid"
rc=$?
set -e
{
  echo "END=$(date --iso-8601=seconds)"
  echo "RC=$rc"
} >> "$status"

if [[ "$rc" -eq 0 ]]; then
  (
    cd "$target"
    find . -maxdepth 1 -type f -printf '%P\n' | LC_ALL=C sort | xargs sha256sum > "$clean_manifest"
    find . -type f -printf '%P\n' | LC_ALL=C sort | xargs sha256sum > "$full_manifest"
  )
fi

exit "$rc"
