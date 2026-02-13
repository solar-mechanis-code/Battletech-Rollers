# BattleTech JumpShip + DropShip Rollers (Sarna-based)

This repo provides two interactive rollers for BattleTech campaigns:

- **JumpShip class roller** (simple weighted d100 distribution).
- **DropShip class roller** using **all DropShip classes listed on Sarna**, with filters for:
  - **Tech base:** Inner Sphere / Clan / Any
  - **Chronology cutoff:** in-universe year (only allow designs introduced on/before that year)
  - **Era:** automatically derived from year
  - **Rarity:** common / uncommon / rare / very_rare / unknown (weighted)

It also includes a **builder script** that scrapes Sarna and generates a local file (`dropship_overrides.py`) containing each DropShip class’s:
- **Intro / production year** (when present on Sarna)
- **Tech base** (when present on Sarna)
- A best-effort **rarity guess** (heuristic from article wording)

> **Rarity note:** Sarna does not have a standardized “rarity” field in infoboxes, so rarity is inferred from phrases like “prototype,” “limited production,” “ubiquitous,” etc. You can (and should) patch edge cases using `LOCAL_OVERRIDES`.

---

## Files

- `build_dropship_overrides.py`  
  One-time (or occasional) scraper that generates:
  - `dropship_overrides.py` (imported by the roller)
  - `dropship_overrides.json` (human-readable)
  - `dropship_failures.txt` (only if some pages fail)

- `bt_ship_rollers.py`  
  Main interactive program:
  - JumpShip roller
  - DropShip roller (filters + weighting)
  - Audit option to summarize data coverage

---

## Requirements

- Python **3.10+**
- Internet access **only for the builder** (`build_dropship_overrides.py`)
- Standard library only (no pip installs required)

---

## Setup (Step-by-step)

### 1) Put the scripts in one folder
Your directory should look like this:

```

your-folder/
build_dropship_overrides.py
bt_ship_rollers.py

````

---

### 2) Generate the DropShip data (required for DropShip rolling)
Run the builder to create `dropship_overrides.py`:

**Terminal / PowerShell**
```bash
python build_dropship_overrides.py
````

**IDLE (Windows)**

1. Open `build_dropship_overrides.py`
2. Press **F5** (Run → Run Module)
3. Wait for it to finish

After this, you should see these new files in the folder:

* `dropship_overrides.py`
* `dropship_overrides.json`
* (optional) `dropship_failures.txt`

---

### 3) Run the rollers

**Terminal / PowerShell**

```bash
python bt_ship_rollers.py
```

**IDLE**

1. Open `bt_ship_rollers.py`
2. Press **F5**
3. Choose from the menu:

   * `1` JumpShip
   * `2` DropShip
   * `3` Audit DropShip data

---

## How DropShip Filtering Works

When rolling DropShips, you’ll be prompted for:

### Tech base

* `IS` — Inner Sphere only
* `Clan` — Clan only
* `Any` — everything

If you choose `IS` or `Clan`, you can decide whether to include entries where tech base is unknown.

### Chronology cutoff (in-universe year)

If you enter a year, the roller will only pick DropShip classes whose intro year is:

* `intro_year <= your_year`

You can enable **Strict year filter** to exclude entries that have unknown intro year.

### Rarity mode

* `common only`
* `common + uncommon`
* `any` (includes rare, very rare, unknown)

If you choose a restricted mode (common-only or common+uncommon), you can choose whether to include `unknown` rarity designs.

---

## Local Overrides (Recommended)

Some designs are lore-only, protoypes, “abandoned production,” or otherwise ambiguous.
Patch those in `bt_ship_rollers.py` using `LOCAL_OVERRIDES`, which always overrides the auto-generated data.

Example block:

```python
LOCAL_OVERRIDES = {
    # Star League-era implied, essentially extinct
    "League": {"year": 2750, "tech": "IS", "rarity": "very_rare"},

    # Terran Hegemony testbed; treat as ancient and near-one-off
    "Hector": {"year": 2600, "tech": "IS", "rarity": "very_rare"},

    # Custom Wolf’s Dragoons listing (assumed Clan-unique)
    "Scout": {"year": 3055, "tech": "Clan", "rarity": "rare"},

    # FedCom Civil War-era game portrayal
    "Talon": {"year": 3062, "tech": "IS", "rarity": "uncommon"},

    # Prototypes / abandoned production lines
    "Cargomaster": {"rarity": "very_rare"},
    "Cargoking": {"rarity": "very_rare"},
    "Argo": {"rarity": "very_rare"},
}
```

### Make “very_rare” *really* rare

In `bt_ship_rollers.py`, adjust:

```python
RARITY_WEIGHT["very_rare"] = 0.05
```

Lower numbers = rarer.

---

## Troubleshooting

### “No DropShip data loaded. Run build_dropship_overrides.py first.”

* You didn’t run the builder yet, or
* `dropship_overrides.py` isn’t in the same folder as `bt_ship_rollers.py`

Fix:

1. Run `python build_dropship_overrides.py`
2. Confirm `dropship_overrides.py` exists next to `bt_ship_rollers.py`

### Builder failures

If `dropship_failures.txt` exists, it logs which pages failed to parse (usually connection hiccups or formatting quirks). Re-running the builder often fixes it.

### Builder is slow

It sleeps between requests.

---

## Credits / Data Source

This tool is based on Sarna.net (BattleTech Wiki) category listings and article content.
Era cutoffs follow Sarna’s BattleTech eras page.

This is a convenience tool for campaign use and is not an “official” BattleTech distribution source.

---

## License

You can add any license you want (MIT is common for small utilities).
Add a `LICENSE` file in the repo root if you want GitHub to display it.

```
::contentReference[oaicite:0]{index=0}
```
