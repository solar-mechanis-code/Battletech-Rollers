import random


# ============================================================
# JumpShip roller
# ============================================================

def roll_jumpship():
    """3025-ish Inner Sphere distribution:
    Invader 46%, Merchant 32%, Scout 11%, Star Lord 5%, Monolith 3%, Minor 3%.
    """
    r = random.randint(1, 100)

    if r <= 46:
        return "Invader"
    elif r <= 78:
        return "Merchant"
    elif r <= 89:
        return "Scout"
    elif r <= 94:
        return "Star Lord"
    elif r <= 97:
        return "Monolith"
    else:
        minor_roll = random.randint(1, 6)
        minor = {
            1: "Tramp",
            2: "Tramp",
            3: "Leviathan",
            4: "Liberty",
            5: "Uma",
            6: "Other minor (your pick)",
        }[minor_roll]
        return f"{minor} (minor bucket)"


def roll_many_jumpships(n):
    return [roll_jumpship() for _ in range(n)]


def interactive_jumpship_roller():
    print("JumpShip Class Roller (d100 weighted)")
    print("Type 'q' at any prompt to quit.\n")

    while True:
        raw = input("How many JumpShips do you want to roll? ").strip()
        if raw.lower() in ("q", "quit", "exit"):
            print("Terminated.")
            return

        try:
            n = int(raw)
            if n <= 0:
                print("Please enter a positive integer.\n")
                continue
        except ValueError:
            print("Please enter a whole number (e.g., 1, 5, 20) or 'q' to quit.\n")
            continue

        results = roll_many_jumpships(n)
        for i, cls in enumerate(results, start=1):
            print(f"JS-{i:02d}: {cls}")
        print()

        again = input("Roll again? (y/n) ").strip().lower()
        if again not in ("y", "yes"):
            print("Terminated.")
            return


# ============================================================
# DropShip roller (uses generated overrides if available)
# ============================================================

ERA_RANGES = [
    ("Age of War",       2005, 2570),
    ("Star League",      2571, 2780),
    ("Succession Wars",  2781, 3049),
    ("Clan Invasion",    3050, 3061),
    ("FedCom Civil War", 3062, 3067),
    ("Jihad",            3068, 3081),
    ("Republic",         3082, 3130),
    ("Dark Age",         3131, 3150),
    ("ilClan",           3151, 9999),
]


def era_for_year(year: int) -> str:
    for name, start, end in ERA_RANGES:
        if start <= year <= end:
            return name
    return "Unknown"


RARITY_WEIGHT = {
    "common": 10.0,
    "uncommon": 3.0,
    "rare": 1.0,
    "very_rare": 0.05,
    "unknown": 1.0,
}


# ---- Load auto-generated overrides (dropship_overrides.py) ----
try:
    from dropship_overrides import DROPSHIP_OVERRIDES
except Exception:
    DROPSHIP_OVERRIDES = {}


# ---- Optional: your personal patches that always win (edit freely) ----
LOCAL_OVERRIDES = {
    # Inferred / lore-only / “extinct-ish”
    "League": {"year": 2750, "tech": "IS", "rarity": "very_rare"},
    "Hector": {"year": 2600, "tech": "IS", "rarity": "very_rare"},
    "Scout":  {"year": 3055, "tech": "Clan", "rarity": "rare"},
    "Talon":  {"year": 3062, "tech": "IS", "rarity": "uncommon"},

    # Prototypes / abandoned production => near-one-offs
    "Cargomaster": {"rarity": "very_rare"},
    "Cargoking":   {"rarity": "very_rare"},
    "Argo":        {"rarity": "very_rare"},
}


def build_dropship_db():
    """
    Build DB from DROPSHIP_OVERRIDES if available (preferred),
    otherwise fall back to an empty list and warn.
    """
    db = []

    if DROPSHIP_OVERRIDES:
        for name, data in DROPSHIP_OVERRIDES.items():
            db.append({
                "name": name,
                "tech": data.get("tech") if data.get("tech") is not None else "Unknown",
                "year": data.get("year"),
                "rarity": data.get("rarity") if data.get("rarity") is not None else "unknown",
            })
        # Stable ordering for nicer output (optional)
        db.sort(key=lambda d: d["name"].lower())
        return db

    # If overrides aren't present, you can still run, but there will be no DS data.
    return db


