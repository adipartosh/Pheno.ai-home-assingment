# DNA_ETL
**Authors:** Adi Partosh

## Overview
A small ETL in Python that merges a participant’s DNA test data from two files:

- `{uuid}_dna.json` - test & individual metadata  
- `{uuid}_dna.txt` - DNA sequences (one per line)

The tool validates the JSON, extracts features from the TXT, and writes one merged output JSON per participant.

## Main Modules
- **ETL.py** - Orchestrates the run: parse args, validate paths, time the run, merge, write.  
- **json_processor.py** - Removes sensitive fields (`_`-prefixed), enforces string-length `< 64`, checks age `≥ 40`, and that dates are within **2014–2024** (inclusive).  
- **txt_processor.py** - Per-sequence GC% and codon frequencies; global most common codon; Longest Common Substring (LCS) across sequence pairs.  
- **valid_input.py** - Verifies the runner JSON, filesystem layout, and matching `{uuid}_dna` pair.  
- **tests/** - Optional pytest suite.

## Data Model

### Runner Input (`input.json`)
```json
{
  "context_path": "PATH/TO/FOLDER/with/participant/files",
  "results_path": "PATH/TO/OUTPUT/FOLDER"
}
```
`context_path` must contain **exactly two files** sharing the same UUID stem: `{uuid}_dna.json` and `{uuid}_dna.txt` (no other files).

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
- **GC content** - percent of G or C in a sequence (two decimals).  
- **Codon frequency** - non-overlapping triplets from the start; drop trailing 1–2 bases.  
- **Most common codon** - aggregated across all sequences; ties → lexicographic.  
- **LCS** - longest common substring among any pair of sequences. Output includes: value, sequences (1-based indices), and length. Tie-breaks: longer > lexicographically smaller > lowest index pair.

## Validation Rules (JSON)
- Drop any key that starts with `_` (recursive).  
- All scalar strings must be `< 64` characters.  
- `date_of_birth` ⇒ age `≥ 40` at run time.  
- All ISO dates (`YYYY-MM-DD`) must be within **2014–2024** (inclusive).

---

## How to Run
Python 3.10+, optional: pytest for tests.

From project root:
```bash
python ETL.py path/to/input.json
# e.g.
python ETL.py data/input_exmpl.json
```
The output file `<uuid>.json` will be written to `results_path` (overwrites if exists).

---

## macOS (zsh/bash) - exact steps
These set mac-friendly paths and run the package correctly (module mode).

```bash
# 0) repo root
cd Pheno.ai-home-assingment

# 1) venv
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip

# 2) create/update input file with POSIX/relative paths (no Windows C:\)
cat > data/input_exmpl.json << 'JSON'
{
  "context_path": "data/input_exmpl_folder",
  "results_path": "results"
}
JSON

# 3) context must have EXACTLY two files (json+txt) with the same UUID
rm -f data/input_exmpl_folder/.DS_Store
mkdir -p results   # results must be OUTSIDE the context_path

# 4) run as a module (do not run the file directly)
export PYTHONPATH="$PWD/src"
python -m dna_etl.ETL data/input_exmpl.json
# one-liner alternative:
# PYTHONPATH=src python -m dna_etl.ETL data/input_exmpl.json
```

---

## Windows (PowerShell) — exact steps
```powershell
# 0) repo root
cd Pheno.ai-home-assingment

# 1) venv
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip

# 2) create/update input file with Windows/relative paths (not C:\ hardcoded)
@'
{
  "context_path": "data/input_exmpl_folder",
  "results_path": "results"
}
'@ | Set-Content -Encoding UTF8 data\input_exmpl.json

# 3) context must have EXACTLY two files (json+txt) with the same UUID
Get-ChildItem -Force data\input_exmpl_folder
Remove-Item data\input_exmpl_folder\Thumbs.db -ErrorAction SilentlyContinue
Remove-Item data\input_exmpl_folder\desktop.ini -ErrorAction SilentlyContinue
New-Item -ItemType Directory results -Force | Out-Null  # results OUTSIDE the context

# 4) run as a module (do not run the file directly)
$env:PYTHONPATH = "src"
python -m dna_etl.ETL data\input_exmpl.json
```

---

## Exit Codes
- `0` - success  
- `2` - invalid runner input / bad paths  
- `3` - missing `{uuid}_dna.json` / `{uuid}_dna.txt`  
- `4` - data validation failed  
- `5` - unexpected runtime error

---

## Run tests (pytest)

### macOS / Linux
```bash
python -m pip install -U pytest
export PYTHONPATH="$PWD/src"
python -m pytest -q
```

### Windows (PowerShell)
```powershell
python -m pip install -U pytest
$env:PYTHONPATH = "src"
python -m pytest -q
```

---

## Troubleshooting

### macOS
- **`'context_path' must be an existing directory.`**  
  Update `data/input_exmpl.json` to use existing POSIX/relative paths as shown above.
- **`context_path must contain exactly two files: one .json and one .txt (no other files).`**  
  Clean the folder (no subfolders, no `.DS_Store`). Keep only `{uuid}_dna.json` and `{uuid}_dna.txt`.  
  Ensure `results` lives **outside** the context folder (e.g., `results/` at repo root).
- **`ModuleNotFoundError: dna_etl`**  
  You are not at the repo root or forgot `PYTHONPATH`. Run:
  ```bash
  export PYTHONPATH="$PWD/src"
  python -m dna_etl.ETL data/input_exmpl.json
  ```
- **`attempted relative import with no known parent package`**  
  You ran a file directly. Always run in **module mode**:
  ```bash
  python -m dna_etl.ETL data/input_exmpl.json
  ```

### Windows
- **`ModuleNotFoundError: dna_etl`**  
  Set `PYTHONPATH` and run in module mode:
  ```powershell
  $env:PYTHONPATH = "src"
  python -m dna_etl.ETL data\input_exmpl.json
  ```
- **`'context_path' must be an existing directory`**  
  Fix `data\input_exmpl.json` like in the steps above.
- **`context_path must contain exactly two files: one .json and one .txt (no other files).`**  
  Remove extras (`Thumbs.db`, `desktop.ini`, subfolders). Keep only `{uuid}_dna.json` and `{uuid}_dna.txt`.  
  Ensure `results\` is **outside** `data\input_exmpl_folder`.
- **Execution policy blocks venv activation**  
  ```powershell
  Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
  .\.venv\Scripts\Activate.ps1
  ```
