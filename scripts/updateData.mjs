// scripts/updateData.mjs
// Legacy Node.js entry point – now just delegates to the Python script.
// Kept for backwards compatibility; the GitHub Actions workflow calls
// sync_sheets.py directly via Python.
import { execSync } from "child_process";
try {
  execSync("python3 scripts/sync_sheets.py", { stdio: "inherit" });
} catch (e) {
  process.exit(1);
}
