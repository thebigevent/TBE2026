import pandas as pd
import json
import re

CSV_PATH  = "Volunteer Signups.csv"   # Google Form export
OUT_PATH  = "signups.json"

def norm(s: str) -> str:
    s = (s or "").strip().lower()
    return re.sub(r"[^a-z0-9]+", "", s)

def clean_phone(v):
    if pd.isna(v):
        return ""
    s = str(v).strip()
    s = re.sub(r"\.0$", "", s)
    return s

df = pd.read_csv(CSV_PATH)

# Update these to match your form headers
FIRST_COL = "First Name"
LAST_COL  = "Last Name"
EMAIL_COL = "Email"
PHONE_COL = "Phone"
ORG_COL   = "Preferred Organization"   # optional
TS_COL    = "Timestamp"               # optional

required = [FIRST_COL, LAST_COL]
for c in required:
    if c not in df.columns:
        raise ValueError(f"Missing required column: '{c}'")

signups = {}
dupes = []

for _, r in df.iterrows():
    first = str(r.get(FIRST_COL, "")).strip()
    last  = str(r.get(LAST_COL, "")).strip()
    if not first or not last or first.lower() == "nan" or last.lower() == "nan":
        continue

    key = norm(first + last)

    item = {
        "first": first,
        "last": last,
        "email": str(r.get(EMAIL_COL, "")).strip() if EMAIL_COL in df.columns else "",
        "phone": clean_phone(r.get(PHONE_COL, "")) if PHONE_COL in df.columns else "",
        "preferredOrg": str(r.get(ORG_COL, "")).strip() if ORG_COL in df.columns else "",
        "timestamp": str(r.get(TS_COL, "")).strip() if TS_COL in df.columns else "",
    }

    if key in signups:
        if isinstance(signups[key], dict):
            signups[key] = [signups[key], item]
        else:
            signups[key].append(item)
        dupes.append(key)
    else:
        signups[key] = item

with open(OUT_PATH, "w", encoding="utf-8") as f:
    json.dump(signups, f, ensure_ascii=False, indent=2)

print(f"Wrote {OUT_PATH} with {len(signups)} unique volunteer keys.")
if dupes:
    print(f"Warning: {len(set(dupes))} duplicate name keys (stored as arrays).")

