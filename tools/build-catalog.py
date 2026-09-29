"""Generate the public, static catalog from the private product data.

Run `python tools/build-catalog.py` for products.html. Add --home to update
only the homepage product grid and category filters after selecting 12
featured products with verified photos in catalog-data.json.
"""

import argparse
import html
import json
import math
from pathlib import Path
import re
from urllib.parse import quote, urlsplit


ROOT = Path(__file__).resolve().parent.parent
VERSION = "20260929-2"
FACEBOOK = "https://www.facebook.com/profile.php?id=61591856639645"
PRICE_SOURCE = (
    "https://www.facebook.com/permalink.php?"
    "story_fbid=pfbid04ZGUx91zq1nqbXti2hUuqAwVh52MddFHdw2s3hDpwGx6qcRb5GnSmVL7oMkwgk7Ql"
    "&id=61591856639645"
)
CATEGORIES = {
    "veg": ("শাকসবজি", "leaf"),
    "fish": ("মাছ", "fish"),
    "meat": ("মাংস ও চিকেন", "meat"),
    "spice": ("মসলা বাটা", "spice"),
    "dairy": ("অন্যান্য", "box"),
    "combos": ("কম্বো প্যাক", "bag"),
}
DIGITS = str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯")


def esc(value):
    return html.escape(str(value), quote=True)


def bn(value):
    return str(value).translate(DIGITS)


def icon(name):
    return f'<svg class="icon" aria-hidden="true"><use href="#i-{esc(name)}"/></svg>'


def local_image(value):
    if not value:
        return None
    image = str(value).replace("\\", "/")
    if not image.startswith("assets/") or urlsplit(image).scheme or ".." in Path(image).parts:
        raise ValueError(f"Image must be a workspace asset: {image}")
    path = (ROOT / image).resolve()
    if not path.is_relative_to((ROOT / "assets").resolve()) or not path.is_file():
        raise ValueError(f"Missing image: {image}")
    return image


def read_catalog():
    items = json.loads((ROOT / "tools/catalog-data.json").read_text(encoding="utf-8-sig"))
    if not isinstance(items, list) or not items:
        raise ValueError("catalog-data.json must contain a nonempty array")
    ids = set()
    for item in items:
        product_id = item.get("id", "")
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", product_id) or product_id in ids:
            raise ValueError(f"Invalid or duplicated product id: {product_id}")
        ids.add(product_id)
        if item.get("category") not in CATEGORIES or not item.get("name") or not item.get("unit"):
            raise ValueError(f"Missing name, unit, or category: {product_id}")
        price = item.get("price")
        if price is not None and (isinstance(price, bool) or not isinstance(price, (int, float)) or not math.isfinite(price) or price <= 0):
            raise ValueError(f"Price must be positive or null: {product_id}")
        local_image(item.get("image"))
    return items


def price_amount(item):
    price = item.get("price")
    return "" if price is None else f"{price:g}"


def order_link(item):
    amount = price_amount(item)
    price_line = f"আনুমানিক তালিকামূল্য: ৳{bn(amount)}" if amount else "পণ্যের দাম ও প্যাকের পরিমাণ জানাবেন।"
    text = "\n".join([
        "আসসালামু আলাইকুম, Fresh Mart Faridpur থেকে অর্ডার করতে চাই:",
        f"• {item['name']} ({item['unit']}) × ১",
        price_line,
        "দয়া করে প্রাপ্যতা, পরিমাণ, চূড়ান্ত দাম ও ডেলিভারি চার্জ জানিয়ে অর্ডার নিশ্চিত করুন।",
    ])
    return "https://wa.me/8801611402642?text=" + quote(text, safe="")