def apply_overrides(dropship_db, overrides):
    by_name = {d["name"]: d for d in dropship_db}
    for name, data in overrides.items():
        if name not in by_name:
            continue
        if data.get("year") is not None:
            by_name[name]["year"] = data["year"]
        if data.get("tech") is not None:
            by_name[name]["tech"] = data["tech"]
        if data.get("rarity") is not None:
            by_name[name]["rarity"] = data["rarity"]
    return dropship_db


DROPSHIP_DB = build_dropship_db()
DROPSHIP_DB = apply_overrides(DROPSHIP_DB, LOCAL_OVERRIDES)  # your patch layer


def weighted_choice(items, weights):
    return random.choices(items, weights=weights, k=1)[0]


def rarity_allowed(item_rarity: str, mode: str, include_unknown: bool) -> bool:
    if item_rarity == "unknown" and not include_unknown:
        return False

    if mode == "any":
        return True
    if mode == "common":
        return item_rarity == "common"
    if mode == "common_uncommon":
        return item_rarity in ("common", "uncommon")
    return True


def tech_allowed(item_tech: str, tech_choice: str, include_unknown_tech: bool) -> bool:
    if tech_choice == "Any":
        return True
    if item_tech == "Unknown":
        return include_unknown_tech
    return item_tech == tech_choice


def roll_dropship(
    tech_choice="Any",
    year=None,
    strict_year=False,
    rarity_mode="any",
    include_unknown_rarity=True,
    include_unknown_tech=True
):
    """
    tech_choice: "IS", "Clan", or "Any"
    year: int or None (chronology filter: intro year <= year)
    strict_year: if True, excludes entries with unknown intro year when year filter is set
    rarity_mode: "common", "common_uncommon", or "any"
    include_unknown_rarity: include 'unknown' rarity entries in the pool?
    include_unknown_tech: include 'Unknown' tech entries when filtering to IS/Clan?
    """

    if not DROPSHIP_DB:
        return "No DropShip data loaded. Run build_dropship_overrides.py first."

    pool = []
    pool_weights = []

    for d in DROPSHIP_DB:
        if not tech_allowed(d["tech"], tech_choice, include_unknown_tech):
            continue
        if not rarity_allowed(d["rarity"], rarity_mode, include_unknown_rarity):
            continue

        if year is not None:
            if d["year"] is None:
                if strict_year:
                    continue
            else:
                if d["year"] > year:
                    continue

        pool.append(d)
        pool_weights.append(RARITY_WEIGHT.get(d["rarity"], 1.0))

    if not pool:
        return "No candidates (filters too strict)."

    picked = weighted_choice(pool, pool_weights)

    parts = [picked["name"]]
    if picked["year"] is not None:
        parts.append(f"(intro {picked['year']}, {era_for_year(picked['year'])})")
    else:
        parts.append("(intro year unknown)")
    parts.append(f"[{picked['tech']}, {picked['rarity']}]")
    return " ".join(parts)


def roll_many_dropships(n, **kwargs):
    return [roll_dropship(**kwargs) for _ in range(n)]


def audit_dropship_db():
    rarity_counts = {}
    tech_counts = {}
    missing_year = 0

    for d in DROPSHIP_DB:
        rarity_counts[d["rarity"]] = rarity_counts.get(d["rarity"], 0) + 1
        tech_counts[d["tech"]] = tech_counts.get(d["tech"], 0) + 1
        if d["year"] is None:
            missing_year += 1

    print(f"Total classes in DB: {len(DROPSHIP_DB)}")
    print(f"Overrides loaded: {len(DROPSHIP_OVERRIDES)}")
    print(f"Missing intro year: {missing_year}")
    print("Tech counts:", tech_counts)
    print("Rarity counts:", rarity_counts)


