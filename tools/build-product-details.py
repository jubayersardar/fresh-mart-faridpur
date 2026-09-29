"""Build one static, shareable detail page for each catalog item.

The catalog remains the single source of names, pack sizes, prices and photos.
Run after tools/build-catalog.py whenever tools/catalog-data.json changes.
"""

from __future__ import annotations

import html
import importlib.util
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parent.parent
CATALOG_BUILDER = ROOT / "tools" / "build-catalog.py"

spec = importlib.util.spec_from_file_location("freshmart_catalog_builder", CATALOG_BUILDER)
if spec is None or spec.loader is None:
    raise RuntimeError("Cannot load the catalog builder")
catalog = importlib.util.module_from_spec(spec)
spec.loader.exec_module(catalog)
VERSION = catalog.VERSION


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def icon(name: str) -> str:
    return catalog.icon(name)


def detail_href(item: dict) -> str:
    return f"product-{item['id']}.html"


def display_price(item: dict) -> str:
    amount = catalog.price_amount(item)
    return item.get("priceLabel") or (f"৳ {catalog.bn(amount)}" if amount else "দাম জেনে নিন")


def product_description(item: dict) -> str:
    return str(item.get("description") or "").strip()


def photo(item: dict, *, recommendation: bool = False) -> str:
    category_name, category_icon = catalog.CATEGORIES[item["category"]]
    image = catalog.local_image(item.get("image"))
    if image:
        eager = "loading=\"lazy\"" if recommendation else "loading=\"eager\" fetchpriority=\"high\""
        return (
            f'<img src="{esc(image)}" alt="Fresh Mart-এর {esc(item["name"])}" '
            f'width="900" height="900" {eager} decoding="async" />'
        )
    return (
        f'<div class="catalog-placeholder detail-placeholder category-{esc(item["category"])}" '
        f'role="img" aria-label="{esc(item["name"])} এর ছবি এখনো যোগ করা হয়নি">'
        f'{icon(category_icon)}<span>{esc(category_name)}</span>'
        '<small>ছবি শীঘ্রই আসছে</small></div>'
    )


def recommendations(current: dict, items: list[dict], limit: int = 4) -> list[dict]:
    others = [item for item in items if item["id"] != current["id"]]
    # Different products from the same aisle come first. A different pack size
    # is still a valid recommendation, but does not fill the entire row.
    ordered = sorted(
        others,
        key=lambda item: (
            item["category"] != current["category"],
            item["name"] == current["name"],
            not bool(item.get("image")),
            not bool(item.get("featured")),
            item["id"],
        ),
    )
    return ordered[:limit]


def render_recommendation(item: dict) -> str:
    name = esc(item["name"])
    category_name, _ = catalog.CATEGORIES[item["category"]]
    return f'''          <article class="detail-recommendation">
            <a class="detail-recommendation-media" href="{detail_href(item)}" aria-label="{name} বিস্তারিত দেখুন">{photo(item, recommendation=True)}</a>
            <div class="detail-recommendation-copy">
              <span class="detail-recommendation-category">{esc(category_name)}</span>
              <h3><a href="{detail_href(item)}">{name}</a></h3>
              <p>{esc(item['unit'])}</p>
              <div class="detail-recommendation-bottom"><strong>{esc(display_price(item))}</strong><a href="{detail_href(item)}" aria-label="{name} বিস্তারিত দেখুন">{icon('arrow')}</a></div>
            </div>
          </article>'''