def render_card(item, home=False):
    name, unit, category = item["name"], item["unit"], item["category"]
    detail_href = f"product-{item['id']}.html"
    category_name, category_icon = CATEGORIES[category]
    custom_search = item.get("search", "")
    if isinstance(custom_search, list):
        custom_search = " ".join(str(value) for value in custom_search)
    search_parts = [str(custom_search), category_name]
    if category == "veg":
        search_parts.append("সবজি শাকসবজি")
    elif category == "fish":
        search_parts.append("মাছ")
    if "chicken" in item["id"]:
        search_parts.append("চিকেন মুরগি")
    search = " ".join(search_parts).strip()
    image = local_image(item.get("image"))
    amount = price_amount(item)
    badge = f'<span class="direct-badge badge-{esc(category)}">{esc(category_name)}</span>'
    if image:
        photo = f'<img src="{esc(image)}" alt="Fresh Mart-এর {esc(name)}" width="720" height="720" loading="lazy" decoding="async" />{badge}'
        visual = f'<a class="direct-card-photo" href="{esc(detail_href)}" aria-label="{esc(name)} পণ্যের বিস্তারিত দেখুন">{photo}</a>'
    else:
        visual = f'<a class="catalog-placeholder category-{esc(category)}" href="{esc(detail_href)}" aria-label="{esc(name)} পণ্যের বিস্তারিত দেখুন">{icon(category_icon)}<span>{esc(category_name)}</span><small>বিস্তারিত দেখুন</small></a>'
    price_label = item.get("priceLabel") or ("৳ " + bn(amount) if amount else "দাম জেনে নিন")
    unit_copy = esc(unit)
    if item.get("description"):
        unit_copy += " · " + esc(item["description"])
    no_photo = " direct-card--without-photo" if not image else ""
    price_caption = (' <small>/ ' + esc(unit) + '</small>') if home and amount else ""
    catalog_caption = "" if home else f'<small class="catalog-price-caption">{"তালিকামূল্য · " + esc(unit) if amount else "চূড়ান্ত মূল্য যোগাযোগে নিশ্চিত করুন"}</small>'
    return f'''          <article class="direct-card{no_photo}" id="product-{esc(item['id'])}" data-product-id="{esc(item['id'])}" data-category="{esc(category)}" data-name="{esc(name)}" data-unit="{esc(unit)}" data-price="{esc(amount)}" data-search="{esc(search)}">
            {visual}
            <div class="direct-card-info">
              <h3 class="direct-card-name"><a href="{esc(detail_href)}">{esc(name)}</a></h3>
              <p class="direct-card-unit">{unit_copy}</p>
              <div class="direct-card-price-row"><span class="direct-card-price">{esc(price_label)}{price_caption}</span>{catalog_caption}</div>
              <div class="direct-card-controls">
                <div class="direct-qty-box"><button type="button" class="direct-qty-btn minus" aria-label="{esc(name)} এর পরিমাণ কমান" disabled>{icon('minus')}</button><span class="direct-qty-val" role="status" aria-live="polite" aria-label="{esc(name)} এর নির্বাচিত পরিমাণ">০১</span><button type="button" class="direct-qty-btn plus" aria-label="{esc(name)} এর পরিমাণ বাড়ান">{icon('plus')}</button></div>
                <a href="{esc(order_link(item))}" target="_blank" rel="noopener noreferrer" class="direct-btn-order" aria-label="{esc(name)} WhatsApp-এ অর্ডারের অনুরোধ করুন">{icon('chat')}অর্ডার করুন</a>
              </div>
              <button class="direct-btn-add" type="button">তালিকায় যোগ করুন{icon('plus')}</button>
            </div>
          </article>'''


def filters(categories=None):
    chosen = set(categories or CATEGORIES)
    buttons = ['          <button type="button" class="filter-tab is-active" data-filter="all" aria-pressed="true">সব পণ্য</button>']
    for category, (name, _) in CATEGORIES.items():
        if category in chosen:
            buttons.append(f'          <button type="button" class="filter-tab" data-filter="{category}" aria-pressed="false">{name}</button>')
    return "\n".join(buttons)


def fragment(source, pattern, label):
    match = re.search(pattern, source, re.S)
    if not match:
        raise ValueError(f"Cannot find homepage {label}")
    return match.group(0)


def chrome(source):
    sprite = fragment(source, r'<svg class="icon-library".*?</svg>', "icon library")
    header = fragment(source, r'  <div class="announcement">.*?(?=\n  <main)', "header")
    header = header.replace('<a href="index.html" class="active" aria-current="page">', '<a href="index.html">')
    header = header.replace('<a href="products.html">', '<a href="products.html" class="active" aria-current="page">', 1)
    order_bar = fragment(source, r'  <aside class="floating-order-bar".*?</aside>', "order bar")
    footer = fragment(source, r'  <footer class="home-footer">.*?</footer>', "footer")
    mobile = fragment(source, r'  <nav class="mobile-bar".*?</nav>', "mobile navigation")
    mobile = mobile.replace('<a href="index.html" aria-current="page">', '<a href="index.html">')
    mobile = mobile.replace('<a href="products.html">', '<a href="products.html" aria-current="page">', 1)
    return sprite, header, order_bar, footer, mobile


def extra_gallery():
    """Optional captioned photos which do not describe one purchasable item."""
    path = ROOT / "tools/catalog-gallery.json"
    if not path.is_file():
        return ""
    photos = json.loads(path.read_text(encoding="utf-8-sig"))
    figures = []
    for photo in photos:
        image = local_image(photo.get("image"))
        if not image:
            continue
        caption = esc(photo.get("caption", "Fresh Mart-এর পণ্যের ছবি"))
        figures.append(f'<figure><img src="{esc(image)}" alt="{caption}" width="720" height="720" loading="lazy" decoding="async"/><figcaption>{caption}</figcaption></figure>')
    if not figures:
        return ""
    return f'''    <section class="catalog-photo-gallery" aria-labelledby="catalog-gallery-heading"><div class="container"><div class="home-section-heading"><div><span class="home-eyebrow">আমাদের পণ্যের আরও ছবি</span><h2 id="catalog-gallery-heading">Fresh Mart-এর প্রস্তুতির এক ঝলক</h2></div><a class="text-link" href="{esc(FACEBOOK)}" target="_blank" rel="noopener noreferrer">Facebook-এ দেখুন {icon('arrow')}</a></div><div class="catalog-gallery-grid">{''.join(figures)}</div></div></section>'''


