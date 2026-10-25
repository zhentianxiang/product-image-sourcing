#!/usr/bin/env python3
"""Download public research images listed in a product research manifest."""

from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
import re
import struct
import time
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import (
    HTTPRedirectHandler,
    Request,
    build_opener,
)


USER_AGENT = "ProductImageResearch/1.0 (local public-image research)"
ALLOWED_LEVELS = {"near-match", "same-category", "partial-match"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download product research images with provenance metadata."
    )
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--max-images", type=int, default=40)
    parser.add_argument("--delay", type=float, default=1.0)
    parser.add_argument("--max-bytes", type=int, default=25 * 1024 * 1024)
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def fail(message: str) -> None:
    raise ValueError(message)


def valid_http_url(value: object) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlparse(value)
    return (
        parsed.scheme in {"http", "https"}
        and bool(parsed.hostname)
        and parsed.username is None
        and parsed.password is None
    )


def public_host(hostname: str) -> bool:
    if hostname.lower() in {"localhost", "localhost.localdomain"}:
        return False
    try:
        ip = ipaddress.ip_address(hostname)
    except ValueError:
        # Resolve public domains through the system network path. Some managed
        # environments intentionally route DNS through a private proxy.
        return "." in hostname and not hostname.endswith(".local")
    return not (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    )


def public_url(value: object) -> bool:
    if not valid_http_url(value):
        return False
    return public_host(urlparse(value).hostname or "")


class SafeRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not public_url(newurl):
            raise HTTPError(
                newurl,
                code,
                "Redirect target is not a public HTTP(S) host",
                headers,
                fp,
            )
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def slugify(value: str, limit: int = 56) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return (normalized or "product")[:limit].rstrip("-")


def image_info(data: bytes) -> tuple[str, str, int | None, int | None] | None:
    if data.startswith(b"\xff\xd8\xff"):
        width = height = None
        position = 2
        while position + 9 < len(data):
            if data[position] != 0xFF:
                position += 1
                continue
            marker = data[position + 1]
            position += 2
            if marker in {0xD8, 0xD9} or 0xD0 <= marker <= 0xD7:
                continue
            if position + 2 > len(data):
                break
            segment_length = int.from_bytes(data[position : position + 2], "big")
            if segment_length < 2 or position + segment_length > len(data):
                break
            if marker in {
                0xC0,
                0xC1,
                0xC2,
                0xC3,
                0xC5,
                0xC6,
                0xC7,
                0xC9,
                0xCA,
                0xCB,
                0xCD,
                0xCE,
                0xCF,
            }:
                if segment_length >= 7:
                    height = int.from_bytes(data[position + 3 : position + 5], "big")
                    width = int.from_bytes(data[position + 5 : position + 7], "big")
                break
            position += segment_length
        return "JPEG", "jpg", width, height
    if data.startswith(b"\x89PNG\r\n\x1a\n") and len(data) >= 24:
        width, height = struct.unpack(">II", data[16:24])
        return "PNG", "png", width, height
    if data.startswith((b"GIF87a", b"GIF89a")) and len(data) >= 10:
        width, height = struct.unpack("<HH", data[6:10])
        return "GIF", "gif", width, height
    if len(data) >= 30 and data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        if data[12:16] == b"VP8X":
            width = 1 + int.from_bytes(data[24:27], "little")
            height = 1 + int.from_bytes(data[27:30], "little")
            return "WebP", "webp", width, height
        if data[12:16] == b"VP8 " and len(data) >= 30:
            frame = data[20:]
            if frame[3:6] == b"\x9d\x01\x2a":
                width = int.from_bytes(frame[6:8], "little") & 0x3FFF
                height = int.from_bytes(frame[8:10], "little") & 0x3FFF
                return "WebP", "webp", width, height
        if data[12:16] == b"VP8L" and len(data) >= 25 and data[20] == 0x2F:
            bits = int.from_bytes(data[21:25], "little")
            width = (bits & 0x3FFF) + 1
            height = ((bits >> 14) & 0x3FFF) + 1
            return "WebP", "webp", width, height
        return "WebP", "webp", None, None
    if len(data) >= 26 and data[:2] == b"BM":
        width, height = struct.unpack("<ii", data[18:26])
        return "BMP", "bmp", abs(width), abs(height)
    if len(data) >= 16 and data[4:8] == b"ftyp" and data[8:12] in {
        b"avif",
        b"avis",
        b"mif1",
    }:
        return "AVIF", "avif", None, None
    return None


