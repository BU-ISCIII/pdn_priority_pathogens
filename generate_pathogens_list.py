from collections import defaultdict
import gspread
import pandas as pd
from gspread_dataframe import get_as_dataframe
from datetime import datetime
import json
import os

# --- Configuration ---
CREDENTIALS_PATH = "credentials_gsheet.json"
SHEET_URL = "https://docs.google.com/spreadsheets/d/1nrG329whDaeVv8BpocWUuSc-lgv-TJVf6RIxW3Bd8jg/edit"
CSV_PATH = "data/complete_priority_pathogens.csv"
JSON_PATH = "data/complete_priority_pathogens.json"
PDN_JSON_PATH = "data/pdn_priority_pathogens.json"


def compute_score(entry):
    """Define a scoring function to compute the score of a pathogen based on its attributes.
    The score is computed as follows:
    - Number of appearances (WHO, NIAID, ECDC) * 1
    - Number of priority lists * 2
    - WasteWater * 1
    - Fungi * 3
    - Parasite (Protozoa) * 4
    The higher the score, the more priority the pathogen has.
    The score is used to rank the pathogens in the final JSON output.

    Parameters
    ----------
    entry : dict
        A dictionary representing a pathogen entry from the Google Sheet.
        The dictionary contains the following   keys:
        - "Number of appearances (WHO, NIAID, ECDC)"
        - "Number of priority lists"
        - "WasteWater"
        - "Pathogen Type"
        The values of these keys are used to compute the score.

    Returns
    -------
    int
        The score is an integer value that represents the priority of the pathogen.
    """
    # Compute the score based on the attributes of the pathogen
    appearances1 = entry.get("Number of appearances (WHO, NIAID, ECDC)", 0)
    appearances2 = entry.get("Number of appearances (WHO, NIAID, ECDC, AFRICACDC)", 0)
    priority_types = entry.get("Number of priority lists", 0)
    wastewater = 1 if str(entry.get("WasteWater", "")).strip().lower() == "yes" else 0
    base = appearances1 * 1 + appearances2 * 2 + priority_types * 1 + wastewater * 1
    if entry.get("Pathogen Type") == "Fungi":
        base += 3
    elif entry.get("Pathogen Type") == "Parasite (Protozoa)":
        base += 4
    return base


def load_pathogen_data(spreadsheet):
    """Load the pathogen data from the Google Sheet and return it as a DataFrame.

    Parameters
    ----------
    spreadsheet
        gspread.Spreadsheet
            The gspread.Spreadsheet object representing the Google Sheet.

    Returns
    -------
    pd.DataFrame
        A pandas DataFrame containing the pathogen data.
        The DataFrame contains the following columns:
        - "Pathogen"
        - "Pathogen Type"
        - "Taxids"
        - "Priority type"
        - "Number of priority lists"
        - "Number of appearances (WHO, NIAID, ECDC)"
        - "Number of appearances (WHO, NIAID, ECDC, AFRICACDC)"
        - etc.
    """
    ws = spreadsheet.worksheet("pathogens")
    data = ws.get_all_values()
    df = pd.DataFrame(data[1:], columns=data[0])
    df = df.dropna(how="all")
    if "taxids" in df.columns:
        df["taxids"] = pd.to_numeric(df["taxids"], errors="coerce").astype("Int64")
    return df


def load_organizations(spreadsheet):
    """Load the organizations data from the Google Sheet and return it as a DataFrame.

    Parameters
    ----------
    spreadsheet
        gspread.Spreadsheet
            The gspread.Spreadsheet object representing the Google Sheet.

    Returns
    -------
    pd.DataFrame
        A pandas DataFrame containing the organizations data.
        The DataFrame contains the following columns:
        - "Acronym"
        - "url list"
        - "Added?"
    """
    ws = spreadsheet.worksheet("organizations")
    df = get_as_dataframe(ws).dropna(how="all")
    return df[df["Added?"] == 1]


def build_source_urls(active_orgs):
    """Build a dictionary of source URLs from the active organizations DataFrame.

    Parameters
    ----------
    active_orgs
        pd.DataFrame
            A pandas DataFrame containing the organizations data.
            The DataFrame contains the following columns:
            - "Acronym"
            - "url list"
            - "Added?"

    Returns
    -------
    dict
        A dictionary where the keys are the acronyms of the organizations
        and the values are lists of URLs associated with each acronym.
        The URLs are extracted from the "url list" column of the DataFrame.
        Each URL is stripped of leading and trailing whitespace.
    """

    urls = defaultdict(list)
    for _, row in active_orgs.iterrows():
        acronym = row["Acronym"]
        url_list = str(row["url list"]).strip()
        if pd.notna(acronym) and url_list:
            urls[acronym].extend(u.strip() for u in url_list.split("\n") if u.strip())
    return dict(urls)


