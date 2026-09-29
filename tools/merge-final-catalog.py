"""Apply caption-verified Facebook additions without changing featured products."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
path = ROOT / "tools/catalog-data.json"
items = json.loads(path.read_text(encoding="utf-8-sig"))
by_id = {item["id"]: item for item in items}
updates = json.loads((ROOT / "tools/catalog-facebook-updates.json").read_text(encoding="utf-8-sig"))


def photo(item, photo_id):
    item["image"] = f"assets/facebook/{photo_id}.webp"
    item["source"] = f"https://www.facebook.com/photo.php?fbid={photo_id}"


for product_id, photo_id in updates["matches"].items():
    photo(by_id[product_id], photo_id)

for item in updates["newProducts"]:
    item.setdefault("featured", False)
    if item["id"] not in by_id:
        items.append(item)
        by_id[item["id"]] = item

for product_id, photo_id in {
    "water-lily-stems": "122111167881395221",
    "pabda-fish": "122112089733395221",
    "carrot-potato": "122104894725395221",
    "bitter-gourd-potato": "122103712731395221",
    "chopped-garlic": "122109929307395221",
    "beef-potato-combo": "122112012567395221",
}.items():
    photo(by_id[product_id], photo_id)


def add(product_id, name, category, unit, price, photo_id=None, description=None):
    if product_id in by_id:
        return
    item = dict(id=product_id, name=name, category=category, unit=unit,
                price=price, image=None, featured=False)
    if photo_id:
        photo(item, photo_id)
    else:
        item["source"] = "https://www.facebook.com/photo.php?fbid=122109124449395221"
    if description:
        item["description"] = description
    items.append(item)
    by_id[product_id] = item


add("basella-greens", "পুঁই শাক", "veg", "১ প্যাক (পরিমাণ নিশ্চিত করুন)", None,
    "122109862137395221", "বাছা, কাটা ও পরিষ্কার করা")
add("red-amaranth", "লাল শাক", "veg", "১ প্যাক (পরিমাণ নিশ্চিত করুন)", None,
    description="মৌসুম ও প্রাপ্যতা অনুযায়ী")
add("taro-leaves", "কচু শাক", "veg", "১ প্যাক (পরিমাণ নিশ্চিত করুন)", None,
    description="মৌসুম ও প্রাপ্যতা অনুযায়ী")
add("water-lily-shrimp-combo", "শাপলা + চিংড়ি", "combos",
    "১ কম্বো প্যাক (পরিমাণ নিশ্চিত করুন)", None, "122107860339395221")
add("carrot-potato-shrimp-combo", "গাজর + আলু + চিংড়ি", "combos",
    "১ কম্বো প্যাক (পরিমাণ নিশ্চিত করুন)", 80, "122104575063395221")
add("kochur-lati-300g", "কচুর লতি", "veg", "৩০০ গ্রাম", 60,
    "122102234673395221", "ছবির চিংড়ি এই প্যাকের সঙ্গে অন্তর্ভুক্ত নয়")
add("mixed-vegetables-no-potato", "আলু ছাড়া মিক্সড সবজি", "veg",
    "১ প্যাক (পরিমাণ নিশ্চিত করুন)", None, "122112426207395221",
    "মৌসুমি সবজির মিশ্রণ")

path.write_text(json.dumps(items, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# Keep download records in a consistent schema, including the last graphic.
download_path = ROOT / "data/facebook-downloads.json"
records = json.loads(download_path.read_text(encoding="utf-8"))
for record in records:
    if "fbid" in record and "id" not in record:
        record["id"] = record.pop("fbid")
        record["image"] = dict(src=record.pop("src"), w=record.pop("w"), h=record.pop("h"), alt=record.pop("alt"))
download_path.write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Reviewed catalog: {len(items)} products; {sum(bool(i.get('image')) for i in items)} photo cards")
