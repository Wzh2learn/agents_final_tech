from __future__ import annotations

import argparse
import http.client
import io
import json
import urllib.error
import urllib.request
import zipfile
from pathlib import Path


class RemoteZipError(ValueError):
    def __init__(self, code: str, **detail: object) -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"{code}: {detail}")


class RangeReader(io.RawIOBase):
    """Read a remote file through bounded HTTP Range requests only."""

    def __init__(
        self,
        url: str,
        size: int,
        *,
        block_size: int = 256 * 1024,
        max_fetch_bytes: int = 8 * 1024 * 1024,
        range_retries: int = 3,
    ) -> None:
        if size <= 0 or block_size <= 0 or max_fetch_bytes <= 0 or range_retries <= 0:
            raise RemoteZipError(
                "invalid_reader_bounds",
                size=size,
                block_size=block_size,
                max_fetch_bytes=max_fetch_bytes,
                range_retries=range_retries,
            )
        self.url = url
        self.size = size
        self.block_size = block_size
        self.max_fetch_bytes = max_fetch_bytes
        self.range_retries = range_retries
        self.position = 0
        self.fetched_bytes = 0
        self.request_count = 0
        self.retry_count = 0
        self.retry_errors: list[str] = []
        self.blocks: dict[int, bytes] = {}

    def readable(self) -> bool:
        return True

    def seekable(self) -> bool:
        return True

    def tell(self) -> int:
        return self.position

    def seek(self, offset: int, whence: int = io.SEEK_SET) -> int:
        if whence == io.SEEK_SET:
            position = offset
        elif whence == io.SEEK_CUR:
            position = self.position + offset
        elif whence == io.SEEK_END:
            position = self.size + offset
        else:
            raise RemoteZipError("invalid_seek_whence", whence=whence)
        if position < 0:
            raise RemoteZipError("seek_before_start", position=position)
        self.position = position
        return self.position

    def _fetch_block(self, index: int) -> bytes:
        if index in self.blocks:
            return self.blocks[index]
        start = index * self.block_size
        end = min(self.size, start + self.block_size) - 1
        fetch_size = end - start + 1
        if self.fetched_bytes + fetch_size > self.max_fetch_bytes:
            raise RemoteZipError(
                "remote_fetch_budget_exceeded",
                fetched_bytes=self.fetched_bytes,
                requested_bytes=fetch_size,
                max_fetch_bytes=self.max_fetch_bytes,
            )

        for _ in range(self.range_retries):
            request = urllib.request.Request(
                self.url,
                headers={
                    "Range": f"bytes={start}-{end}",
                    "User-Agent": "JinRongAgents-readonly-zip-auditor/1",
                },
            )
            try:
                with urllib.request.urlopen(request, timeout=60) as response:
                    status = getattr(response, "status", response.getcode())
                    content_length = response.headers.get("Content-Length")
                    if status != 206 or content_length != str(fetch_size):
                        raise RemoteZipError(
                            "range_request_failed",
                            status=status,
                            expected_bytes=fetch_size,
                            content_length=content_length,
                        )
                    data = response.read()
                if len(data) != fetch_size:
                    raise RemoteZipError(
                        "range_request_failed",
                        status=206,
                        expected_bytes=fetch_size,
                        actual_bytes=len(data),
                    )
                self.request_count += 1
                self.fetched_bytes += len(data)
                self.blocks[index] = data
                return data
            except http.client.IncompleteRead as exc:
                self.fetched_bytes += len(exc.partial)
                self.retry_count += 1
                self.retry_errors.append(f"IncompleteRead:{len(exc.partial)}")
            except (urllib.error.URLError, TimeoutError, OSError) as exc:
                self.retry_count += 1
                self.retry_errors.append(type(exc).__name__)
            if self.fetched_bytes > self.max_fetch_bytes:
                raise RemoteZipError(
                    "remote_fetch_budget_exceeded",
                    fetched_bytes=self.fetched_bytes,
                    max_fetch_bytes=self.max_fetch_bytes,
                )
        raise RemoteZipError(
            "range_request_retries_exhausted",
            index=index,
            retries=self.range_retries,
            errors=self.retry_errors[-self.range_retries :],
        )

    def read(self, size: int = -1) -> bytes:
        if self.position >= self.size:
            return b""
        if size is None or size < 0:
            size = self.size - self.position
        size = min(size, self.size - self.position)
        output = bytearray()
        while size > 0:
            index = self.position // self.block_size
            offset = self.position % self.block_size
            block = self._fetch_block(index)
            take = min(size, len(block) - offset)
            output.extend(block[offset : offset + take])
            self.position += take
            size -= take
        return bytes(output)


