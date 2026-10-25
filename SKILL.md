---
name: product-image-sourcing
description: Research, compare, and download product-image references from a supplied image or description across Google, web search, Alibaba, Made-in-China, Global Sources, 1688, Amazon, Etsy, independent B2B manufacturer sites, and wholesale catalogs. Cover stone, marble sculpture, monuments, headstones, angels, Jesus and religious statues, fountains, garden art, and other physical products. Use whenever the user asks to find similar products, competitors, suppliers, factory listings, original image sources, or asks to collect and download product galleries from supplier or manufacturer websites, including “根据这张图找同类产品”, “找石雕/雕塑厂家”, “从独立站下载产品图”, “收集 B2B 竞品资料”, or “这张图来自哪里”. Do not use merely to generate or edit an image, publish a product, or source only licensed stock photography.
---

# B2B Product Image Sourcing

Turn a reference image or product description into an evidence-backed set of
comparable products, original image sources, and relevant supplier pages.
Optimize for traceability and useful visual comparison, not for claiming that a
decorative image is a verified product listing.

## Operating boundaries

- Treat marketplace images as research references unless the user supplies
  explicit reuse permission or a license. Do not present them as ready-to-use
  website assets.
- Preserve watermarks and visible source marks. Do not remove them, bypass
  logins or CAPTCHAs, or use non-public interfaces to obtain images.
- Separate a product page from an image search result or Pinterest pin. Use the
  original seller/manufacturer page when it can be found.
- Never invent a supplier, manufacturer, model, material grade, price, MOQ,
  lead time, license, or “customizable” claim. Mark unverified fields clearly.
- Link and date every result. A product that cannot be reopened should be marked
  unavailable rather than described as current.
- If a platform blocks access, say so and continue with accessible sources. Do
  not spend the task repeatedly retrying a blocked endpoint.

## Establish the brief

When the user supplies an image, inspect it with Codex's native image capability
first, preferably at original detail. When text and images disagree, preserve
both readings and make the visual evidence explicit.

Record the matching features that a useful result must share:

- product type and function;
- material, finish, color, and construction;
- shape, pose, proportions, and silhouette;
- distinctive ornaments or hardware;
- intended setting and buyer use;
- image angle, scene, and scale;
- visible text, watermark, logo, or SKU;
- features that are incidental and should not drive the query.

Infer one of these intents from the request:

| Intent | Typical ask | Primary deliverable |
| --- | --- | --- |
| Visual reference | “找同类图/近似款” | Closest matching product images |
| Supplier sourcing | “找厂家/供应商/报价线索” | Supplier or factory listings |
| Market scan | “看看有哪些产品/竞品” | Product pattern and source map |
| Licensed asset sourcing | “找可上官网的图” | Rights-cleared image sources |

Default to visual reference plus source discovery when intent is mixed. Ask a
question only when region, reuse permission, or sourcing quantity would
materially change the result; otherwise make the limitation visible and
proceed.

## Search and collect

Read [references/research-playbook.md](references/research-playbook.md) before
choosing platforms, queries, or a reverse-image-search route. Use the available
web search and browser tools rather than relying on memory.

1. Start with the exact product type and the two or three most distinctive
   visible features. Then broaden by material, style, and commercial terms such
   as `factory`, `manufacturer`, `wholesale`, `custom`, or the equivalent local
   marketplace terms.
2. Use reverse image search when the supplied image can be uploaded to a
   supported public search interface and access is permitted. Use text search
   to catch rephrased listings and supplier catalogs.
3. Search across more than one route when possible: general visual search,
   independent B2B manufacturer sites, wholesale catalogs, and marketplace
   pages. Search product categories, not just exact strings from the source.
4. Open the best source pages to confirm that the product still matches. A
   visually similar thumbnail in an article, mood board, or unrelated collection
   is not a substitute for the product page.
5. Deduplicate reposts of the same image. Prefer the earliest credible
   manufacturer, seller, or catalogue page; retain secondary pages only when
   they add information.
6. For each candidate, capture the product page URL, the image URL or local
   preview, platform, seller, matched features, differences, image quality,
   watermark status, rights status, and check date.

Use the current client date for `checked_at`. Do not claim live price or stock
unless it is visible and attributable to the linked page.

## Mine independent B2B sites

When the user asks for factories, suppliers, B2B websites, or downloads from
their sites, read
[references/stone-sculpture-sites.md](references/stone-sculpture-sites.md) for
stone-specific categories, query vocabulary, and a seed list. Treat that list as
a starting point whose pages must be rechecked, not as proof that a company is
active or owns every image.

For each promising domain:

1. Open its product index and identify the navigation or URL pattern used for
   products, collections, galleries, and individual product pages.
2. Inspect individual product pages rather than downloading every image visible
   on a home or category landing page. Landing images often mix logos, banners,
   unrelated projects, and lazy-loading placeholders.
3. Wait for lazy-loaded media, then collect resolved image URLs from the final
   DOM. Prefer the highest available version of the same product image. With an
   `agent-browser` session, scroll through the gallery and run:

   ```bash
   agent-browser eval --stdin < scripts/extract_page_images.js
   ```

4. Classify useful files as a hero view, alternate angle, detail, scale/context,
   drawing, factory, packaging, or video thumbnail. Skip logos, icons, QR codes,
   chat widgets, tracking pixels, and unrelated decorative modules.
5. Follow the site’s about, factory, quality-control, and contact pages when the
   user needs supplier verification. Keep those claims separate from visual
   similarity.

Independent manufacturer sites often use Common Crawl-style URL paths such as
`/product/`, `/products/`, `/product-category/`, `/collections/`, or
`/gallery/`. Use those patterns to find additional product and gallery pages,
but verify each page's actual content.

## Evaluate

Use a 100-point score as a decision aid, not false precision:

| Signal | Weight |
| --- | ---: |
| Visual similarity of form, material, and composition | 30 |
| Distinctive feature overlap | 20 |
| Same product function and category | 15 |
| Source authority and ability to contact/verify the seller | 15 |
| Image quality and usefulness as a reference | 10 |
| Source and licensing evidence completeness | 10 |

Classify the result:

- `near-match`: same product type and nearly all defining features align;
- `same-category`: product type fits, but shape, construction, material, or
  scale differs;
- `partial-match`: useful for one feature or style direction only;
- `irrelevant`: rejected and excluded from the main result.

Do not call products “同款” when only the subject matter is shared. For example,
two angel statues are not the same product if their pose, base architecture,
memorial function, and ornamentation differ.

Aim for 8–15 deduplicated candidates, with 3–5 closest matches surfaced first.
Stop expanding when new results only repeat known sources or no longer improve
coverage of the requested dimension.

## Build the deliverable

Store research under:

```text
research/<short-slug>/
|-- manifest.json
|-- images/
|-- candidates.csv
`-- report.html
```

Read [references/output-schema.md](references/output-schema.md) before creating
the manifest. Put downloaded research previews in `images/` and reference them
from `image_file`. Keep remote URLs for pages whose assets should not be copied.

Download public product images included in the manifest with the bounded
downloader:

```bash
python3 scripts/download_images.py \
  --manifest research/<short-slug>/manifest.json \
  --max-images 40 \
  --delay 1.0
```

The downloader saves supported raster images, preserves each image URL and
source page, records MIME type, byte size, dimensions when available, final URL,
and SHA-256, and updates `image_file` in the manifest. It skips duplicate image
content. Use `--overwrite` only when the user asks to replace an existing local
download.

Generate the tabular report with the bundled script:

```bash
python3 scripts/build_report.py \
  --manifest research/<short-slug>/manifest.json \
  --output research/<short-slug>/report.html
```

The script writes `candidates.csv` beside the report and sorts candidates by
score. Inspect the report and at least the top previews before presenting it.

In chat, lead with the closest matches rather than the search process:

1. one-sentence product/visual identification;
2. 3–5 best matches with local previews when available;
3. a compact table of source, match level, key similarities/differences, and
   rights status;
4. supplier leads when request intent includes sourcing;
5. access limits and facts that still need verification;
6. links to the local HTML report and CSV.

When the user only wants to know how to use the skill, show a short menu instead
of beginning a search:

- `“根据这张图，找 5 个最接近的同类产品和原始链接。”`
- `“以这张图为准，在 Alibaba / Made-in-China 找 10 个潜在供应商。”`
- `“去石雕 B2B 独立站找同类产品，下载产品页主图和多角度图。”`
- `“按天使、耶稣、墓碑、喷泉分类收集这些厂家网站的产品图。”`
- `“用文字描述找同类产品参考图，并比较造型、材质和款式。”`
- `“查这张图的原始出处，并列出各站点的授权或使用说明。”`

## Reference routing

- Read [references/research-playbook.md](references/research-playbook.md) for
  query patterns, platform selection, reverse-image-search tactics, and source
  verification.
- Read [references/stone-sculpture-sites.md](references/stone-sculpture-sites.md)
  for stone and sculpture discovery terms, site-mining patterns, and
  independently verified seed domains.
- Read [references/output-schema.md](references/output-schema.md) when building
  or debugging `manifest.json`.