def render_products(items, source):
    sprite, header, bar, footer, mobile = chrome(source)
    # Group categories consistently and put verified photos first in each group.
    category_order = {name: index for index, name in enumerate(CATEGORIES)}
    ordered = sorted(items, key=lambda item: (category_order[item["category"]], not bool(item.get("image"))))
    cards = "\n".join(render_card(item) for item in ordered)
    return f'''<!DOCTYPE html>
<html lang="bn">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>পণ্য ও মূল্য — Fresh Mart Faridpur</title>
  <meta name="description" content="Fresh Mart Faridpur-এর শাকসবজি, মাছ, মাংস, মসলা ও কম্বো প্যাকের সম্পূর্ণ তালিকা। পরিমাণ বেছে WhatsApp-এ অর্ডারের অনুরোধ করুন।" />
  <meta name="theme-color" content="#174b35" />
  <link rel="icon" type="image/png" href="assets/favicon.png" />
  <link rel="apple-touch-icon" href="assets/favicon.png" />
  <link rel="stylesheet" href="css/fonts.css?v={VERSION}" />
  <link rel="stylesheet" href="css/style.css?v={VERSION}" />
  <link rel="stylesheet" href="css/home.css?v={VERSION}" />
  <link rel="stylesheet" href="css/catalog.css?v={VERSION}" />
  <script src="js/main.js?v={VERSION}" defer></script>
</head>
<body class="home-page catalog-page">
  <a class="skip-link" href="#main-content">মূল বিষয়বস্তুতে যান</a>
  {sprite}

{header}
  <main id="main-content" tabindex="-1">
    <section class="catalog-intro" aria-labelledby="catalog-heading">
      <div class="container catalog-intro-layout">
        <div class="catalog-intro-copy"><nav class="catalog-breadcrumb" aria-label="অবস্থান"><a href="index.html">হোম</a><span aria-hidden="true">/</span><span aria-current="page">পণ্য ও মূল্য</span></nav><span class="home-eyebrow">আপনার প্রতিদিনের রান্নার সঙ্গী</span><h1 id="catalog-heading">পণ্য ও মূল্য</h1><p>শাকসবজি থেকে মাছ, মাংস ও মসলা—আপনার পছন্দের উপকরণ এক জায়গায়। পণ্য ও পরিমাণ বেছে এখান থেকেই অর্ডারের অনুরোধ করুন।</p></div>
        <div class="catalog-order-guide">{icon('bag')}<div><h2>একটি পণ্য অথবা পুরো তালিকা</h2><p>সরাসরি অর্ডার করুন, অথবা পণ্যগুলো তালিকায় যোগ করে একসঙ্গে WhatsApp-এ পাঠান। সময়মতো পেতে ১–২ দিন আগে অর্ডার করুন।</p><a href="tel:+8801611402642">{icon('phone')}<span lang="en">01611-402642</span></a></div></div>
      </div>
    </section>
    <section class="catalog-products" id="direct-products" aria-labelledby="products-heading">
      <div class="container">
        <div class="catalog-toolbar"><div><h2 id="products-heading">পছন্দের পণ্য খুঁজে নিন</h2><p>পরিমাণের প্রতিটি ধাপ কার্ডে দেখানো একটি প্যাক বা ইউনিট।</p></div><div class="catalog-search"><label for="productSearch">পণ্যের নাম লিখে খুঁজুন</label><div class="catalog-search-input">{icon('bag')}<input type="search" id="productSearch" placeholder="যেমন: মাছ, আলু, চিকেন…" autocomplete="off" aria-controls="directProductsGrid" /></div></div></div>
        <div class="direct-filter-tabs" role="group" aria-label="পণ্যের ধরন বেছে নিন">
{filters()}
        </div>
        <div class="catalog-results"><p id="productFilterStatus" role="status" aria-live="polite">{bn(len(items))}টি পণ্য দেখানো হচ্ছে</p><a href="{esc(PRICE_SOURCE)}" target="_blank" rel="noopener noreferrer">Facebook-এর মূল্য তালিকা {icon('arrow')}</a></div>
        <div class="catalog-price-note">{icon('check')}<p>প্রকাশিত তালিকার মূল্য দেখানো হয়েছে; বাজার ও মজুত অনুযায়ী বদলাতে পারে। চূড়ান্ত মূল্য, প্যাকের পরিমাণ ও ডেলিভারি খরচ অর্ডারের আগে নিশ্চিত করুন।</p></div>
        <div class="direct-products-grid" id="directProductsGrid">
{cards}
        </div>
        <div id="productEmptyState" class="catalog-empty" hidden>{icon('bag')}<h3>এই নামে কোনো পণ্য পাওয়া যায়নি</h3><p>অন্য নামে খুঁজুন বা সব পণ্যের বিভাগ বেছে নিন। নিজের পছন্দমতো প্যাকের জন্য আমাদের সঙ্গে কথা বলুন।</p><a class="text-link" href="https://wa.me/8801611402642" target="_blank" rel="noopener noreferrer">WhatsApp-এ কথা বলুন {icon('arrow')}</a></div>
        <noscript><p class="catalog-no-script">সব পণ্য নিচে দেখানো হয়েছে। অর্ডার করুন বাটন থেকে একটি ইউনিটের অনুরোধ পাঠাতে পারবেন; প্রয়োজনীয় পরিমাণ WhatsApp-এ লিখুন।</p></noscript>
      </div>
    </section>
{extra_gallery()}
    <section class="catalog-custom-order" aria-labelledby="custom-order-heading"><div class="container"><div class="order-callout"><div><span class="callout-kicker">আপনার পছন্দমতো প্রস্তুতি</span><h2 id="custom-order-heading">নিজের মতো প্যাক সাজাতে চান?</h2><p>পছন্দের পণ্য, কাট ও পরিমাণ জানিয়ে কথা বলুন। প্রাপ্যতা, মূল্য ও ডেলিভারির সময় আমরা নিশ্চিত করব।</p></div><div class="callout-buttons"><a class="home-button button-light" href="https://wa.me/8801611402642?text={quote('আসসালামু আলাইকুম, আমি আমার পছন্দমতো পণ্য ও পরিমাণ দিয়ে একটি প্যাক অর্ডার করতে চাই।', safe='')}" target="_blank" rel="noopener noreferrer">{icon('chat')}কাস্টম প্যাকের অনুরোধ</a><a class="callout-phone" href="tel:+8801611402642">{icon('phone')}<span lang="en">01611-402642</span></a></div></div></div></section>
  </main>

{bar}

{footer}
{mobile}
</body>
</html>
'''


