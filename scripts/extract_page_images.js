(() => {
  const absolute = (value) => {
    if (!value) return null;
    try {
      const url = new URL(value, document.baseURI);
      return url.protocol === "http:" || url.protocol === "https:"
        ? url.href
        : null;
    } catch {
      return null;
    }
  };

  const canonical =
    document.querySelector('link[rel="canonical"]')?.href || location.href;
  const description =
    document.querySelector('meta[name="description"]')?.content ||
    document.querySelector('meta[property="og:description"]')?.content ||
    null;
  const ogImage = absolute(
    document.querySelector('meta[property="og:image"]')?.content,
  );

  const seen = new Set();
  const images = Array.from(document.images)
    .map((image, index) => {
      const url = absolute(image.currentSrc || image.src);
      if (!url || seen.has(url)) return null;
      seen.add(url);
      return {
        index,
        url,
        alt: image.alt || "",
        display_width: image.width || null,
        display_height: image.height || null,
        natural_width: image.naturalWidth || null,
        natural_height: image.naturalHeight || null,
        loading: image.loading || null,
        nearest_link: absolute(image.closest("a")?.href),
      };
    })
    .filter(Boolean)
    .filter(
      (image) =>
        (image.natural_width || 0) >= 120 &&
        (image.natural_height || 0) >= 120,
    );

  return JSON.stringify(
    {
      page_url: location.href,
      canonical_url: canonical,
      title: document.title,
      description,
      og_image: ogImage,
      images,
    },
    null,
    2,
  );
})()