def interactive_dropship_roller():
    print("DropShip Class Roller (weighted)")
    print("Type 'q' at any prompt to quit.\n")

    if not DROPSHIP_DB:
        print("No DropShip data loaded.")
        print("Run build_dropship_overrides.py (F5) to generate dropship_overrides.py, then run this again.\n")
        return

    # Tech base
    tech_raw = input("Tech base? (IS / Clan / Any) [Any]: ").strip().lower()
    if tech_raw in ("q", "quit", "exit"):
        print("Terminated.")
        return

    tech_choice = "Any"
    if tech_raw in ("is", "inner sphere", "innersphere"):
        tech_choice = "IS"
    elif tech_raw in ("clan", "clans"):
        tech_choice = "Clan"

    include_unknown_tech = True
    if tech_choice != "Any":
        ans = input("Include 'Unknown tech' DropShips in this tech filter? (y/n) [y]: ").strip().lower()
        if ans in ("q", "quit", "exit"):
            print("Terminated.")
            return
        include_unknown_tech = (ans not in ("n", "no"))

    # Chronology
    year = None
    year_raw = input("Filter by in-universe year? (blank = no filter): ").strip().lower()
    if year_raw in ("q", "quit", "exit"):
        print("Terminated.")
        return

    if year_raw:
        try:
            year = int(year_raw)
            print(f"Year {year} => era: {era_for_year(year)}")
        except ValueError:
            print("Invalid year; continuing with no year filter.")
            year = None

    strict_year = False
    if year is not None:
        sy = input("Strict year filter? (exclude unknown-year designs) (y/n) [n]: ").strip().lower()
        if sy in ("q", "quit", "exit"):
            print("Terminated.")
            return
        strict_year = (sy in ("y", "yes"))

    # Rarity mode
    print("\nRarity mode:")
    print("  1) common only")
    print("  2) common + uncommon")
    print("  3) any (includes rare + very rare + unknown)")
    rm = input("Choose 1/2/3 [3]: ").strip().lower()
    if rm in ("q", "quit", "exit"):
        print("Terminated.")
        return

    rarity_mode = "any"
    if rm == "1":
        rarity_mode = "common"
    elif rm == "2":
        rarity_mode = "common_uncommon"

    # Default behavior: unknown rarity excluded for restricted modes
    include_unknown_rarity = True
    if rarity_mode != "any":
        ans = input("Include 'Unknown rarity' DropShips in this rarity filter? (y/n) [n]: ").strip().lower()
        if ans in ("q", "quit", "exit"):
            print("Terminated.")
            return
        include_unknown_rarity = (ans in ("y", "yes"))
    else:
        include_unknown_rarity = True

    print("\n--- Ready ---\n")

    while True:
        raw = input("How many DropShips do you want to roll? ").strip()
        if raw.lower() in ("q", "quit", "exit"):
            print("Terminated.")
            return

        try:
            n = int(raw)
            if n <= 0:
                print("Please enter a positive integer.\n")
                continue
        except ValueError:
            print("Please enter a whole number (e.g., 1, 5, 20) or 'q' to quit.\n")
            continue

        results = roll_many_dropships(
            n,
            tech_choice=tech_choice,
            year=year,
            strict_year=strict_year,
            rarity_mode=rarity_mode,
            include_unknown_rarity=include_unknown_rarity,
            include_unknown_tech=include_unknown_tech,
        )

        for i, cls in enumerate(results, start=1):
            print(f"DS-{i:02d}: {cls}")
        print()

        again = input("Roll again with same filters? (y/n) ").strip().lower()
        if again not in ("y", "yes"):
            print("Terminated.")
            return


# ============================================================
# Menu
# ============================================================

def main_menu():
    while True:
        choice = input("Roll what? (1=JumpShip, 2=DropShip, 3=Audit DS data, q=quit): ").strip().lower()
        if choice in ("q", "quit", "exit"):
            return
        if choice == "1":
            interactive_jumpship_roller()
            return
        if choice == "2":
            interactive_dropship_roller()
            return
        if choice == "3":
            audit_dropship_db()
            return
        print("Please enter 1, 2, 3, or q.")


if __name__ == "__main__":
    main_menu()