def transform_pathogen_row(row, priority_sources):
    """Transform a row of the pathogen DataFrame into a dictionary entry.

    Parameters
    ----------
    row
        pd.Series
            A pandas Series representing a row of the pathogen DataFrame.
    priority_sources
        list
            A list of acronyms representing the priority sources.
            The acronyms are used to identify the organizations that prioritized the pathogen.

    Returns
    -------
    dict
        A dictionary representing the pathogen entry.
        The dictionary contains the following keys:
        - "Pathogen"
        - "Pathogen Type"
        - "Taxids"
        - "Priority type"
        - "Number of priority lists"
        - "Number of appearances (WHO, NIAID, ECDC)"
        - "Number of appearances (WHO, NIAID, ECDC, AFRICACDC)"
        - etc.
    """    
    entry = {}
    prioritized_by = [
        source
        for source in priority_sources
        if str(row.get(source)).strip().upper() == "X"
    ]
    for col in row.index:
        if col in priority_sources:
            continue
        val = row[col]
        if col == "Priority type" and pd.notna(val):
            entry[col] = [x.strip() for x in str(val).split(",")]
        elif (
            col
            not in [
                "Number of priority lists",
                "Number of appearances (WHO, NIAD, ECDC)",
                "Number of appearances (WHO, NIAD, ECDC, AFRICACDC)",
                "Priority order",
                "Priority score",
            ]
            and pd.notna(val)
            and str(val).strip()
        ):
            entry[col] = val
    entry["prioritized_by"] = prioritized_by
    entry["Number of priority lists"] = sum(
        1 for p in entry.get("Priority type", []) if p != "Animal disease"
    )
    entry["Number of appearances (WHO, NIAID, ECDC)"] = sum(
        1 for x in ["WHO", "NIAID", "ECDC"] if x in prioritized_by
    )
    entry["Number of appearances (WHO, NIAID, ECDC, AFRICACDC)"] = sum(
        1 for x in ["WHO", "NIAID", "ECDC", "AFRICACDC"] if x in prioritized_by
    )
    return entry


def apply_inclusion_criteria(entry):
    """Apply inclusion criteria to determine if a pathogen entry should be included in the final JSON output.

    Parameters
    ----------
    entry
        dict
            A dictionary representing a pathogen entry from the Google Sheet.
            The dictionary contains the following keys:
            - "prioritized_by"
            - "Number of priority lists"
            - "Pathogen Type"

    Returns
    -------
    bool
        True if the entry meets the inclusion criteria, False otherwise.
        The inclusion criteria are as follows:
        - The pathogen must be prioritized by at least 2 organizations (WHO, NIAID, ECDC)
        - The pathogen must be listed in at least 2 priority lists
    """
    n_appearances = entry.get("Number of appearances (WHO, NIAID, ECDC)", 0)
    n_priority_types = entry.get("Number of priority lists", 0)

    return n_appearances >= 2 and n_priority_types >= 2


def add_scoring(entry):
    """Add scoring to the pathogen entry based on its attributes.

    Parameters
    ----------
    entry
        dict
            A dictionary representing a pathogen entry from the Google Sheet.
            The dictionary contains the following keys:
            - "Number of appearances (WHO, NIAID, ECDC)"
            - "Number of priority lists"
            - "WasteWater"
            - "Pathogen Type"

    Returns
    -------
    dict
        The input dictionary with additional keys:
        - "Priority score (computed)"
        - "Highest priority"
        The "Priority score (computed)" key contains the computed score of the pathogen.
        The "Highest priority" key is a boolean indicating if the score is greater than or equal to 12.
    """
    score = compute_score(entry)
    entry["Priority score"] = score
    entry["Highest priority"] = score >= 12
    return entry


def assign_priority_order(taxa, score_field="Priority score (computed)"):
    """Assign a priority order based on the score field.

    Parameters
    ----------
    taxa : list of dict
        The list of pathogen entries.
    score_field : str
        The key to use for sorting entries (default: Priority score (computed)).

    Returns
    -------
    list of dict
        The same list, with each entry updated with a new key: Priority order (computed).
    """
    sorted_taxa = sorted(taxa, key=lambda x: x.get(score_field, 0), reverse=True)
    for i, entry in enumerate(sorted_taxa, start=1):
        entry["Priority order"] = i
    return sorted_taxa


def main():
    gc = gspread.service_account(filename=CREDENTIALS_PATH)
    spreadsheet = gc.open_by_url(SHEET_URL)

    patho_df = load_pathogen_data(spreadsheet)
    active_orgs = load_organizations(spreadsheet)
    priority_sources = active_orgs["Acronym"].dropna().drop_duplicates().tolist()
    source_urls = build_source_urls(active_orgs)

    complete_json = {
        "full_name": "Complete Pathogen Priority List",
        "source_urls": source_urls,
        "last_updated": datetime.now().strftime("%Y-%m-%d"),
        "taxa": [],
    }

    for _, row in patho_df.iterrows():
        entry = transform_pathogen_row(row, priority_sources)
        entry = add_scoring(entry)
        complete_json["taxa"].append(entry)

    # Write complete list
    os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)
    patho_df.to_csv(CSV_PATH, index=False)

    complete_json["taxa"] = assign_priority_order(complete_json["taxa"])
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(complete_json, f, indent=2, ensure_ascii=False)

    # Apply inclusion criteria
    pdn_taxa = [e for e in complete_json["taxa"] if apply_inclusion_criteria(e)]
    pdn_taxa = assign_priority_order(pdn_taxa)

    pdn_json = {
        "full_name": "PDN Pathogen Priority List",
        "source_urls": source_urls,
        "last_updated": datetime.now().strftime("%Y-%m-%d"),
        "taxa": [],
    }
    pdn_json["taxa"] = pdn_taxa
    with open(PDN_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(pdn_json, f, indent=2, ensure_ascii=False)

    print(f"✅ CSV saved to {CSV_PATH}")
    print(f"✅ JSON saved to {JSON_PATH}")
    print(f"✅ PDN JSON saved to {PDN_JSON_PATH}")


if __name__ == "__main__":
    main()
