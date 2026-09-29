"""Apply the product matches verified from the Facebook page's photo captions."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
path = ROOT / 'tools/catalog-data.json'
items = json.loads(path.read_text(encoding='utf-8'))
by_id = {item['id']: item for item in items}
matches = {
    'mixed-vegetables': '122128950093395221',
    'bottle-gourd-leaves': '122130093399395221',
    'shing-fish': '122128371111395221',
    'koi-fish': '122127885393395221',
    'grated-coconut-250g': '122127402903395221',
    'grated-coconut-500g': '122127402903395221',
    'peeled-garlic': '122126639859395221',
    'small-shrimp-100g': '122126181495395221',
    'small-shrimp-1kg': '122126530371395221',
    'chicken-breast': '122126298093395221',
    'kochur-lati': '122125856529395221',
    'deshi-puti-fish': '122125840371395221',
    'gutum-fish': '122125452549395221',
    'kajli-fish': '122125907283395221',
    'beef-tripe-potato': '122125166559395221',
    'ginger-paste': '122122550385395221',
    'banana-blossom': '122122277883395221',
    'sweet-pumpkin': '122122315839395221',
}
new_items = [
    ('diet-box', 'ডায়েট বক্স', 'combos', '১ বক্স', 130, '122129686851395221', 'সবজি পছন্দমতো বদলাতে যোগাযোগ করুন'),
    ('beef-liver-combo', 'গরুর কলিজা কম্বো', 'combos', '১ কম্বো প্যাক', 200, '122128860093395221', 'প্যাকের পরিমাণ নিশ্চিত করুন'),
    ('rui-fish', 'রুই মাছ', 'fish', 'পছন্দমতো পরিমাণ', None, '122129351127395221', 'প্রয়োজনীয় ওজন জানিয়ে দাম জেনে নিন'),
    ('piyali-fish-500g', 'নদীর পিয়ালি মাছ', 'fish', '৫০০ গ্রাম', None, '122128592475395221', '২৫০ গ্রামের জন্যও যোগাযোগ করতে পারেন'),
    ('boneless-beef-1kg', 'হাড় ছাড়া গরুর মাংস', 'meat', '১ কেজি', None, '122128818879395221', 'চূড়ান্ত দাম নিশ্চিত করুন'),
    ('boneless-beef-250g', 'হাড় ছাড়া গরুর মাংস', 'meat', '২৫০ গ্রাম', None, '122127428637395221', 'চূড়ান্ত দাম নিশ্চিত করুন'),
    ('spinach', 'পালং শাক', 'veg', 'পরিমাণ নিশ্চিত করুন', None, '122126549457395221', 'মৌসুম ও প্রাপ্যতা অনুযায়ী'),
    ('goat-tripe-combo', 'খাসির ভুঁড়ি কম্বো', 'combos', '১ কম্বো প্যাক', 100, '122126409261395221', 'প্যাকের পরিমাণ নিশ্চিত করুন'),
    ('goat-tripe', 'খাসি / ছাগলের ভুঁড়ি', 'meat', 'পছন্দমতো পরিমাণ', None, '122125463613395221', 'প্রি-অর্ডারে পরিমাণ ও দাম নিশ্চিত করুন'),
    ('rice-flour-250g', 'আতপ চালের গুঁড়া', 'dairy', '২৫০ গ্রাম', None, '122124088317395221', 'ফ্রোজেন করে রাখুন'),
    ('rice-flour-500g', 'আতপ চালের গুঁড়া', 'dairy', '৫০০ গ্রাম', None, '122122523733395221', 'ফ্রোজেন করে রাখুন'),
    ('rice-flour-1kg', 'আতপ চালের গুঁড়া', 'dairy', '১ কেজি', None, '122122523733395221', 'ফ্রোজেন করে রাখুন'),
    ('thin-beef-tripe', 'গরুর পাতলা ভুঁড়ি', 'meat', 'পছন্দমতো পরিমাণ', None, '122123654247395221', 'পরিষ্কার করা, রান্নার জন্য প্রস্তুত'),
]
for id_, name, category, unit, price, image_id, description in new_items:
    if id_ not in by_id:
        row = dict(id=id_, name=name, category=category, unit=unit, price=price,
                   image=None, featured=False, description=description)
        items.append(row)
        by_id[id_] = row
    matches[id_] = image_id
for id_, image_id in matches.items():
    row = by_id[id_]
    row['image'] = f'assets/facebook/{image_id}.webp'
    row['source'] = f'https://www.facebook.com/photo.php?fbid={image_id}'
by_id['beef-tripe-potato']['name'] = 'গরুর ভুঁড়ি + আলু'
# Exactly twelve distinct product photographs on the home page.
featured = ['diet-box', 'mixed-vegetables', 'bottle-gourd-leaves', 'chicken-breast',
            'beef-liver-combo', 'peeled-garlic', 'grated-coconut-250g', 'ginger-paste',
            'kochur-lati', 'deshi-puti-fish', 'shing-fish', 'piyali-fish-500g']
for row in items:
    row['featured'] = row['id'] in featured
    if row['featured']:
        row['featuredOrder'] = featured.index(row['id'])
path.write_text(json.dumps(items, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(f'{len(items)} products; {len(featured)} home products; {len(matches)} photo matches')
