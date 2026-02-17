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
ASSIGNMENTS_GID = os.environ.get("ASSIGNMENTS_GID", "1887412390")

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


# ── Assignments ───────────────────────────────────────────────────────────────

def build_assignments(rows: list[dict]) -> dict:
    """
    Expected columns (case-insensitive, flexible):
      First name / First Name / first
      Last name  / Last Name  / last
      Site
      Organization/RSO  (optional)
      Crew Leader (optional)
    """
    # Normalise header lookup
    def col(row: dict, *candidates: str) -> str:
        for c in candidates:
            for k in row:
                if k.strip().lower() == c.lower():
                    return (row[k] or "").strip()
        return ""

    assignments: dict = {}
    dupes: list = []

    for r in rows:
        first = col(r, "First name", "First Name", "first")
        last  = col(r, "Last name",  "Last Name",  "last")
        site  = col(r, "Site", "site")
        group = col(r, "Organization/RSO", "Organization", "RSO", "group")
        crew  = col(r, "Crew Leader", "crew leader", "crew")

        if not first or not last or not site:
            continue  # skip empty rows

        key  = norm(first + last)
        item = {
            "first": first,
            "last":  last,
            "site":  site,
            "group": group,
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

def build_sites(rows: list[dict]) -> list[dict]:
    """
    Expected columns (adapt to whatever the bios sheet uses):
      Service Site Name  (required)
      Address
      Tasks
      Volunteer Count
      Notes
      Contact Name
      Email
      Phone
      Public Description
    """
    def col(row: dict, *candidates: str) -> str:
        for c in candidates:
            for k in row:
                if k.strip().lower() == c.lower():
                    return (row[k] or "").strip()
        return ""

    sites = []
    for r in rows:
        name = col(r, "Service Site Name", "Site Name", "Name", "name")
        if not name:
            continue

        # volunteers: coerce to int
        vol_raw = col(r, "Volunteer Count", "Volunteers", "volunteer count")
        try:
            volunteers = int(float(vol_raw)) if vol_raw else 0
        except ValueError:
            volunteers = 0

        site_id = f"{len(sites)+1:03d}-{slugify(name)}"

        sites.append({
            "siteId":            site_id,
            "name":              name,
            "address":           col(r, "Address", "address"),
            "tasks":             col(r, "Tasks", "tasks"),
            "volunteers":        volunteers,
            "notes":             col(r, "Notes", "notes"),
            "contactName":       col(r, "Contact Name", "contact name"),
            "email":             col(r, "Email", "email"),
            "phone":             col(r, "Phone", "phone"),
            "publicDescription": col(r, "Public Description", "public description", "Description"),
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
        url = csv_url(ASSIGNMENTS_SHEET_ID, ASSIGNMENTS_GID)
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
        url = csv_url(SITES_SHEET_ID, SITES_GID)
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