.PHONY: all clean

all:
	python3 parseAssignments.py
	python3 parseSites.py
	python3 parseSignups.py
	@echo "✅ All JSON files rebuilt."

clean:
	rm -f assignments.json sites.json signups.json
	@echo "🧹 JSON cleaned."

