# Research Manifest Schema

Use one JSON object per research task. The bundled report builder consumes this
schema and preserves the evidence in both HTML and CSV.

```json
{
  "title": "White marble angel memorial headstones",
  "slug": "white-marble-angel-headstone",
  "brief": {
    "input_type": "image",
    "goal": "Find visually similar products and traceable suppliers",
    "canonical_product": "Seated white marble angel cemetery headstone on a dark granite base",
    "required_features": [
      "seated angel",
      "black or dark granite base",
      "white marble figure",
      "memorial/headstone use"
    ],
    "distinctive_features": [
      "roses at the waist",
      "small cherub at lower left"
    ],
    "optional_features": [
      "engraved plaque",
      "cemetery setting"
    ],
    "exclusions": [
      "garden-only angel ornaments"
    ]
  },
  "queries": [
    "white marble seated angel headstone black granite base",
    "custom angel memorial monument manufacturer"
  ],
  "checked_at": "2026-10-25",
  "limitations": [
    "Pinterest results were treated as untraced references"
  ],
  "candidates": [
    {
      "id": "P01",
      "title": "Custom seated angel memorial with dark granite base",
      "platform": "Manufacturer website",
      "source_url": "https://example.com/product",
      "image_url": "https://example.com/image.jpg",
      "image_file": "images/p01.jpg",
      "seller": "Example Stone Works",
      "country": "China",
      "match_score": 88,
      "match_level": "near-match",
      "rights_status": "reference-only",
      "price": "[VERIFY]",
      "moq": "[VERIFY]",
      "matched_features": [
        "seated angel",
        "dark granite base",
        "white marble"
      ],
      "differences": [
        "different ornamentation"
      ],
      "image_quality": "high",
      "watermark": "visible supplier watermark",
      "checked_at": "2026-10-25",
      "notes": "Source page is public; verify current availability."
    }
  ]
}
```

## Required top-level fields

- `title`: Human-readable research title.
- `brief`: Object describing the target and match criteria.
- `checked_at`: `YYYY-MM-DD` date of the completed research.
- `candidates`: Non-empty array.

Optional top-level fields are `slug`, `queries`, and `limitations`.

## Required candidate fields

- `id`: Stable identifier unique within the manifest.
- `title`: Product title as observed on the source page.
- `platform`: Marketplace, manufacturer site, social site, or other source type.
- `source_url`: Canonical HTTP(S) product/source page.
- `match_score`: Integer from 0 to 100.
- `match_level`: `near-match`, `same-category`, `partial-match`, or `irrelevant`.
- `rights_status`: `licensed`, `supplier-permission`, `reference-only`, or
  `unknown`.
- `matched_features`: Array of supported overlap.
- `differences`: Array of material differences.
- `checked_at`: `YYYY-MM-DD` date checked.

Use `image_file` for a local preview relative to the manifest directory, or
`image_url` for a public image URL. Include both when practical. A candidate may
have neither only when the image is inaccessible; the report will show a text
card.

Optional fields include `seller`, `country`, `price`, `moq`, `image_quality`,
`watermark`, and `notes`. Never insert inferred values into price or MOQ; use a
`[VERIFY]` string instead.

## Download metadata

For an internal product-image archive, create the manifest first and then run
`scripts/download_images.py`. The script adds these candidate fields when an
image is downloaded:

- `image_file`: relative local preview path;
- `image_sha256`: content hash used for duplicate detection;
- `image_bytes`: downloaded byte size;
- `image_content_type`: HTTP MIME type;
- `image_format`: detected raster format;
- `image_width` and `image_height`: dimensions when detectable;
- `image_final_url`: URL after public redirects;
- `image_downloaded_at`: ISO date/time of download;
- `download_error`: failure reason, only when download failed;
- `duplicate_of`: earlier candidate ID whose local file was reused.

The script also writes a top-level `download_summary`. Preserve the original
`source_url` and `image_url`; download metadata does not change image rights.

## Output behavior

Run:

```bash
python3 scripts/build_report.py \
  --manifest research/<short-slug>/manifest.json \
  --output research/<short-slug>/report.html
```

The builder validates required fields and URLs, sorts by score, writes
`report.html`, and writes `candidates.csv` in the same directory.
