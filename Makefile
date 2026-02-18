.PHONY: all sync clean

all: sync

# Pull live data from Google Sheets (requires internet access)
sync:
	python3 sync_sheets.py
	@echo "✅ assignments.json and sites.json updated from Google Sheets."

# Legacy: rebuild from local Excel/CSV files if you have them
local:
	python3 parseAssignments.py
	python3 parseSites.py
	python3 parseSignups.py
	@echo "✅ All JSON files rebuilt from local files."

clean:
	rm -f assignments.json sites.json signups.json
	@echo "🧹 JSON cleaned."
