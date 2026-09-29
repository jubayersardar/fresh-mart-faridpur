"""Optimize downloaded public Facebook photos without cropping or inventing images.

Original photographs stay in data/facebook-originals. All compressed,
orientation-corrected photographs stay in data/facebook-optimized. Only photos
referenced by the reviewed catalog or gallery are copied to assets/facebook.
The private manifest and contact sheet support the product-to-photo review.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import shutil
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parent.parent


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def label_font() -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for filename in ("C:/Windows/Fonts/arial.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(filename, 13)
        except OSError:
            continue
    return ImageFont.load_default()


def process(source_dir: Path, output_dir: Path, max_size: int, quality: int) -> list[dict]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = sorted(
        p for p in source_dir.glob("*")
        if p.is_file() and p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}
    )
    records = []
    for source in paths:
        # Facebook photo IDs keep the source-to-asset mapping transparent.
        if not source.stem.isdecimal():
            print(f"Skipped non-photo-ID filename: {source.name}")
            continue
        target = output_dir / (source.stem + ".webp")
        with Image.open(source) as raw:
            original_size = raw.size
            photo = ImageOps.exif_transpose(raw).convert("RGB")
            photo.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            photo.save(target, "WEBP", quality=quality, method=6)
            size = photo.size
        records.append({
            "fbid": source.stem,
            "original": str(source.resolve()),
            "asset": str(target.relative_to(ROOT)).replace("\\", "/")
                if target.is_relative_to(ROOT) else str(target.resolve()),
            "originalWidth": original_size[0],
            "originalHeight": original_size[1],
            "width": size[0],
            "height": size[1],
            "bytes": target.stat().st_size,
            "sha256Original": digest(source),
            "sha256Asset": digest(target),
        })
    return records


def contact_sheet(records: list[dict], destination: Path) -> None:
    columns, thumb_size, cell_height, pad = 6, 200, 235, 8
    rows = max(1, math.ceil(len(records) / columns))
    sheet = Image.new("RGB", (columns * thumb_size, rows * cell_height), "#f5f6f3")
    draw = ImageDraw.Draw(sheet)
    font = label_font()
    if not records:
        draw.text((12, 12), "No downloaded photographs yet", fill="#254a38", font=font)
    for index, record in enumerate(records):
        x, y = (index % columns) * thumb_size, (index // columns) * cell_height
        with Image.open(record["original"]) as raw:
            photo = ImageOps.exif_transpose(raw).convert("RGB")
            photo.thumbnail((thumb_size - pad * 2, thumb_size - pad * 2), Image.Resampling.LANCZOS)
            sheet.paste(photo, (x + (thumb_size - photo.width) // 2, y + (thumb_size - photo.height) // 2))
        draw.text((x + pad, y + 203), record["fbid"], fill="#254a38", font=font)
        draw.text((x + pad, y + 219), f'{record["originalWidth"]} x {record["originalHeight"]}', fill="#647069", font=font)
    destination.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(destination, "JPEG", quality=90)


def reviewed_public_paths() -> set[str]:
    paths: set[str] = set()

    def inspect(value: object) -> None:
        if isinstance(value, str) and re.fullmatch(r"assets/facebook/[0-9]+\.webp", value):
            paths.add(value)
        elif isinstance(value, dict):
            for child in value.values():
                inspect(child)
        elif isinstance(value, list):
            for child in value:
                inspect(child)

    for catalog_path in (ROOT / "tools/catalog-data.json", ROOT / "tools/catalog-gallery.json"):
        if catalog_path.is_file():
            inspect(json.loads(catalog_path.read_text(encoding="utf-8-sig")))
    return paths


def copy_reviewed_photos(records: list[dict], reviewed_paths: set[str]) -> int:
    copied = 0
    public_dir = (ROOT / "assets/facebook").resolve()
    public_dir.mkdir(parents=True, exist_ok=True)
    for record in records:
        public_path = f'assets/facebook/{record["fbid"]}.webp'
        record["publicAsset"] = None
        if public_path not in reviewed_paths:
            continue
        destination = (ROOT / public_path).resolve()
        if destination.parent != public_dir:
            raise ValueError("Reviewed asset path escaped assets/facebook")
        shutil.copy2(ROOT / record["asset"], destination)
        record["publicAsset"] = public_path
        copied += 1
    return copied


def move_unreferenced_public_photos(reviewed_paths: set[str], private_dir: Path) -> int:
    public_dir = (ROOT / "assets/facebook").resolve()
    workspace = ROOT.resolve()
    private_dir = private_dir.resolve()
    if not public_dir.is_relative_to(workspace) or not private_dir.is_relative_to(workspace / "data"):
        raise ValueError("Photo move targets must stay within the workspace's assets and private data")
    moved = 0
    if not public_dir.is_dir():
        return moved
    for source in public_dir.glob("*.webp"):
        if not source.is_file() or not source.stem.isdecimal():
            continue
        public_path = f"assets/facebook/{source.name}"
        if public_path in reviewed_paths:
            continue
        source = source.resolve()
        destination = (private_dir / source.name).resolve()
        if source.parent != public_dir or destination.parent != private_dir:
            raise ValueError("Photo move path escaped its verified directories")
        # Preserve a public variant if its bytes differ from the private copy.
        if destination.exists() and digest(source) != digest(destination):
            destination = private_dir / (source.stem + ".previous-public.webp")
        source.replace(destination)
        moved += 1
    return moved


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=ROOT / "data/facebook-originals")
    parser.add_argument("--output", type=Path, default=ROOT / "data/facebook-optimized")
    parser.add_argument("--max-size", type=int, default=900)
    parser.add_argument("--quality", type=int, default=82)
    parser.add_argument("--prune-public", action="store_true", help="Move unreferenced public photos into private data")
    args = parser.parse_args()
    if not args.source.is_dir():
        print(f"No downloaded photo directory yet: {args.source}")
        return
    if not 1 <= args.max_size <= 4096 or not 1 <= args.quality <= 100:
        parser.error("max-size must be 1–4096; quality must be 1–100")
    if not args.output.resolve().is_relative_to((ROOT / "data").resolve()):
        parser.error("All optimized photographs must be kept inside private data")
    records = process(args.source.resolve(), args.output.resolve(), args.max_size, args.quality)
    reviewed_paths = reviewed_public_paths()
    copied = copy_reviewed_photos(records, reviewed_paths)
    moved = move_unreferenced_public_photos(reviewed_paths, args.output) if args.prune_public else 0
    private_data = ROOT / "data"
    private_data.mkdir(parents=True, exist_ok=True)
    (private_data / "facebook-image-manifest.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    contact_sheet(records, private_data / "facebook-contact-sheet.jpg")
    # Short review pages keep each photo ID readable when viewed in the app.
    for page_index in range(0, len(records), 24):
        page_number = page_index // 24 + 1
        contact_sheet(
            records[page_index:page_index + 24],
            private_data / f"facebook-contact-sheet-{page_number:02d}.jpg",
        )
    total_bytes = sum(r["bytes"] for r in records)
    print(f"Processed {len(records)} photographs, {total_bytes / 1024:.0f} KB total.")
    print(f"Copied {copied} reviewed photos to public assets; moved {moved} unreferenced public photos to private data.")
    print("Private review: data/facebook-image-manifest.json and data/facebook-contact-sheet.jpg")


if __name__ == "__main__":
    main()
