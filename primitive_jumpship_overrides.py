# primitive_jumpship_overrides.py
# Only put entries here that you want to override.

PRIMITIVE_JS_OVERRIDES = {
    # Only two ships built by 2325 -> make it a known intro-year + very rare
    "Kaiser": {"year": 2325, "rarity": "very_rare"},

    # Built in large numbers -> bump rarity up
    "Predator": {"rarity": "common"},

    # Keep going as needed:
    # "Type 51": {"rarity": "common"},
    # "Vritra": {"rarity": "uncommon"},
}
