# Punk Records — One Piece TCG Data

Punk Records is a static, versioned JSON card dataset for the One Piece TCG. These files are generated using the [vegapull](https://github.com/Coko7/vegapull) tool, which fetches card and pack data from the official One Piece TCG website.

Most of the data is ©Eiichiro Oda/Shueisha ©Eiichiro Oda/Shueisha, Toei Animation, Bandai Namco Entertainment Inc.

The actual source code of the pipeline — are available under the GNU Affero General Public License 3.0 or later. See [License](LICENSE) for more details.

## Structure

- Language folders with packs, cards, and indices:
    - <lang>/packs.json — all packs released for the language/region
    - <lang>/cards/<pack-id>.json — all cards in a pack
    - <lang>/index/cards_by_id.json — quick lookup index (by card ID)
    - <lang>/index/by_name.json — quick lookup index (by card name, case-insensitive)
    - <lang>/manifest.json — metadata about the generation
- Supported Languages
  - english (en)
  - english-asia (en-asia)
  - japanese (jp)
  - chinese-hongkong (zh_hk)
  - chinese-taiwan (zh_tw)
  - thai (th)
  - french (fr)
- Example (partial):

```
punk-records/
  english/
    packs.json
    cards/
      569001.json
      OP01.json
    index/
      cards_by_id.json
      by_name.json
    manifest.json
  french/
    packs.json
    cards/
      569001.json
      OP01.json
    index/
      cards_by_id.json
      by_name.json
    manifest.json
  ...
```

## Schema

### Packs (packs.json)

- Array of:
  - id — pack ID string from the site (e.g., OP01, 569001)
  - raw_title — original title string
  - title_parts — parsed { prefix?, title, label? }

### Cards (cards/<pack-id>.json)

- Array of:
  - id — card ID (e.g., ST01-004)
  - pack_id — source pack ID
  - name — card name (locale-specific)
  - rarity — one of: Common, Uncommon, Rare, SuperRare, SecretRare, Leader, Special, TreasureRare, Promo
  - category — one of: Leader, Character, Event, Stage, Don
  - img_url — relative image URL from the site
  - img_full_url — absolute image URL (convenience)
  - colors — array (e.g., ["Red"])
  - cost — integer or null
  - attributes — array of attributes (e.g., ["Strike", "Slash"])
  - power — integer or null
  - counter — integer or null
  - types — array of strings
  - effect — rules text (localized)
  - trigger — optional trigger text

### Index (index/cards_by_id.json)

Object mapping id -> `{ name, pack_id, rarity, colors }`

### Index (index/by_name.json)

Object mapping lowercased name -> list of IDs

### Manifest (manifest.json)

```
{ 
  "language": "<lang>", 
  "generated_at": <unix_ts>, "split_per_card": bool, "images": bool, "source": "vegapull", "version": "1" }
  "split_per_card": bool, 
  "images": bool, 
  "source": "vegapull", 
  "version": "1" 
}
```

## How To Generate the Data

You can generate the data yourself using the [vegapull](https://github.com/Coko7/vegapull) tool.

**Prerequisites**:
  - Rust (for vegapull)
  - Vegapull Binary: `cargo install vegapull`
  - Python 3.9+ if using the helper script.

### Generate with the helper script:

```bash
git clone https://github.com/buhbbl/punk-records.git
cd punk-records
python build_punk_records.py --language english --out-dir punk-records
# Optional:
#   --split-per-card   also write per-card JSON files
#   --images           also download images per pack
#   --clean            delete existing lang dir before writing
#   --vegapull <path>  custom vegapull path/binary
```

## License and Disclaimer
- This repository contains structured data derived from official sources. All trademarks and images are property of their respective owners.
- Use at your own discretion. Respect the terms of service of the data sources when generating updates.