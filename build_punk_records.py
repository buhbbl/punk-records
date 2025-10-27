"""Build punk-records JSON using vegapull."""
import argparse
import json
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


def run(cmd, out_path=None):
    """Run a command and optionally write its stdout to out_path."""
    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{e.stderr}") from e
    if out_path:
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        Path(out_path).write_text(proc.stdout, encoding="utf-8")
        return None
    return proc.stdout

def stable_dump(obj) -> str:
    """Dump JSON with consistent formatting."""
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"), sort_keys=False)

def build_language(args, lang):
    """Build punk-records for a single language."""
    print(f"Building punk-records for language: {lang}")
    lang_dir = Path(args.out_dir) / lang
    cards_dir = lang_dir / "data"
    per_card_dir = lang_dir / "cards"
    index_dir = lang_dir / "index"
    images_root = lang_dir / "images"

    if args.clean and lang_dir.exists():
        shutil.rmtree(lang_dir)

    lang_dir.mkdir(parents=True, exist_ok=True)
    cards_dir.mkdir(parents=True, exist_ok=True)
    index_dir.mkdir(parents=True, exist_ok=True)

    # 1) Packs
    packs_json_path = lang_dir / "packs.json"
    print(f"Fetching packs ({lang})...")
    run([args.vegapull, "--language", lang, "packs", "--out", packs_json_path])
    packs = json.loads(packs_json_path.read_text(encoding="utf-8"))
    print(f"Found {len(packs)} packs.")

    # 2) Cards per pack
    cards_by_id = {}
    by_name = {}

    for i, pack in enumerate(packs, 1):
        pack_id = pack["id"]
        print(f"[{i}/{len(packs)}] Fetching cards for {pack_id}...")
        out_file = cards_dir / f"{pack_id}.json"
        run([args.vegapull, "--language", lang, "cards", pack_id, "--out", out_file])
        cards = json.loads(out_file.read_text(encoding="utf-8"))

        # Optional split
        if args.split_per_card:
            (per_card_dir / pack_id).mkdir(parents=True, exist_ok=True)
            for card in cards:
                single_path = per_card_dir / pack_id / f"{card['id']}.json"
                single_path.write_text(stable_dump(card), encoding="utf-8")

        # Build indices
        for card in cards:
            cards_by_id[card["id"]] = {
                "name": card.get("name"),
                "pack_id": card.get("pack_id"),
                "colors": card.get("colors"),
                "cost": card.get("cost")
            }
            key = (card.get("name") or "").strip().lower()
            if key:
                by_name.setdefault(key, []).append(card["id"])

        # Optional images
        if args.images:
            out_dir = images_root / pack_id
            print(f"  Downloading images for {pack_id} -> {out_dir}")
            out_dir.mkdir(parents=True, exist_ok=True)
            subprocess.run(
                [args.vegapull, "--language", lang, "images", f"--output-dir={str(out_dir)}", pack_id, "-vv"],
                check=True,
            )

    # 3) Indices and manifest
    (index_dir / "cards_by_id.json").write_text(stable_dump(cards_by_id), encoding="utf-8")
    (index_dir / "by_name.json").write_text(stable_dump(by_name), encoding="utf-8")
    (lang_dir / "manifest.json").write_text(stable_dump({
        "language": lang,
        "generated_at": int(time.time()),
        "split_per_card": args.split_per_card,
        "images": args.images,
        "source": "vegapull",
        "version": "1",
    }), encoding="utf-8")

    print(f"Done. Wrote JSON records to {lang_dir}")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Build punk-records JSON using vegapull.")
    parser.add_argument("--vegapull", default="vegapull", help="Path to vegapull binary (or name in PATH)")
    parser.add_argument("--language", default="all", help="Locale (english, english-asia, japanese, etc.)")
    parser.add_argument("--out-dir", default="punk-records", help="Output root directory")
    parser.add_argument("--clean", action="store_true", help="Delete existing language dir before writing")
    parser.add_argument("--split-per-card", action="store_true", help="Also write one JSON file per card")
    parser.add_argument("--images", action="store_true", help="Also download images per pack")
    args = parser.parse_args()

    # Check vegapull is callable
    try:
        subprocess.run([args.vegapull, "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    except (FileNotFoundError, OSError) as e:
        sys.exit(f"vegapull not found/executable ({args.vegapull}). Install with `cargo install vegapull` or pass --vegapull path. Error: {e}")

    if args.language.lower() == "all":
        languages = ["chinese-hongkong", "chinese-taiwan", "english", "french", "english-asia", "japanese", "thai"]
    else:
        languages = [args.language]

    for lang in languages:
        build_language(args, lang)

if __name__ == "__main__":
    start_time = time.time()
    main()
    end_time = time.time()
    print(f"Built punk-records in {datetime.fromtimestamp(end_time - start_time, tz=timezone.utc).strftime('%H:%M:%S.%f')[:-3]}")
