import gspread
import pandas as pd
from gspread_dataframe import get_as_dataframe
from datetime import datetime
import json
import os

# --- Configuration ---
CREDENTIALS_PATH = "credentials_gsheet.json"
SHEET_URL = "https://docs.google.com/spreadsheets/d/1nrG329whDaeVv8BpocWUuSc-lgv-TJVf6RIxW3Bd8jg/edit"
CSV_PATH = "data/patogenos_prioritarios.csv"
JSON_PATH = "data/patogenos_prioritarios.json"

# --- Fetch data from Google Sheet ---
gc = gspread.service_account(filename=CREDENTIALS_PATH)
spreadsheet = gc.open_by_url(SHEET_URL)

# --- Define priority pathogen list ---
# Load the "pathogens" worksheet and parse it
worksheet = spreadsheet.worksheet("pathogens")
data = worksheet.get_all_values()
patho_df = pd.DataFrame(data[1:], columns=data[0])  # Use first row as headers
patho_df = patho_df.dropna(how="all")  # Drop rows where all elements are NaN
if "taxids" in patho_df.columns:
    patho_df["taxids"] = pd.to_numeric(patho_df["taxids"], errors="coerce").astype("Int64")

# --- Define priority sources ---
# Load the "organizations" worksheet and parse it
org_ws = spreadsheet.worksheet("organizations")
org_df = get_as_dataframe(org_ws).dropna(how="all")

# Get active organizations only
active_orgs = org_df[org_df["Added?"] == 1]
import pdb; pdb.set_trace()
# Build priority_sources list and source_urls dict
priority_sources = active_orgs["Acronym"].dropna().tolist()

source_urls = {
    row["Acronym"]: row["url list"]
    for _, row in active_orgs.iterrows()
    if pd.notna(row["Acronym"]) and pd.notna(row["url list"])
}
priority_sources = active_orgs["Acronym"].dropna().drop_duplicates().tolist()

# --- Build JSON structure ---
json_output = {
    "full_name": "PDN Pathogen Priority List",
    "source_urls": source_urls,
    "last_updated": datetime.now().strftime("%Y-%m-%d"),
    "taxa": [],
}

for _, row in patho_df.iterrows():
    pathogen_entry = {}

    # Compute prioritized_by from active sources only
    prioritized = [
        source
        for source in priority_sources
        if str(row.get(source)).strip().upper() == "X"
    ]

    for col in patho_df.columns:
        if col in priority_sources:
            continue  # skip org columns handled via prioritized_by
        elif col == "Priority type":
            val = row[col]
            if pd.notna(val) and str(val).strip():
                pathogen_entry[col] = [x.strip() for x in str(val).split(",")]
        elif col in [
            "Number of priority lists",
            "Number of appearances (WHO, NIAD, ECDC)",
            "Number of appearances (WHO, NIAD, ECDC, AFRICACDC)",
        ]:
            continue  # we compute these separately
        else:
            val = row[col]
            if pd.notna(val) and str(val).strip() != "":
                pathogen_entry[col] = val

    # Inject prioritized_by
    pathogen_entry["prioritized_by"] = prioritized
    # Inject calculated fields
    pathogen_entry["Number of priority lists"] = len(
        pathogen_entry.get("Priority type", [])
    )
    pathogen_entry["Number of appearances (WHO, NIAID, ECDC)"] = sum(
        1 for x in ["WHO", "NIAID", "ECDC"] if x in prioritized
    )
    pathogen_entry["Number of appearances (WHO, NIAID, ECDC, AFRICACDC)"] = sum(
        1 for x in ["WHO", "NIAID", "ECDC", "AFRICACDC"] if x in prioritized
    )

    json_output["taxa"].append(pathogen_entry)

# --- Save outputs ---
os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)
patho_df.to_csv(CSV_PATH, index=False)

with open(JSON_PATH, "w", encoding="utf-8") as f:
    json.dump(json_output, f, indent=2, ensure_ascii=False)

print(f"✅ CSV saved to {CSV_PATH}")
print(f"✅ JSON saved to {JSON_PATH}")
