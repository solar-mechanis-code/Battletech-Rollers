import json
import re
import time
import html as ihtml
from urllib.request import Request, urlopen
from urllib.parse import urljoin


BASE = "https://www.sarna.net"
CATEGORY_URL = f"{BASE}/wiki/Category:DropShip_classes"

USER_AGENT = "Mozilla/5.0 (compatible; BT-DropShip-Roller/1.1; +https://www.sarna.net)"
REQUEST_DELAY_SEC = 0.35  # be polite


# -----------------------------
# Fetch / parsing helpers
# -----------------------------

def fetch(url: str, timeout: int = 30) -> str:
    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=timeout) as resp:
        data = resp.read()
    return data.decode("utf-8", errors="replace")


def fetch_raw_wikitext(page_url: str) -> str:
    sep = "&" if "?" in page_url else "?"
    return fetch(page_url + sep + "action=raw")


def strip_tags(html_text: str) -> str:
    html_text = re.sub(r"(?is)<script.*?>.*?</script>", " ", html_text)
    html_text = re.sub(r"(?is)<style.*?>.*?</style>", " ", html_text)
    html_text = re.sub(r"(?is)<!--.*?-->", " ", html_text)
    text = re.sub(r"(?is)<[^>]+>", " ", html_text)
    text = ihtml.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def normalize_name(title: str) -> str:
    title = re.sub(r"\s*\(DropShip class\)\s*$", "", title, flags=re.I)
    title = re.sub(r"\s*\(DropShuttle class\)\s*$", "", title, flags=re.I)
    return title.strip()


def extract_mw_pages_block(page_html: str) -> str:
    m = re.search(r'(?is)<div[^>]+id="mw-pages"[^>]*>(.*?)<div[^>]+class="printfooter"', page_html)
    if m:
        return m.group(1)
    return page_html


def get_category_members(category_url: str):
    """
    Returns list of (title, href) for all members of the category, following 'next page' if present.
    """
    members = []
    seen_pages = set()
    url = category_url

    while url and url not in seen_pages:
        seen_pages.add(url)
        html_page = fetch(url)
        block = extract_mw_pages_block(html_page)

        for href, title in re.findall(r'(?is)<a[^>]+href="(/wiki/[^"]+)"[^>]+title="([^"]+)"', block):
            title = ihtml.unescape(title)
            if title.startswith("Category:"):
                continue
            if href.startswith("/wiki/Special:"):
                continue
            members.append((title, href))

        next_match = re.search(r'(?is)<a[^>]+href="([^"]+)"[^>]*>\s*next page\s*</a>', block)
        if next_match:
            next_href = ihtml.unescape(next_match.group(1))
            url = urljoin(BASE, next_href)
        else:
            url = None

        time.sleep(REQUEST_DELAY_SEC)

    dedup = []
    seen = set()
    for t, h in members:
        if h not in seen:
            seen.add(h)
            dedup.append((t, h))
    return dedup


# -----------------------------
# Infobox extraction (wikitext)
# -----------------------------

def extract_infobox_fields_from_wikitext(wt: str):
    """
    Parse infobox parameters from raw wikitext.
    This is much more reliable than HTML text scraping.
    """
    def find_year(keys):
        for k in keys:
            m = re.search(rf"(?im)^\s*\|\s*{k}\s*=\s*(.+?)\s*$", wt)
            if m:
                m2 = re.search(r"\b(\d{4})\b", m.group(1))
                if m2:
                    return int(m2.group(1))
        return None

    def find_tech(keys):
        for k in keys:
            m = re.search(rf"(?im)^\s*\|\s*{k}\s*=\s*(.+?)\s*$", wt)
            if m:
                v = m.group(1).lower()
                if "inner sphere" in v:
                    return "IS"
                if "clan" in v:
                    return "Clan"
        return None

    year = find_year([
        r"production\s*year",
        r"introduced",
        r"introduction",
        r"year",
        r"first\s*produced",
        r"entered\s*service",
    ])

    tech = find_tech([
        r"tech\s*base",
        r"techbase",
    ])

    return year, tech


# Fallback (HTML-text) extraction
def extract_infobox_fields_from_text(page_text: str):
    year = None
    tech = None

    m = re.search(r"\bProduction\s*Year\b\s*(\d{4})", page_text, flags=re.I)
    if not m:
        m = re.search(r"\bIntroduced\b\s*(\d{4})", page_text, flags=re.I)
    if m:
        year = int(m.group(1))

    m = re.search(r"\bTech\s*Base\b\s*(Inner Sphere|Clan)", page_text, flags=re.I)
    if m:
        tech = "IS" if m.group(1).lower().startswith("inner") else "Clan"

    return year, tech


# -----------------------------
# Rarity guesser (heuristic)
# -----------------------------

