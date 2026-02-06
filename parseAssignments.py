import pandas as pd
import json
import re

XLSX_PATH = "TLE 2025 SITE ASSIGNMENTS.xlsx"
OUT_PATH  = "assignments.json"

def norm(s: str) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"[^a-z0-9]+", "", s)   # keep alnum only
    return s

df = pd.read_excel(XLSX_PATH, sheet_name="Big Master Sheet")

# pick the main assignment columns
df = df.rename(columns={
    "First Name": "first",
    "Last Name": "last",
    "Service Site": "site",
    "Group": "group"
})

df = df[["first", "last", "site", "group"]].dropna(subset=["first", "last", "site"])

assignments = {}
dupes = []

for _, r in df.iterrows():
    first = str(r["first"]).strip()
    last  = str(r["last"]).strip()
    site  = str(r["site"]).strip()
    group = "" if pd.isna(r["group"]) else str(r["group"]).strip()

    key = norm(first + last)

    item = {"first": first, "last": last, "site": site, "group": group}

    if key in assignments:
        # handle duplicates by storing a list
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
    print(f"Warning: {len(set(dupes))} duplicate name keys (stored as arrays).")