def safe_filename(candidate: dict, extension: str) -> str:
    identifier = slugify(str(candidate.get("id", "image")), 24)
    title = slugify(str(candidate.get("title", "product")))
    return f"{identifier}-{title}.{extension}"


def fetch_image(url: str, max_bytes: int, timeout: float, opener) -> tuple[bytes, str, str]:
    request = Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "image/avif,image/webp,image/png,image/jpeg,image/gif;q=0.9,*/*;q=0.1",
            "Accept-Encoding": "identity",
        },
    )
    with opener.open(request, timeout=timeout) as response:
        final_url = response.geturl()
        if not public_url(final_url):
            fail("response redirected to a non-public host")
        content_type = response.headers.get_content_type().lower()
        declared_length = response.headers.get("Content-Length")
        if declared_length and int(declared_length) > max_bytes:
            fail(f"image exceeds {max_bytes} byte limit")
        data = bytearray()
        while True:
            chunk = response.read(min(1024 * 1024, max_bytes + 1 - len(data)))
            if not chunk:
                break
            data.extend(chunk)
            if len(data) > max_bytes:
                fail(f"image exceeds {max_bytes} byte limit")
    return bytes(data), content_type, final_url


def main() -> None:
    args = parse_args()
    if not 1 <= args.max_images <= 200:
        fail("--max-images must be between 1 and 200")
    if not 0 <= args.delay <= 30:
        fail("--delay must be between 0 and 30 seconds")
    if not 1024 <= args.max_bytes <= 100 * 1024 * 1024:
        fail("--max-bytes must be between 1024 and 104857600")
    if not 1 <= args.timeout <= 120:
        fail("--timeout must be between 1 and 120 seconds")

    manifest_path = args.manifest.resolve()
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"Cannot read manifest: {exc}")
    if not isinstance(manifest, dict) or not isinstance(manifest.get("candidates"), list):
        fail("manifest must contain a candidates array")

    candidates = [
        item
        for item in manifest["candidates"]
        if isinstance(item, dict)
        and item.get("match_level") in ALLOWED_LEVELS
        and item.get("image_url")
    ]
    candidates.sort(key=lambda item: (-int(item.get("match_score", 0)), str(item.get("id", ""))))
    if not candidates:
        print("No eligible image_url values found.")
        return
    if len(candidates) > args.max_images:
        print(
            f"Downloading the top {args.max_images} of {len(candidates)} eligible images."
        )
        candidates = candidates[: args.max_images]

    images_dir = manifest_path.parent / "images"
    images_dir.mkdir(parents=True, exist_ok=True)
    opener = build_opener(SafeRedirectHandler())
    hashes: dict[str, dict] = {}
    results = []
    downloaded_count = 0
    skipped_count = 0
    failed_count = 0

    for index, candidate in enumerate(candidates):
        identifier = str(candidate.get("id", f"candidate-{index + 1}"))
        candidate.pop("download_error", None)
        existing = candidate.get("image_file")
        if existing and not args.overwrite:
            existing_path = (manifest_path.parent / existing).resolve()
            try:
                existing_path.relative_to(manifest_path.parent)
            except ValueError:
                existing_path = None
            if existing_path and existing_path.is_file():
                if existing_path.stat().st_size <= args.max_bytes:
                    existing_data = existing_path.read_bytes()
                    existing_info = image_info(existing_data)
                    if existing_info:
                        image_format, _, width, height = existing_info
                        digest = hashlib.sha256(existing_data).hexdigest()
                        candidate["image_sha256"] = digest
                        candidate["image_bytes"] = len(existing_data)
                        candidate["image_format"] = image_format
                        candidate["image_width"] = width
                        candidate["image_height"] = height
                        hashes[digest] = {
                            "id": identifier,
                            "image_file": existing,
                        }
                skipped_count += 1
                results.append(
                    {"id": identifier, "status": "existing", "image_file": existing}
                )
                continue

        image_url = candidate["image_url"]
        if not public_url(image_url):
            candidate["download_error"] = "image_url is not a public HTTP(S) URL"
            failed_count += 1
            results.append(
                {"id": identifier, "status": "failed", "error": candidate["download_error"]}
            )
            continue

        if index:
            time.sleep(args.delay)
        try:
            data, content_type, final_url = fetch_image(
                image_url,
                args.max_bytes,
                args.timeout,
                opener,
            )
            info = image_info(data)
            if info is None:
                fail(f"unsupported or invalid raster image ({content_type})")
            image_format, extension, width, height = info
            digest = hashlib.sha256(data).hexdigest()
            if digest in hashes:
                duplicate = hashes[digest]
                candidate["image_file"] = duplicate["image_file"]
                candidate["duplicate_of"] = duplicate["id"]
                candidate["image_sha256"] = digest
                candidate["image_bytes"] = len(data)
                candidate["image_content_type"] = content_type
                candidate["image_format"] = image_format
                candidate["image_width"] = width
                candidate["image_height"] = height
                candidate["image_final_url"] = final_url
                candidate["image_downloaded_at"] = datetime.now().astimezone().isoformat(
                    timespec="seconds"
                )
                skipped_count += 1
                results.append(
                    {
                        "id": identifier,
                        "status": "duplicate",
                        "duplicate_of": duplicate["id"],
                    }
                )
                continue

            filename = safe_filename(candidate, extension)
            target = images_dir / filename
            counter = 2
            while target.exists() and args.overwrite is False:
                target = images_dir / (
                    f"{Path(filename).stem}-{counter}{Path(filename).suffix}"
                )
                counter += 1
            temporary = target.with_name(f".{target.name}.part")
            temporary.write_bytes(data)
            temporary.replace(target)

            image_file = target.relative_to(manifest_path.parent).as_posix()
            candidate["image_file"] = image_file
            candidate.pop("duplicate_of", None)
            candidate["image_sha256"] = digest
            candidate["image_bytes"] = len(data)
            candidate["image_content_type"] = content_type
            candidate["image_format"] = image_format
            candidate["image_width"] = width
            candidate["image_height"] = height
            candidate["image_final_url"] = final_url
            candidate["image_downloaded_at"] = datetime.now().astimezone().isoformat(
                timespec="seconds"
            )
            hashes[digest] = {"id": identifier, "image_file": image_file}
            downloaded_count += 1
            results.append(
                {
                    "id": identifier,
                    "status": "downloaded",
                    "image_file": image_file,
                    "bytes": len(data),
                }
            )
        except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
            candidate["download_error"] = str(exc)
            failed_count += 1
            results.append({"id": identifier, "status": "failed", "error": str(exc)})

    manifest["download_summary"] = {
        "completed_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "requested": len(candidates),
        "downloaded": downloaded_count,
        "duplicates_or_existing": skipped_count,
        "failed": failed_count,
        "max_images": args.max_images,
        "delay_seconds": args.delay,
        "max_bytes": args.max_bytes,
        "results": results,
    }
    temporary_manifest = manifest_path.with_name(f".{manifest_path.name}.part")
    temporary_manifest.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary_manifest.replace(manifest_path)
    print(f"Manifest updated: {manifest_path}")
    print(
        f"Downloaded: {downloaded_count}; existing/duplicate: {skipped_count}; "
        f"failed: {failed_count}"
    )
    for result in results:
        detail = result.get("image_file") or result.get("duplicate_of") or result.get("error")
        print(f"{result['id']}: {result['status']} {detail or ''}".rstrip())


if __name__ == "__main__":
    try:
        main()
    except ValueError as exc:
        raise SystemExit(f"error: {exc}")