RARITY_PATTERNS = [
    ("common", [
        r"\bmost common\b",
        r"\bamong the most common\b",
        r"\bubiquitous\b",
        r"\bmass[- ]produced\b",
        r"\bproduced in large numbers\b",
        r"\bworkhorse\b",
        r"\bmainstay\b",
        r"\bwidely used\b",
        r"\bcommonly encountered\b",
        r"\bfrequently encountered\b",
    ]),
    ("uncommon", [
        r"\buncommon\b",
        r"\brelatively uncommon\b",
        r"\bless common\b",
        r"\bnot as common\b",
        r"\blimited production\b",
        r"\bproduced in limited numbers\b",
        r"\bbuilt in limited numbers\b",
        r"\bsmall production run\b",
    ]),
    ("very_rare", [
        r"\bnear extinction\b",
        r"\bneared extinction\b",
        r"\bextinct\b",
        r"\bone[- ]of[- ]a[- ]kind\b",
        r"\bonly\s+\d+\s+(?:were|was)\s+(?:built|constructed|produced)\b",
        r"\bonly\s+\d+\s+(?:built|constructed|produced)\b",
        r"\b(single|sole)\s+(?:example|prototype)\b",
    ]),
    ("rare", [
        r"\bmuch rarer\b",
        r"\brarely encountered\b",
        r"\brarely seen\b",
        r"\brarely used\b",
        r"\bhandful\b",
        r"\bprototype\b",
        r"\bexperimental\b",
        r"\bshort production run\b",
        r"\bfew were built\b",
        r"\bproduced in small numbers\b",
    ]),
]


def guess_rarity(article_text: str):
    """
    Returns (rarity, evidence_list).
    Rarity is 'common'/'uncommon'/'rare'/'very_rare'/'unknown'.
    """
    t = article_text.lower()

    start = t.find("description")
    window = t[start:start + 4000] if start != -1 else t[:4000]

    evidence = []
    hits = set()

    # Scarcity priority beats commonness if both match
    priority = ["very_rare", "rare", "uncommon", "common"]
    found = {k: False for k in priority}

    for bucket, patterns in RARITY_PATTERNS:
        for pat in patterns:
            if re.search(pat, window, flags=re.I):
                found[bucket] = True
                if pat not in hits:
                    hits.add(pat)
                    evidence.append(f"{bucket}: /{pat}/")

    for bucket in priority:
        if found.get(bucket):
            return bucket, evidence[:8]

    return "unknown", []


# -----------------------------
# Main build
# -----------------------------

def build_overrides():
    print("Scraping DropShip class list from Sarna category...")
    members = get_category_members(CATEGORY_URL)
    print(f"Found {len(members)} category members.")

    overrides = {}
    failures = []

    for idx, (title, href) in enumerate(members, start=1):
        url = urljoin(BASE, href)
        try:
            # 1) Prefer infobox fields from raw wikitext
            wt = fetch_raw_wikitext(url)
            year, tech = extract_infobox_fields_from_wikitext(wt)

            # 2) Use HTML text for rarity guessing (prose)
            html_page = fetch(url)
            text = strip_tags(html_page)

            # 3) Fallback for year/tech if raw parse misses
            if year is None or tech is None:
                y2, t2 = extract_infobox_fields_from_text(text)
                year = year if year is not None else y2
                tech = tech if tech is not None else t2

            rarity, evidence = guess_rarity(text)

            name = normalize_name(title)

            overrides[name] = {
                "year": year,           # int or None
                "tech": tech,           # "IS"/"Clan"/None
                "rarity": rarity,       # "common"/"uncommon"/"rare"/"very_rare"/"unknown"
                "evidence": evidence,   # regex hit evidence
                "source_title": title,
                "source_url": url,
            }

            if idx % 10 == 0:
                print(f"  ...{idx}/{len(members)} done")

        except Exception as e:
            failures.append((title, url, str(e)))

        time.sleep(REQUEST_DELAY_SEC)

    return overrides, failures


def write_outputs(overrides, failures):
    with open("dropship_overrides.json", "w", encoding="utf-8") as f:
        json.dump(overrides, f, indent=2, ensure_ascii=False)

    with open("dropship_overrides.py", "w", encoding="utf-8") as f:
        f.write("# Auto-generated from Sarna DropShip class pages.\n")
        f.write("# year/tech from infobox when present; rarity is heuristic from prose.\n\n")
        f.write("DROPSHIP_OVERRIDES = ")
        f.write(repr(overrides))
        f.write("\n")

    if failures:
        with open("dropship_failures.txt", "w", encoding="utf-8") as f:
            for title, url, err in failures:
                f.write(f"{title}\t{url}\t{err}\n")

    print("\nWrote:")
    print("  - dropship_overrides.json")
    print("  - dropship_overrides.py")
    if failures:
        print(f"  - dropship_failures.txt ({len(failures)} failures)")


if __name__ == "__main__":
    overrides, failures = build_overrides()
    write_outputs(overrides, failures)
