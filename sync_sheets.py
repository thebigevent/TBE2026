#!/usr/bin/env python3
"""
sync_sheets.py  –  fetch both Google Sheets and write assignments.json + sites.json
Reads two env vars:
  ASSIGNMENTS_SHEET_ID  – spreadsheet ID for the volunteer assignments sheet
  SITES_SHEET_ID        – spreadsheet ID for the service-site bios sheet
Both sheets must be publicly readable (Share → Anyone with the link → Viewer).
"""

import csv
import io
import json
import os
import re
import sys
import ssl
import urllib.request

# ── Sheet IDs ────────────────────────────────────────────────────────────────
ASSIGNMENTS_SHEET_ID = os.environ.get(
    "ASSIGNMENTS_SHEET_ID",
    "1On6ZSx9Y5DiSwHQ8xsA61IR3AqIsZB-frMrHul4HrMs",
)
ASSIGNMENTS_GID = os.environ.get("ASSIGNMENTS_GID", "0")

SITES_SHEET_ID = os.environ.get(
    "SITES_SHEET_ID",
    "1gO41fLDZweadUq0y_Y-0yx0ChU_eI0t9ZpFWx2uS4-c",
)
SITES_GID = os.environ.get("SITES_GID", "0")

# ── Helpers ───────────────────────────────────────────────────────────────────

def csv_url(sheet_id: str, gid: str) -> str:
    return (
        f"https://docs.google.com/spreadsheets/d/{sheet_id}"
        f"/export?format=csv&gid={gid}"
    )


def fetch_csv(url: str) -> list[dict]:
    """Download a Google Sheet as CSV and return list-of-dicts."""
    req = urllib.request.Request(url, headers={"User-Agent": "tbe-sync/1.0"})
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
        raw = resp.read().decode("utf-8-sig")  # strip BOM if present
    reader = csv.DictReader(io.StringIO(raw))
    return [row for row in reader]


def norm(s: str) -> str:
    """Normalise a name for use as a dict key."""
    s = (s or "").strip().lower()
    return re.sub(r"[^a-z0-9]+", "", s)


def slugify(s: str) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return re.sub(r"-{2,}", "-", s).strip("-")


def col(row: dict, *candidates: str) -> str:
    """Return the first matching column value from a row (case-insensitive)."""
    for c in candidates:
        for k in row:
            if (k or "").strip().lower() == c.strip().lower():
                return (row[k] or "").strip()
    return ""


# ── Assignments ───────────────────────────────────────────────────────────────
# Actual sheet columns:
#   Group Number | First name | Last name | School |
#   How are you participating in The Big Event? | Organization/RSO |
#   Delegate | Site | Address

def build_assignments(rows: list[dict]) -> dict:
    assignments: dict = {}
    dupes: list = []

    for r in rows:
        first = col(r, "First name", "First Name", "first")
        last  = col(r, "Last name",  "Last Name",  "last")
        site  = col(r, "Site", "site")
        group = col(r, "Organization/RSO", "Organization", "RSO", "group")
        # "Delegate" is the crew/team leader indicator in this sheet
        crew  = col(r, "Delegate", "Crew Leader", "crew leader", "crew")

        if not first or not last or not site:
            continue  # skip blank rows

        key  = norm(first + last)
        item = {
            "first":      first,
            "last":       last,
            "site":       site,
            "group":      group,
            "crewLeader": crew,
        }

        if key in assignments:
            existing = assignments[key]
            if isinstance(existing, dict):
                assignments[key] = [existing, item]
            else:
                assignments[key].append(item)
            dupes.append(key)
        else:
            assignments[key] = item

    if dupes:
        print(f"  ⚠️  {len(set(dupes))} duplicate name key(s) stored as arrays.")
    return assignments


# ── Sites ─────────────────────────────────────────────────────────────────────
# Actual sheet columns:
#   Site Name | Contact Name | Phone Number | Email | Site Address |
#   Tasks That Will Be Performed | Task Performed Text Entry |
#   Special Notes | Bio

def build_sites(rows: list[dict]) -> list[dict]:
    sites = []

    for r in rows:
        name = col(r, "Site Name", "Service Site Name", "Name", "name")
        if not name:
            continue

        # Badge labels – already comma-separated task types
        tasks = col(r, "Tasks That Will Be Performed", "Tasks", "Task(s)")

        # Free-text work description (stored, shown on results page)
        work_desc = col(r, "Task Performed Text Entry", "Work Description",
                        "Public Description", "Description")

        # Organisation background / bio (shown labeled on org + results pages)
        bio = col(r, "Bio", "Organization Bio", "About the Organization", "About")

        public_desc = work_desc

        vol_raw = col(r, "Volunteer Count", "Volunteers", "Volunteers Needed", "# Volunteers")
        try:
            volunteers = int(float(vol_raw)) if vol_raw else 0
        except ValueError:
            volunteers = 0

        site_id = f"{len(sites)+1:03d}-{slugify(name)}"

        sites.append({
            "siteId":            site_id,
            "name":              name,
            "address":           col(r, "Site Address", "Address", "address"),
            "tasks":             tasks,
            "volunteers":        volunteers,
            "notes":             col(r, "Special Notes", "Notes", "notes", "Additional Notes"),
            "contactName":       col(r, "Contact Name", "contact name", "Contact"),
            "email":             col(r, "Email", "email", "Contact Email"),
            "phone":             col(r, "Phone Number", "Phone", "phone", "Contact Phone"),
            "publicDescription": public_desc,
            "bio":               bio,
        })

    return sites


# ── Main ──────────────────────────────────────────────────────────────────────

def write_json(path: str, data) -> None:
    os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main():
    errors = []

    # --- Assignments ---
    print("📥 Fetching assignments sheet …")
    try:
        url  = csv_url(ASSIGNMENTS_SHEET_ID, ASSIGNMENTS_GID)
        rows = fetch_csv(url)
        print(f"   {len(rows)} rows fetched.")
        assignments = build_assignments(rows)
        write_json("assignments.json", assignments)
        print(f"✅ assignments.json  ({len(assignments)} unique volunteer keys)")
    except Exception as e:
        errors.append(f"assignments: {e}")
        print(f"❌ Failed to update assignments.json: {e}", file=sys.stderr)

    # --- Sites ---
    print("📥 Fetching service-site bios sheet …")
    try:
        url  = csv_url(SITES_SHEET_ID, SITES_GID)
        rows = fetch_csv(url)
        print(f"   {len(rows)} rows fetched.")
        sites = build_sites(rows)
        write_json("sites.json", sites)
        print(f"✅ sites.json  ({len(sites)} sites)")
    except Exception as e:
        errors.append(f"sites: {e}")
        print(f"❌ Failed to update sites.json: {e}", file=sys.stderr)

    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()