def _entry_record(info: zipfile.ZipInfo) -> dict[str, object]:
    return {
        "filename": info.filename,
        "is_dir": info.is_dir(),
        "file_size": info.file_size,
        "compress_size": info.compress_size,
        "crc32": f"{info.CRC:08x}",
        "compress_type": info.compress_type,
        "header_offset": info.header_offset,
        "date_time": list(info.date_time),
    }


def audit_remote_zip(
    url: str,
    size: int,
    *,
    block_size: int,
    max_fetch_bytes: int,
    range_retries: int,
) -> tuple[dict[str, object], list[dict[str, object]]]:
    reader = RangeReader(
        url,
        size,
        block_size=block_size,
        max_fetch_bytes=max_fetch_bytes,
        range_retries=range_retries,
    )
    try:
        with zipfile.ZipFile(reader) as archive:
            infos = archive.infolist()
    except (OSError, zipfile.BadZipFile, EOFError) as exc:
        raise RemoteZipError("remote_zip_parse_failed", error=str(exc)) from exc

    entries = [_entry_record(info) for info in infos]
    report = {
        "record_type": "remote_zip_structure_audit",
        "record_version": "remote-zip-structure-audit-v1",
        "status": "PASS_READ_ONLY_RANGE_AUDIT",
        "source": {
            "url": url,
            "archive_size": size,
        },
        "transport": {
            "mode": "HTTP_RANGE_ONLY",
            "block_size": block_size,
            "max_fetch_bytes": max_fetch_bytes,
            "fetched_bytes": reader.fetched_bytes,
            "range_requests": reader.request_count,
            "range_retries": reader.retry_count,
            "retry_error_types": reader.retry_errors,
            "full_archive_downloaded": False,
        },
        "zip": {
            "entry_count": len(entries),
            "file_count": sum(not entry["is_dir"] for entry in entries),
            "directory_count": sum(entry["is_dir"] for entry in entries),
            "total_uncompressed_bytes": sum(int(entry["file_size"]) for entry in entries if not entry["is_dir"]),
            "total_compressed_bytes": sum(int(entry["compress_size"]) for entry in entries if not entry["is_dir"]),
        },
        "extraction_performed": False,
        "adapter_run": False,
        "ground_truth_read": False,
    }
    return report, entries


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit a remote ZIP through bounded HTTP Range reads without downloading the archive"
    )
    parser.add_argument("--url", required=True)
    parser.add_argument("--size", required=True, type=int)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--entry-manifest", required=True, type=Path)
    parser.add_argument("--block-size", type=int, default=256 * 1024)
    parser.add_argument("--max-fetch-mib", type=int, default=8)
    parser.add_argument("--range-retries", type=int, default=3)
    args = parser.parse_args()

    report, entries = audit_remote_zip(
        args.url,
        args.size,
        block_size=args.block_size,
        max_fetch_bytes=args.max_fetch_mib * 1024 * 1024,
        range_retries=args.range_retries,
    )
    args.output.write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    args.entry_manifest.write_text(
        json.dumps({"entries": entries}, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({**report, "entry_manifest": str(args.entry_manifest)}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
