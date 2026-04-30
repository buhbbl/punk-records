"""Build punk-records JSON using vegapull."""
import argparse
import json
import logging
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger("punk-records")


def run(cmd, out_path=None):
    """Run a command and optionally write its stdout to out_path."""
    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Command failed: {' '.join(str(cmd))}\n{e.stderr}") from e
    if out_path:
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        Path(out_path).write_text(proc.stdout, encoding="utf-8")
        return None
    return proc.stdout

def stable_dump(obj) -> str:
    """Dump JSON with consistent formatting."""
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"), sort_keys=True)

def build_language(args, lang):
    """Build punk-records for a single language."""
    logger.info("Building punk-records for language: %s", lang)
    lang_dir = Path(args.out_dir) / lang
    data_dir = lang_dir / "data"
    cards_dir = lang_dir / "cards"
    index_dir = lang_dir / "index"

    if args.clean and lang_dir.exists():
        shutil.rmtree(lang_dir)

    lang_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)
    index_dir.mkdir(parents=True, exist_ok=True)

    # 1) Packs
    logger.debug("Fetching packs (%s)...", lang)
    run([args.vegapull, "pull", "--language", lang, "--output", lang_dir, "packs"])
    packs_json_path = lang_dir / "json" / "packs.json"
    packs = json.loads(packs_json_path.read_text(encoding="utf-8"))
    logger.info("Found %d packs.", len(packs))

    # Move packs JSON to root dir — re-serialize for stable key ordering
    if (lang_dir / "packs.json").exists():
        logger.warning("%s already exists, overwriting.", lang_dir / "packs.json")
        os.remove(lang_dir / "packs.json")
    (lang_dir / "packs.json").write_text(stable_dump(packs), encoding="utf-8")

    # 2) Cards per pack
    cards_by_id = {}
    by_name = {}

    for i, pack in enumerate(packs.values(), 1):
        pack_id = pack["id"]
        logger.debug("[%d/%d] Fetching cards for %s...", i, len(packs), pack_id)

        if os.path.exists(data_dir / f"{pack_id}.json") and not args.clean:
            logger.debug("Skipping %s, already exists.", pack_id)
            pack_json_path = data_dir / f"{pack_id}.json"
            cards = json.loads(pack_json_path.read_text(encoding="utf-8"))
        else:
            run([args.vegapull, "pull", "--language", lang, "--output", lang_dir, "cards", pack_id])
            out_file = lang_dir / "json" / f"cards_{pack_id}.json"
            cards = json.loads(out_file.read_text(encoding="utf-8"))

            # Optional split
            if args.split_per_card:
                (cards_dir / pack_id).mkdir(parents=True, exist_ok=True)
                for card in cards:
                    single_path = cards_dir / pack_id / f"{card['id']}.json"
                    single_path.write_text(stable_dump(card), encoding="utf-8")

            # Re-serialize to data dir with stable key ordering
            (data_dir / f"{pack_id}.json").write_text(stable_dump(cards), encoding="utf-8")

        # Build indices
        for card in cards:
            cards_by_id[card["id"]] = {
                "name": card.get("name"),
                "card_id": card.get("id"),
                "pack_id": card.get("pack_id"),
                "colors": card.get("colors"),
                "cost": card.get("cost"),
                "category": card.get("category"),
                "power": card.get("power"),
                "counter": card.get("counter")
            }
            key = (card.get("name") or "").strip().lower()
            if key:
                by_name.setdefault(key, []).append(card["id"])

    # 3) Indices and manifest
    (index_dir / "cards_by_id.json").write_text(stable_dump(cards_by_id), encoding="utf-8")
    # Sort card ID arrays so index is stable across runs with varying pack order
    by_name = {k: sorted(v) for k, v in by_name.items()}
    (index_dir / "by_name.json").write_text(stable_dump(by_name), encoding="utf-8")
    (lang_dir / "manifest.json").write_text(stable_dump({
        "language": lang,
        "generated_at": int(time.time()),
        "split_per_card": args.split_per_card,
        "source": "vegapull",
        "version": "2.0",
    }), encoding="utf-8")

    # Cleanup vegapull's json dir
    vegapull_json_dir = lang_dir / "json"
    if vegapull_json_dir.exists():
        shutil.rmtree(vegapull_json_dir)
        os.remove(lang_dir / "vega.meta.toml")

    logger.info("Done. Wrote JSON records to %s", lang_dir)

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Build punk-records JSON using vegapull.")
    parser.add_argument("--vegapull", default="vega", help="Path to vegapull binary (or name in PATH)")
    parser.add_argument("--language", default="all", help="Locale (english, english-asia, japanese, etc.)")
    parser.add_argument("--out-dir", default="punk-records", help="Output root directory")
    parser.add_argument("--clean", action="store_true", help="Delete existing language dir before writing")
    parser.add_argument("--split-per-card", action="store_true", help="Also write one JSON file per card")
    parser.add_argument("--verbose", action="store_true", help="Enable debug-level logging")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

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
    elapsed = datetime.fromtimestamp(end_time - start_time, tz=timezone.utc).strftime('%H:%M:%S.%f')[:-3]
    logger.info("Built punk-records in %s", elapsed)
