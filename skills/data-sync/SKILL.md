---
name: data-sync
description: Download data or model checkpoints from object storage to local training server. Checks target directory, avoids overwriting, supports resumable downloads.
when_to_use: need to download or sync data from cloud storage (S3/GCS/OSS/Azure Blob) to training machine
---

# Data Sync

## When to use
- Pulling training data or pretrained checkpoints to a new machine
- Syncing updated datasets before a training run
- Resuming interrupted large file downloads

## Procedure

### 1. Check target directory
```bash
ls -la ~/project/datasets/
df -h .  # Ensure enough disk space
```

### 2. Download with resume support
```bash
# Example with aws s3
aws s3 sync s3://bucket/datasets/ ~/project/datasets/ --no-progress

# Example with gsutil
gsutil -m rsync -r gs://bucket/datasets/ ~/project/datasets/

# Example with ossutil
ossutil cp oss://bucket/datasets/ ~/project/datasets/ -r --update
```

### 3. Verify integrity
```bash
# Check file counts match
find ~/project/datasets/ -type f | wc -l

# Check sizes (no zero-byte files)
find ~/project/datasets/ -type f -empty

# Optional: verify checksums
md5sum -c checksums.md5
```

## Safety rules
- **Never overwrite existing files** without `--update` flag (only newer files)
- **Check disk space first** — downloads failing mid-way leave partial files
- **Use `--dry-run`** first for large syncs to see what would change
- **Log the sync** — record what was pulled, when, from where

## Common patterns
| Scenario | Command flag |
|----------|-------------|
| Only download newer files | `--update` / `--newer-than` |
| Skip existing files entirely | `--skip-existing` / `--no-clobber` |
| Resume interrupted download | `--continue` / built-in for most tools |
| Exclude certain patterns | `--exclude "*.tmp"` |
