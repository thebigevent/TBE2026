import pandas as pd
import json
import re

# ===== CONFIG =====
XLSX_PATH  = "TBE26_SITE_ASSIGNMENTS.xlsx"
SHEET_NAME = "Site Assignments"   # exact sheet name
OUT_PATH   = "assignments.json"

# Actual columns in the xlsx:
#   Group Number | First name | Last name | School |
#   How are you participating in The Big Event? | Organization/RSO |
#   Delegate | Site | Address

# ===== HELPERS =====
def norm(s: str) -> str:
    s = (s or "").strip().lower()
    return re.sub(r"[^a-z0-9]+", "", s)

def clean(v) -> str:
    if v is None or (isinstance(v, float) and str(v) == "nan"):
        return ""
    return str(v).strip()

# ===== LOAD =====
df = pd.read_excel(XLSX_PATH, sheet_name=SHEET_NAME, dtype=str)
print("Columns:", df.columns.tolist())

assignments = {}
dupes = []

for _, r in df.iterrows():
    first = clean(r.get("First name", ""))
    last  = clean(r.get("Last name",  ""))
    site  = clean(r.get("Site",       ""))
    group = clean(r.get("Organization/RSO", ""))
    # "Delegate" column marks the crew/team leader for the group
    crew  = clean(r.get("Delegate",   ""))

    if not first or not last or not site:
        continue

    key  = norm(first + last)
    item = {
        "first":      first,
        "last":       last,
        "site":       site,
        "group":      group,
        "crewLeader": crew,
    }

    if key in assignments:
        if isinstance(assignments[key], dict):
            assignments[key] = [assignments[key], item]
        else:
            assignments[key].append(item)
        dupes.append(key)
    else:
        assignments[key] = item

with open(OUT_PATH, "w", encoding="utf-8") as f:
    json.dump(assignments, f, ensure_ascii=False, indent=2)

print(f"Wrote {OUT_PATH} with {len(assignments)} unique volunteer keys.")
if dupes:
    print(f"Warning: {len(set(dupes))} duplicate name key(s) stored as arrays.")