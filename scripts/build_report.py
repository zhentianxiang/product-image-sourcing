#!/usr/bin/env python3
"""Build a local, source-linked product research report from a JSON manifest."""

from __future__ import annotations

import argparse
import csv
import html
import json
import re
from datetime import date
from pathlib import Path
from urllib.parse import urlparse


MATCH_LEVELS = {"near-match", "same-category", "partial-match", "irrelevant"}
RIGHTS_STATUSES = {"licensed", "supplier-permission", "reference-only", "unknown"}
REQUIRED_TOP_LEVEL = {"title", "brief", "checked_at", "candidates"}
REQUIRED_CANDIDATE = {
    "id",
    "title",
    "platform",
    "source_url",
    "match_score",
    "match_level",
    "rights_status",
    "matched_features",
    "differences",
    "checked_at",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build an HTML/CSV report from a product research manifest."
    )
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def fail(message: str) -> None:
    raise ValueError(message)


def valid_http_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def valid_date(value: str) -> bool:
    try:
        date.fromisoformat(value)
    except (TypeError, ValueError):
        return False
    return bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", value))


def as_string_list(value: object, field: str, candidate_id: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        fail(f"{candidate_id}.{field} must be an array of strings")
    return value


def validate(manifest: dict) -> None:
    missing = REQUIRED_TOP_LEVEL - manifest.keys()
    if missing:
        fail(f"Missing top-level fields: {', '.join(sorted(missing))}")
    if not isinstance(manifest["title"], str) or not manifest["title"].strip():
        fail("title must be a non-empty string")
    if not isinstance(manifest["brief"], dict):
        fail("brief must be an object")
    for field in ("required_features", "distinctive_features", "optional_features", "exclusions"):
        if field in manifest["brief"]:
            as_string_list(manifest["brief"][field], f"brief.{field}", "manifest")
    for field in ("queries", "limitations"):
        if field in manifest:
            as_string_list(manifest[field], field, "manifest")
    if not valid_date(manifest["checked_at"]):
        fail("checked_at must use YYYY-MM-DD")
    candidates = manifest["candidates"]
    if not isinstance(candidates, list) or not candidates:
        fail("candidates must be a non-empty array")

    seen_ids: set[str] = set()
    for index, candidate in enumerate(candidates, start=1):
        if not isinstance(candidate, dict):
            fail(f"candidate {index} must be an object")
        candidate_id = str(candidate.get("id", f"candidate-{index}"))
        missing = REQUIRED_CANDIDATE - candidate.keys()
        if missing:
            fail(f"{candidate_id} is missing: {', '.join(sorted(missing))}")
        if candidate_id in seen_ids:
            fail(f"duplicate candidate id: {candidate_id}")
        seen_ids.add(candidate_id)
        if not isinstance(candidate["title"], str) or not candidate["title"].strip():
            fail(f"{candidate_id}.title must be a non-empty string")
        if not isinstance(candidate["platform"], str) or not candidate["platform"].strip():
            fail(f"{candidate_id}.platform must be a non-empty string")
        if not valid_http_url(candidate["source_url"]):
            fail(f"{candidate_id}.source_url must be an HTTP(S) URL")
        if (
            not isinstance(candidate["match_score"], int)
            or isinstance(candidate["match_score"], bool)
            or not 0 <= candidate["match_score"] <= 100
        ):
            fail(f"{candidate_id}.match_score must be an integer from 0 to 100")
        if candidate["match_level"] not in MATCH_LEVELS:
            fail(f"{candidate_id}.match_level is invalid")
        if candidate["rights_status"] not in RIGHTS_STATUSES:
            fail(f"{candidate_id}.rights_status is invalid")
        if not valid_date(candidate["checked_at"]):
            fail(f"{candidate_id}.checked_at must use YYYY-MM-DD")
        as_string_list(candidate["matched_features"], "matched_features", candidate_id)
        as_string_list(candidate["differences"], "differences", candidate_id)
        if candidate.get("image_url") and not valid_http_url(candidate["image_url"]):
            fail(f"{candidate_id}.image_url must be an HTTP(S) URL")
        if "image_file" in candidate and not isinstance(candidate["image_file"], str):
            fail(f"{candidate_id}.image_file must be a string")
        text_fields = (
            "price",
            "moq",
            "notes",
            "seller",
            "country",
            "image_quality",
            "watermark",
        )
        for field in text_fields:
            if field in candidate and not isinstance(candidate[field], str):
                fail(f"{candidate_id}.{field} must be a string")


def item_text(items: list[str], empty: str = "—") -> str:
    return " · ".join(html.escape(item) for item in items) if items else empty


def render_candidate(candidate: dict, manifest_dir: Path) -> str:
    title = html.escape(candidate["title"])
    source_url = html.escape(candidate["source_url"], quote=True)
    platform = html.escape(candidate["platform"])
    score = candidate["match_score"]
    level = html.escape(candidate["match_level"])
    rights = html.escape(candidate["rights_status"])
    matched = item_text(candidate["matched_features"])
    different = item_text(candidate["differences"])
    seller = html.escape(candidate.get("seller", "—"))
    country = html.escape(candidate.get("country", "—"))
    price = html.escape(candidate.get("price", "—"))
    moq = html.escape(candidate.get("moq", "—"))
    notes = html.escape(candidate.get("notes", "—"))

    image_file = candidate.get("image_file")
    image_url = candidate.get("image_url")
    if image_file:
        local_path = (manifest_dir / image_file).resolve()
        if local_path.is_file():
            try:
                rel = Path(local_path).relative_to(manifest_dir.resolve())
            except ValueError:
                preview = '<div class="missing">Preview must be inside manifest folder</div>'
            else:
                preview = (
                    f'<img src="{html.escape(rel.as_posix(), quote=True)}" '
                    f'alt="{title}">'
                )
        else:
            preview = '<div class="missing">Preview file not found</div>'
    elif image_url:
        preview = (
            f'<img src="{html.escape(image_url, quote=True)}" '
            f'alt="{title}">'
        )
    else:
        preview = '<div class="missing">No preview available</div>'

    return f"""
    <article class="card">
      <div class="preview">{preview}</div>
      <div class="body">
        <div class="meta"><span>{platform}</span><span class="score">{score}/100</span></div>
        <h2><a href="{source_url}" target="_blank" rel="noopener noreferrer">{title}</a></h2>
        <p class="badges"><span>{level}</span><span>{rights}</span></p>
        <dl>
          <dt>Seller / country</dt><dd>{seller} / {country}</dd>
          <dt>Matched</dt><dd>{matched}</dd>
          <dt>Differences</dt><dd>{different}</dd>
          <dt>Price / MOQ</dt><dd>{price} / {moq}</dd>
          <dt>Notes</dt><dd>{notes}</dd>
        </dl>
        <a class="source" href="{source_url}" target="_blank" rel="noopener noreferrer">Open original source ↗</a>
      </div>
    </article>
    """


def write_csv(path: Path, ranked: list[dict]) -> None:
    fieldnames = [
        "rank",
        "id",
        "title",
        "platform",
        "source_url",
        "image_url",
        "image_file",
        "seller",
        "country",
        "match_score",
        "match_level",
        "rights_status",
        "price",
        "moq",
        "matched_features",
        "differences",
        "image_quality",
        "watermark",
        "checked_at",
        "notes",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for rank, candidate in enumerate(ranked, start=1):
            row = {field: candidate.get(field, "") for field in fieldnames}
            row["rank"] = rank
            row["matched_features"] = " | ".join(candidate["matched_features"])
            row["differences"] = " | ".join(candidate["differences"])
            writer.writerow(row)


def main() -> None:
    args = parse_args()
    try:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"Cannot read manifest: {exc}")
    if not isinstance(manifest, dict):
        fail("manifest root must be an object")
    validate(manifest)

    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    manifest_dir = args.manifest.resolve().parent
    ranked = sorted(
        manifest["candidates"],
        key=lambda item: (-item["match_score"], item["id"]),
    )
    candidate_html = "\n".join(render_candidate(item, manifest_dir) for item in ranked)
    brief = manifest["brief"]
    required = brief.get("required_features", [])
    distinctive = brief.get("distinctive_features", [])
    exclusions = brief.get("exclusions", [])
    limitations = manifest.get("limitations", [])
    queries = manifest.get("queries", [])
    limitations_html = (
        "Limitations: "
        + " | ".join(html.escape(str(item)) for item in limitations)
        if limitations
        else "No additional limitations recorded."
    )

    page = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(manifest["title"])}</title>
  <style>
    :root {{ color-scheme: light; --ink:#17201d; --muted:#66736e; --line:#dce4df;
      --paper:#f5f7f4; --card:#fff; --accent:#176b4d; }}
    * {{ box-sizing: border-box; }}
    body {{ margin:0; font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",
      "PingFang SC",sans-serif; color:var(--ink); background:var(--paper); }}
    main {{ max-width:1180px; margin:auto; padding:40px 24px 72px; }}
    header {{ margin-bottom:28px; }}
    h1 {{ font-size:clamp(28px,4vw,48px); line-height:1.08; margin:0 0 12px; }}
    h2 {{ font-size:18px; line-height:1.3; margin:8px 0 10px; }}
    a {{ color:var(--accent); }}
    .lede, .muted {{ color:var(--muted); }}
    .brief {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr));
      gap:14px; margin:24px 0 32px; }}
    .brief div {{ background:var(--card); border:1px solid var(--line);
      border-radius:14px; padding:16px; }}
    .label {{ color:var(--muted); font-size:12px; text-transform:uppercase;
      letter-spacing:.08em; margin-bottom:6px; }}
    .grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(320px,1fr));
      gap:18px; }}
    .card {{ display:flex; flex-direction:column; background:var(--card);
      border:1px solid var(--line); border-radius:18px; overflow:hidden; }}
    .preview {{ aspect-ratio:4/3; background:#e9eeea; display:grid; place-items:center; }}
    .preview img {{ width:100%; height:100%; object-fit:contain; }}
    .missing {{ color:var(--muted); padding:24px; }}
    .body {{ padding:18px; }}
    .meta {{ display:flex; justify-content:space-between; gap:12px;
      color:var(--muted); font-size:13px; }}
    .score {{ color:var(--accent); font-weight:700; }}
    .badges {{ display:flex; flex-wrap:wrap; gap:6px; margin:0 0 14px; }}
    .badges span {{ border:1px solid var(--line); border-radius:999px;
      padding:2px 9px; font-size:12px; }}
    dl {{ display:grid; grid-template-columns:110px 1fr; gap:6px 12px;
      font-size:13px; margin:0 0 14px; }}
    dt {{ color:var(--muted); }}
    dd {{ margin:0; }}
    .source {{ font-weight:600; }}
    footer {{ border-top:1px solid var(--line); margin-top:32px; padding-top:20px;
      color:var(--muted); font-size:13px; }}
  </style>
</head>
<body>
<main>
  <header>
    <p class="muted">PRODUCT IMAGE SOURCING · CHECKED {html.escape(manifest["checked_at"])}</p>
    <h1>{html.escape(manifest["title"])}</h1>
    <p class="lede">{html.escape(str(brief.get("canonical_product", "")))}</p>
  </header>
  <section class="brief">
    <div><div class="label">Required</div>{item_text(required)}</div>
    <div><div class="label">Distinctive</div>{item_text(distinctive)}</div>
    <div><div class="label">Exclude</div>{item_text(exclusions)}</div>
    <div><div class="label">Queries</div>{item_text(queries)}</div>
  </section>
  <section class="grid">
  {candidate_html}
  </section>
  <footer>
    <strong>Use note:</strong> Publicly accessible images are not automatically
    licensed for republishing. Confirm rights before website, advertising, or
    print use.<br>
    {limitations_html}
  </footer>
</main>
</body>
</html>
"""
    output.write_text(page, encoding="utf-8")
    csv_path = output.with_name("candidates.csv")
    write_csv(csv_path, ranked)
    print(f"Wrote {output}")
    print(f"Wrote {csv_path}")
    print(f"Candidates: {len(ranked)}")


if __name__ == "__main__":
    try:
        main()
    except ValueError as exc:
        raise SystemExit(f"error: {exc}")