def render(item: dict, items: list[dict], chrome: tuple[str, str, str, str, str]) -> str:
    sprite, header, order_bar, footer, mobile = chrome
    header = header.replace(
        '<a href="products.html" class="active" aria-current="page">',
        '<a href="products.html" class="active">',
        1,
    )
    mobile = mobile.replace(
        '<a href="products.html" aria-current="page">',
        '<a href="products.html" class="active">',
        1,
    )
    name = esc(item["name"])
    unit = esc(item["unit"])
    category_name, _ = catalog.CATEGORIES[item["category"]]
    category = esc(category_name)
    amount = catalog.price_amount(item)
    price = esc(display_price(item))
    description = product_description(item)
    description_html = f'<p class="detail-description">{esc(description)}</p>' if description else ""
    meta_copy = esc(
        f"{item['name']} ({item['unit']}) — Fresh Mart Faridpur-এর {category_name} পণ্য। "
        "পরিমাণ বেছে WhatsApp-এ অর্ডারের অনুরোধ করুন; দাম, মজুত ও ডেলিভারি নিশ্চিত করুন।"
    )
    source = item.get("source")
    source_link = ""
    if item.get("image") and source and str(source).startswith("https://www.facebook.com/"):
        source_link = f'<a class="detail-photo-source" href="{esc(source)}" target="_blank" rel="noopener noreferrer">Facebook-এ পণ্যের ছবি দেখুন {icon("arrow")}</a>'
    recommendations_html = "\n".join(render_recommendation(other) for other in recommendations(item, items))
    category_link = f"products.html#{esc(item['category'])}"
    return f'''<!DOCTYPE html>
<html lang="bn">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{name} · {unit} — Fresh Mart Faridpur</title>
  <meta name="description" content="{meta_copy}" />
  <meta name="theme-color" content="#174b35" />
  <meta property="og:type" content="product" />
  <meta property="og:locale" content="bn_BD" />
  <meta property="og:title" content="{name} · {unit} — Fresh Mart Faridpur" />
  <meta property="og:description" content="{meta_copy}" />
  <link rel="icon" type="image/png" href="assets/favicon.png" />
  <link rel="apple-touch-icon" href="assets/favicon.png" />
  <link rel="stylesheet" href="css/fonts.css?v={VERSION}" />
  <link rel="stylesheet" href="css/style.css?v={VERSION}" />
  <link rel="stylesheet" href="css/home.css?v={VERSION}" />
  <link rel="stylesheet" href="css/catalog.css?v={VERSION}" />
  <link rel="stylesheet" href="css/product-detail.css?v={VERSION}" />
  <script src="js/main.js?v={VERSION}" defer></script>
</head>
<body class="home-page catalog-page product-detail-page">
  <a class="skip-link" href="#main-content">মূল বিষয়বস্তুতে যান</a>
  {sprite}

{header}
  <main id="main-content" tabindex="-1">
    <div class="container">
      <nav class="catalog-breadcrumb detail-breadcrumb" aria-label="অবস্থান">
        <a href="index.html">হোম</a><span aria-hidden="true">/</span>
        <a href="products.html">পণ্য ও মূল্য</a><span aria-hidden="true">/</span>
        <a href="{category_link}">{category}</a><span aria-hidden="true">/</span>
        <span aria-current="page">{name}</span>
      </nav>
    </div>
    <section class="detail-product-section" id="direct-products" aria-labelledby="product-heading">
      <div class="container" id="directProductsGrid">
        <article class="direct-card detail-card" id="product-{esc(item['id'])}"
          data-product-id="{esc(item['id'])}" data-category="{esc(item['category'])}"
          data-name="{name}" data-unit="{unit}" data-price="{esc(amount)}">
          <div class="detail-visual-wrap">
            <div class="direct-card-photo detail-photo">
              {photo(item)}
              <span class="direct-badge badge-{esc(item['category'])}">{category}</span>
            </div>
            {source_link}
          </div>
          <div class="direct-card-info detail-info">
            <span class="home-eyebrow">Fresh Mart Faridpur · {category}</span>
            <h1 class="direct-card-name" id="product-heading">{name}</h1>
            <p class="detail-unit">প্রতি প্যাক: <strong>{unit}</strong></p>
            {description_html}
            <div class="detail-value-panel">
              <span>তালিকামূল্য</span>
              <div class="direct-card-price-row"><strong class="direct-card-price">{price}</strong><small>/ {unit}</small></div>
              <p>তালিকামূল্য বদলাতে পারে। চূড়ান্ত মূল্য ও ডেলিভারি খরচ নিশ্চিত করুন।</p>
            </div>
            <div class="detail-order-panel">
              <span class="detail-order-label">কয়টি ইউনিট চান?</span>
              <p>প্রতি ধাপে উপরে দেখানো পরিমাণ ({unit}) যোগ হবে।</p>
              <div class="direct-card-controls">
                <div class="direct-qty-box" aria-label="প্যাকের সংখ্যা বেছে নিন">
                  <button type="button" class="direct-qty-btn minus" aria-label="{name} এর পরিমাণ কমান" disabled>{icon('minus')}</button>
                  <span class="direct-qty-val" role="status" aria-live="polite" aria-label="{name} এর নির্বাচিত পরিমাণ">০১</span>
                  <button type="button" class="direct-qty-btn plus" aria-label="{name} এর পরিমাণ বাড়ান">{icon('plus')}</button>
                </div>
                <a href="{esc(catalog.order_link(item))}" target="_blank" rel="noopener noreferrer" class="direct-btn-order" aria-label="{name} WhatsApp-এ অর্ডারের অনুরোধ করুন">{icon('chat')}এই পণ্য অর্ডার করুন</a>
              </div>
              <button class="direct-btn-add" type="button">অর্ডার তালিকায় যোগ করুন{icon('plus')}</button>
              <noscript><p class="catalog-no-script">অর্ডার করুন বাটন একটি প্যাকের WhatsApp খসড়া খুলবে। অন্য পরিমাণ চাইলে বার্তায় লিখুন।</p></noscript>
            </div>
            <div class="detail-service-strip" aria-label="অর্ডারের তথ্য">
              <span>{icon('truck')} ফরিদপুর শহরে হোম ডেলিভারি</span>
              <span>{icon('phone')} <a href="tel:+8801611402642" lang="en">01611-402642</a></span>
            </div>
          </div>
        </article>
      </div>
    </section>
    <section class="detail-recommendations" aria-labelledby="recommendations-heading">
      <div class="container">
        <div class="detail-recommendations-heading">
          <div><span class="home-eyebrow">আরও কিছু বেছে নিন</span><h2 id="recommendations-heading">আপনার জন্য আরও পণ্য</h2></div>
          <a class="text-link" href="products.html">সব পণ্য দেখুন {icon('arrow')}</a>
        </div>
        <div class="detail-recommendations-grid">
{recommendations_html}
        </div>
      </div>
    </section>
  </main>

{order_bar}

{footer}
{mobile}
</body>
</html>
'''


def main() -> None:
    items = catalog.read_catalog()
    source = (ROOT / "index.html").read_text(encoding="utf-8-sig")
    shared_chrome = catalog.chrome(source)
    rendered = [(ROOT / detail_href(item), render(item, items, shared_chrome)) for item in items]
    if len({path.name for path, _ in rendered}) != len(items):
        raise ValueError("Duplicate product detail output path")
    for path, content in rendered:
        if not re.search(r'<h1\b[^>]*>', content) or content.count('class="direct-card detail-card"') != 1:
            raise ValueError(f"Malformed detail page: {path.name}")
        path.write_text(content, encoding="utf-8")
    print(f"Generated {len(rendered)} individual product detail pages")


if __name__ == "__main__":
    main()
