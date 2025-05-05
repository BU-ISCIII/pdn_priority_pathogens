# 🦠 PDN Priority Pathogens List

This repository is part of the [PDN (Pathogen Data Network)](https://pathogendatanetwork.org/) initiative and contains a curated, updatable list of priority pathogens. The aim is to centralize information from various international organizations and establish a harmonized and structured reference list for research and public health decision-making.

## Objectives

* Aggregate pathogen prioritization lists from leading public health and research organizations.
* Provide a unified reference with consistent taxonomy and annotation.
* Support pathogen surveillance, pandemic preparedness, and biosecurity efforts.
* Make prioritization data **machine-readable**, as many official lists are only available in formats (PDFs or websites) that are not readily accessible for automated analysis.

## Methodology

### Taxonomic standardization

* Pathogens are named using scientific **species names** whenever possible.
* When species-level resolution is not feasible, the **genus name** is used.
* Viral naming follows **ICTV (International Committee on Taxonomy of Viruses)** recommendations.
* Additional or common names are listed under the `Also known as` field.

### Data sources

The prioritization list integrates information from international and national agencies, using their publicly available priority lists. Each source is referenced below:

| Organization                                          | Acronym   | Link                                            | List Name                                                           | Source URLs                                                                                                                                                                                                                                                          |
| ----------------------------------------------------- | --------- | ----------------------------------------------- | ------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| National Institute of Allergy and Infectious Diseases | NIAID     | [niaid.nih.gov](https://www.niaid.nih.gov/)     | NIAID Biodefense Pathogens, Research, Wiriya's document             | [1](https://www.niaid.nih.gov/research/niaid-biodefense-pathogens), [2](https://www.niaid.nih.gov/research-areas), [3](https://docs.google.com/document/d/1RY7u4TiTzBV_1T7Rthpn2gdU5pBwPnOc/edit)                                                                    |
| European Centre for Disease Prevention and Control    | ECDC      | [ecdc.europa.eu](https://www.ecdc.europa.eu/en) | Disease-based list                                                  | [Link](https://www.ecdc.europa.eu/en/all-topics)                                                                                                                                                                                                                     |
| World Health Organization                             | WHO       | [who.int](https://www.who.int/)                 | WHO priority pathogen lists (scientific framework, bacteria, fungi) | [1](https://www.who.int/publications/m/item/pathogens-prioritization-a-scientific-framework-for-epidemic-and-pandemic-research-preparedness), [2](https://www.who.int/publications/i/item/9789240093461), [3](https://www.who.int/publications/i/item/9789240060241) |
| Africa Centres for Disease Control and Prevention     | AFRICACDC | [africacdc.org](https://africacdc.org/)         | Epidemic-prone diseases prioritization                              | [Link](https://africacdc.org/download/risk-ranking-and-prioritization-of-epidemic-prone-diseases/)                                                                                                                                                                   |
| Centers for Disease Control and Prevention (USA)      | CDC       | [cdc.gov](https://www.cdc.gov/)                 | AMR Threats Report 2021-2022                                        | [Link](https://www.cdc.gov/antimicrobial-resistance/media/pdfs/antimicrobial-resistance-threats-update-2022-508.pdf)                                                                                                                                                 |

> You can consult the [live Google Sheet](https://docs.google.com/spreadsheets/d/1nrG329whDaeVv8BpocWUuSc-lgv-TJVf6RIxW3Bd8jg/edit?usp=sharing) used for this repository.

## Priority Type Classification

Each pathogen is categorized into one or more "priority types", based on its inclusion in the above lists. These allow grouping pathogens by relevance across thematic areas.

**Unique priority types used:**

```
- Pandemic preparedness
- Biodefense/Bioterrorism
- vaccine-preventable
- STI
- AMR/Nosocomial infection
- Animal disease
- Neglected Tropical Diseases
- Other
```

> Pathogens may belong to multiple categories simultaneously.

## Outputs

* `patogenos_prioritarios.csv`: Tabular data extracted from the source.
* `patogenos_prioritarios.json`: Structured version with:

  * Harmonized taxonomy and metadata
  * `Priority type` and `prioritized_by`
  * Appearance counters and taxonomy ID

## Updating

Run the script `generate_pathogens_list.py` to pull the latest data and regenerate the files from the live Google Sheet.

### Example usage

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Run the script:

```bash
python generate_pathogens_list.py
```

This will generate updated `.csv` and `.json` files based on the latest content in the linked Google Sheet.
