# Stone and Sculpture B2B Site Research

## Contents

- Search product families
- Commercial query patterns
- Independent-site discovery
- Seed domains
- Page and image extraction
- Download and use boundaries

## Search product families

Expand the visual subject into adjacent terms that buyers and manufacturers use:

| Family | Useful English terms | Useful Chinese terms |
| --- | --- | --- |
| Cemetery memorial | headstone, gravestone, tombstone, cemetery monument, grave marker, memorial statue, columbarium | 墓碑, 纪念碑, 墓地雕塑, 墓碑雕像, 骨灰龛 |
| Angel sculpture | angel statue, weeping angel, guardian angel, cherub, angel memorial, angel headstone | 天使雕塑, 天使雕像, 哭泣天使, 小天使, 天使墓碑 |
| Jesus and faith | Jesus Christ statue, Sacred Heart, Pieta, Madonna, Virgin Mary, Saint statue, church sculpture, religious relief | 耶稣像, 圣心耶稣, 圣母像, 哀悼基督, 圣徒像, 教堂雕塑 |
| Marble sculpture | marble statue, hand-carved sculpture, custom stone figure, bust, relief, classical replica | 大理石雕塑, 汉白玉雕像, 石雕人物, 半身像, 浮雕 |
| Garden and architecture | garden statue, fountain, planter, bench, fireplace, gazebo, balustrade, architectural carving | 园林雕塑, 喷泉, 花钵, 石凳, 壁炉, 凉亭, 建筑石雕 |
| Public and contemporary | public art, bronze/stone landmark, abstract sculpture, animal sculpture, memorial plaza sculpture | 城市雕塑, 地标雕塑, 抽象雕塑, 动物雕塑, 广场雕塑 |

Do not mechanically translate a caption. Stone sellers distinguish natural
marble, white marble, granite, limestone, travertine, sandstone, cast stone, and
bronze. Only use the material term supported by the source or user.

## Commercial query patterns

Combine appearance with supply language:

```text
"white marble angel headstone" manufacturer
"Jesus Christ statue" marble supplier factory
"custom monument" wholesale cemetery memorials
"hand carved marble sculpture" OEM factory
"marble fountain" "trade supplier" export
```

Add independent-site triggers:

```text
inurl:product "marble angel statue"
inurl:products "custom Jesus statue"
inurl:gallery "marble monuments"
"request a quote" "marble sculpture"
"factory direct" "angel headstone"
```

Use `site:` for a known manufacturer or marketplace. Use `-amazon -etsy` or
other exclusion terms when retail products hide factory and wholesale domains.

## Independent-site discovery

Search both product terms and site-structure terms. A genuine manufacturer site
often has a coherent product catalogue, factory/about pages, a contact or RFQ
route, and material or customization details. A visual inspiration board usually
does not.

Look for:

- product/collection/gallery navigation with many related items;
- manufacturer identity, location, production, packing, or factory evidence;
- stable product pages with descriptive names and SKUs;
- inquiry, quote, OEM/ODM, wholesale, or trade language;
- multiple angles and production/installation photos;
- contact details that can be checked independently;
- explicit copyright, image-use, or downloadable-media terms.

Do not infer that a site owns its factory merely because it uses “factory” in
marketing copy. Record the platform’s stated business role as a claim to verify.

## Seed domains

The following sites returned relevant public product or category pages during a
spot check on 2026-10-25. This is not an endorsement, a guarantee of current
availability, or proof of image ownership. Recheck the page and company every
time.

| Domain | Observed useful area |
| --- | --- |
| `you-fine.com` | Marble memorials and marble Jesus statues |
| `yun-sculpture.com` | Angel headstones, memorials, and Jesus statues |
| `dzsculpture.com` | Marble and bronze Jesus/religious sculpture |
| `premiumsculpture.com` | Marble angel headstone product pages |
| `milystatue.com` | Marble angel tombstone category |
| `finestsculpture.com` | White marble angel memorial products |
| `sculpturesgroup.com` | Marble memorials and monuments |
| `marbleism.com` | Marble tombstones and angel monuments |
| `cnstatue.com` | Marble religious and Jesus sculpture |
| `stonediscover.com` | Wholesale granite cemetery memorials |
| `supernovaintl.com` | Wholesale headstones and monuments |
| `monumentwarehouse.com` | Wholesale monuments for trade buyers |
| `interglostone.com` | Wholesale and manufactured granite monuments |
| `timelessbronze.com` | Marble Jesus statues and religious imagery |

Some sites block headless access, require regional selection, or hide images
behind lazy-loading. If access is denied, record that limitation and continue
with another accessible site. Do not treat a search snippet as a verified page.

## Page and image extraction

Open product pages with a browser-capable tool so JavaScript-rendered and
lazy-loaded images resolve. Scroll through galleries before reading the DOM.
Collect:

- canonical page URL and title;
- product name or SKU;
- seller/site;
- resolved `img.currentSrc`, `srcset`, or gallery data URLs;
- image role and visible watermark;
- natural image dimensions and useful file type;
- whether the image shows the product itself or only a project/context.

Prefer the original image URL over thumbnails, but do not manipulate URL
parameters to probe private or higher-resolution endpoints. If a gallery stores
image URLs in JSON or a media API, use only URLs the public page exposes.

When a page uses lazy loading, scroll and wait for the gallery before extracting.
Use the top-level product image as the primary candidate and alternate/detail
views as additional assets linked to the same candidate ID.

## Download and use boundaries

The user may request an internal archive of public product references. Before
download, confirm that the file is a public raster image, not an SVG payload,
tracking pixel, embedded icon, or private account asset. Keep downloads bounded,
rate-limited, and specific to the requested products.

Store source metadata with every file. A downloaded image remains
`reference-only` unless its page or written permission supports another status.
Do not remove watermarks, claim the image as original, or upload supplier images
to the company website without authorization. If the site disallows automated
access or bulk download, stop and report the restriction.
