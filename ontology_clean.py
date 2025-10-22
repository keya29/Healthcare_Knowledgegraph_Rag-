# ontology_clean.py
from pathlib import Path

raw_path = Path("desc2025.xml")
clean_path = Path("desc2025_clean.xml")

# Read and ignore invalid characters
with open(raw_path, "r", encoding="utf-8", errors="ignore") as f:
    clean_content = f.read()

# Save cleaned XML
with open(clean_path, "w", encoding="utf-8") as f:
    f.write(clean_content)

print(f"[INFO] Cleaned XML saved to {clean_path}")
