// scripts/updateData.mjs
import fs from "fs";
import path from "path";

const SHEET_CSV_URL = process.env.SHEET_CSV_URL; // set in GitHub secrets
if (!SHEET_CSV_URL) {
  console.error("Missing SHEET_CSV_URL env var");
  process.exit(1);
}

const outDir = "data";
const outFile = path.join(outDir, "orgs.json");

function parseCSV(text) {
  // simple CSV parser good for “no commas in fields”.
  // If you have commas/quotes, switch to csv-parse.
  const lines = text.trim().split(/\r?\n/);
  const headers = lines.shift().split(",").map(h => h.trim());
  return lines
    .filter(Boolean)
    .map(line => {
      const cols = line.split(",").map(c => c.trim());
      const obj = {};
      headers.forEach((h, i) => (obj[h] = cols[i] ?? ""));
      return obj;
    });
}

const res = await fetch(SHEET_CSV_URL);
if (!res.ok) {
  console.error("Failed to fetch CSV:", res.status, res.statusText);
  process.exit(1);
}
const csvText = await res.text();

const rows = parseCSV(csvText);

const cleaned = rows.filter(r => Object.values(r).some(v => String(v).trim() !== ""));

fs.mkdirSync(outDir, { recursive: true });
fs.writeFileSync(outFile, JSON.stringify(cleaned, null, 2));

console.log(`Wrote ${cleaned.length} records to ${outFile}`);
