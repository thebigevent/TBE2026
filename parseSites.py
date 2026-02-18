import pandas as pd
import json
import re

# ===== CONFIG =====
XLSX_PATH  = "TBE26_Service_Site_Bios.xlsx"
SHEET_NAME = 0        # first sheet ("Sheet1")
OUT_PATH   = "sites.json"

# Actual columns in the xlsx:
#   Site Name | Contact Name | Phone Number | Email | Site Address |
#   Tasks That Will Be Performed | Task Performed Text Entry |
#   Special Notes | Bio

# ===== HELPERS =====
def slugify(s: str) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return re.sub(r"-{2,}", "-", s).strip("-")

def clean(v) -> str:
    """Coerce a cell value to a clean string, handling NaN and trailing .0."""
    if v is None or (isinstance(v, float) and str(v) == "nan"):
        return ""
    s = str(v).strip()
    s = re.sub(r"\.0$", "", s)  # strip Excel trailing .0 on numeric fields
    return s

# ===== LOAD =====
df = pd.read_excel(XLSX_PATH, sheet_name=SHEET_NAME, dtype=str)
print("Columns:", df.columns.tolist())

sites = []
for _, r in df.iterrows():
    name = clean(r.get("Site Name", ""))
    if not name:
        continue

    # Task badge labels — comma-separated, shown as blue chips
    tasks = clean(r.get("Tasks That Will Be Performed", ""))

    # Org background bio — shown labeled on the org page
    bio = clean(r.get("Bio", ""))

    # Work description — stored but not shown on org page
    work_desc = clean(r.get("Task Performed Text Entry", ""))

    # Special notes
    notes = clean(r.get("Special Notes", ""))

    site_id = f"{len(sites)+1:03d}-{slugify(name)}"

    sites.append({
        "siteId":            site_id,
        "name":              name,
        "address":           clean(r.get("Site Address", "")),
        "tasks":             tasks,
        "volunteers":        0,
        "notes":             notes,
        "contactName":       clean(r.get("Contact Name", "")),
        "email":             clean(r.get("Email", "")),
        "phone":             clean(r.get("Phone Number", "")),
        "bio":               bio,
        "publicDescription": work_desc,
    })

with open(OUT_PATH, "w", encoding="utf-8") as f:
    json.dump(sites, f, ensure_ascii=False, indent=2)

print(f"Wrote {OUT_PATH} with {len(sites)} sites.")