def update_home(items, source):
    featured = sorted(
        (item for item in items if item.get("featured")),
        key=lambda item: item.get("featuredOrder", math.inf),
    )
    if len(featured) != 12 or any(not item.get("image") for item in featured):
        raise ValueError("--home requires exactly 12 featured products, each with a verified local image")
    replacement = '<div class="direct-products-grid" id="directProductsGrid">\n' + "\n".join(render_card(item, home=True) for item in featured)
    pattern = r'<div class="direct-products-grid" id="directProductsGrid">.*?(?=\n        </div>\n        <div class="direct-more-products")'
    updated, count = re.subn(pattern, lambda _: replacement, source, count=1, flags=re.S)
    if count != 1:
        raise ValueError("Cannot locate homepage product-grid boundary")
    pattern = r'(<div class="direct-filter-tabs"[^>]*>).*?(</div>)'
    active_categories = {item["category"] for item in featured}
    filter_content = "\n" + filters(active_categories)
    if "spice" not in active_categories:
        filter_content += '\n          <a class="filter-link" href="products.html#spice">মসলা বাটার মূল্য দেখুন ↗</a>'
    updated, count = re.subn(pattern, lambda match: match.group(1) + filter_content + "\n        " + match.group(2), updated, count=1, flags=re.S)
    if count != 1:
        raise ValueError("Cannot locate homepage category filters")
    # Keep existing hero, story, and other page content intact.
    return re.sub(r'(css/(?:fonts|style|home)\.css|js/main\.js)\?v=\d+(?:-\d+)?', lambda match: match.group(1) + "?v=" + VERSION, updated)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--home", action="store_true", help="also render the 12 featured homepage products")
    args = parser.parse_args()
    items = read_catalog()
    homepage = ROOT / "index.html"
    source = homepage.read_text(encoding="utf-8-sig")
    products = render_products(items, source)
    home = update_home(items, source) if args.home else None
    # Validate all output first so an invalid home selection never partially updates pages.
    (ROOT / "products.html").write_text(products, encoding="utf-8")
    if home is not None:
        homepage.write_text(home, encoding="utf-8")
    print(f"Generated products.html: {len(items)} products, {sum(bool(item.get('image')) for item in items)} photo cards")
    if home is not None:
        print("Updated index.html: 12 featured photo products")


if __name__ == "__main__":
    main()
