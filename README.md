# README.md

# DNA\_ETL

## Authors

Adi Partosh

## Overview

A small ETL in Python that merges a participant’s DNA test data from two files:

* `{uuid}_dna.json` — test & individual metadata
* `{uuid}_dna.txt` — DNA sequences (one per line)

The tool validates the JSON, extracts features from the TXT, and writes **one** merged output JSON per participant.

## Main Modules

* **ETL.py** – Orchestrates the run: parse args, validate paths, time the run, merge, write.
* **json\_processor.py** – Removes sensitive fields (`_`-prefixed), enforces string-length < 64, checks **age ≥ 40**, and that dates are within **2014–2024** (inclusive).
* **txt\_processor.py** – Per-sequence GC% and codon frequencies; global most-common codon; **Longest Common Substring (LCS)** across sequence pairs.
* **valid\_input.py** – Verifies the runner JSON, filesystem layout, and matching `{uuid}_dna` pair.
* **tests/** – Optional pytest suite.

## Data Model

### Runner Input (`input.json`)

```json
{
  "context_path": "PATH/TO/FOLDER/with/participant/files",
  "results_path": "PATH/TO/OUTPUT/FOLDER"
}
```

* `context_path` must contain **exactly two files** sharing the same UUID stem:
  `{uuid}_dna.json` and `{uuid}_dna.txt`.

### Output (single file)

Written to `results_path` as `<uuid>.json`:

```json
{
  "metadata": {
    "start_at": "UTC ISO",
    "end_at": "UTC ISO",
    "context_path": "...",
    "results_path": "..."
  },
  "results": [
    {
      "participant": { "_id": "<uuid>" },
      "txt": { ... },   // features extracted from TXT
      "JSON": { ... }   // cleaned+validated JSON
    }
  ]
}
```

## Algorithms (TXT)

* **GC content** – Percent of `G` or `C` in a sequence (two decimals).
* **Codon frequency** – Non-overlapping triplets from the **start**; drop trailing 1–2 bases.
* **Most common codon** – Aggregated across all sequences; **tie-break lexicographically**.
* **LCS** – Longest common **substring** among any pair of sequences.
  Output includes: `value`, `sequences` (1-based indices), and `length`.
  Tie-breaks: longer > lexicographically smaller > lowest index pair.

## Validation Rules (JSON)

* Drop any key that **starts with `_`** (recursive).
* All scalar strings must be **< 64** characters.
* `date_of_birth` ⇒ **age ≥ 40** at run time.
* All ISO dates (`YYYY-MM-DD`) must be within **2014–2024** (inclusive).

## How to Run

1. **Python 3.10+**, optional: `pytest` for tests.
2. (Recommended) Create venv and activate.
3. From project root:

   ```bash
   python ETL.py path/to/input.json
   # e.g.
   python ETL.py input_exmpl.json
   ```
4. The output file `<uuid>.json` will be written to `results_path` (overwrites if exists).

## Exit Codes

* `0` - success
* `2` - invalid runner input / bad paths
* `3` - missing `{uuid}_dna.json` / `{uuid}_dna.txt`
* `4` - data validation failed (JSON rules)
* `5` - unexpected runtime error

## Example Files

* `input_exmpl.json` - runner config
* `IND123456_dna.json` - example metadata
* `IND123456_dna.txt` - example sequences
