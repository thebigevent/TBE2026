import pandas as pd
import json
import re

# ===== CONFIG =====
XLSX_PATH   = "TBE Sites.xlsx"          # <- rename to your org workbook filename
SHEET_NAME  = 0                         # <- or "Sites" if you have a named sheet
OUT_PATH    = "sites.json"

# Map your spreadsheet columns -> output fields
COLS = {
    "name": "Service Site Name",        # required
    "address": "Address",
    "tasks": "Tasks",
    "volunteers": "Volunteer Count",
    "notes": "Notes",
    "contactName": "Contact Name",
    "email": "Email",
    "phone": "Phone",
    "publicDescription": "Public Description",
}

# ===== HELPERS =====
def slugify(s: str) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-{2,}", "-", s).strip("-")
    return s

def clean_phone(v):
    if pd.isna(v):
        return ""
    s = str(v).strip()
    # remove trailing .0 from Excel numeric phones
    s = re.sub(r"\.0$", "", s)
    return s

# ===== LOAD =====
df = pd.read_excel(XLSX_PATH, sheet_name=SHEET_NAME)

# Ensure required column exists
if COLS["name"] not in df.columns:
    raise ValueError(f"Missing required column: '{COLS['name']}'")

sites = []
for i, r in df.iterrows():
    name = str(r.get(COLS["name"], "")).strip()
    if not name or name.lower() == "nan":
        continue

    address = str(r.get(COLS["address"], "")).strip()
    tasks = str(r.get(COLS["tasks"], "")).strip()
    notes = str(r.get(COLS["notes"], "")).strip()
    contact = str(r.get(COLS["contactName"], "")).strip()
    email = str(r.get(COLS["email"], "")).strip()
    phone = clean_phone(r.get(COLS["phone"], ""))

    # volunteers: try to coerce to int, else default 0
    vol_raw = r.get(COLS["volunteers"], 0)
    try:
        volunteers = int(vol_raw) if not pd.isna(vol_raw) else 0
    except Exception:
        volunteers = 0

    public_desc = str(r.get(COLS["publicDescription"], "")).strip()

    site_id = f"{len(sites)+1:03d}-{slugify(name)}"

    sites.append({
        "name": name,
        "address": address,
        "tasks": tasks,
        "volunteers": volunteers,
        "notes": notes,
        "contactName": contact,
        "email": email,
        "phone": phone,
        "siteId": site_id,
        "publicDescription": public_desc,
    })

with open(OUT_PATH, "w", encoding="utf-8") as f:
    json.dump(sites, f, ensure_ascii=False, indent=2)

print(f"Wrote {OUT_PATH} with {len(sites)} sites.")

