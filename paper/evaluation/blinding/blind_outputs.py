"""
Blinding script for third-party evaluation (Protocol v1 §8).
Strips metadata headers and randomizes output order.
No external dependencies — uses only Python standard library.

Usage:
    python blind_outputs.py --seed 42 --calibration
"""

import argparse
import json
import os
import random
import sys
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
FULLPAPER_DIR = REPO_ROOT / "docs" / "examples" / "fullpaper"
PHASE1_DIR = REPO_ROOT / "docs" / "examples"
BLINDED_DIR = Path(__file__).resolve().parent.parent / "blinded"
CALIBRATION_DIR = Path(__file__).resolve().parent.parent / "calibration"
BLINDING_DIR = Path(__file__).resolve().parent

# ── Phase 2 files (40) ────────────────────────────────────────────

CONDITIONS = ["conventional", "paper-format", "pdd-template", "checklist"]
CASE_STUDIES = ["cs1", "cs2"]
RUNS = range(1, 6)


def list_phase2_files():
    """List all 40 Phase 2 output files in canonical order."""
    files = []
    for cs in CASE_STUDIES:
        for cond in CONDITIONS:
            for run in RUNS:
                fname = f"{cs}-{cond}-run{run}.md"
                fpath = FULLPAPER_DIR / fname
                if not fpath.exists():
                    print(f"ERROR: Missing file: {fpath}", file=sys.stderr)
                    sys.exit(1)
                files.append(fpath)
    return files


# ── Calibration files (Phase 1, 5 selected) ──────────────────────

# A×1, B×2, C×2 — quality level spread across CS1 and CS2
CALIBRATION_SOURCES = [
    "cs2-conventional.md",     # A (low quality)
    "cs1-paper-format.md",     # B (medium)
    "cs2-paper-format.md",     # B (medium)
    "cs1-pdd-template.md",     # C (high quality)
    "cs2-pdd-template.md",     # C (high quality)
]


def list_calibration_files():
    """List selected Phase 1 files for calibration."""
    files = []
    for fname in CALIBRATION_SOURCES:
        fpath = PHASE1_DIR / fname
        if not fpath.exists():
            print(f"ERROR: Missing calibration file: {fpath}", file=sys.stderr)
            sys.exit(1)
        files.append(fpath)
    return files


# ── Header stripping ──────────────────────────────────────────────

def strip_header(content):
    """Remove metadata header (title line through first '---' separator).

    The header format is:
        # Title line
        > **metadata**: value
        > ...
        ---
        [body starts here]

    Returns the body content after the first '---' separator.
    """
    lines = content.split("\n")
    separator_idx = None

    for i, line in enumerate(lines):
        # Skip empty lines at the start
        stripped = line.strip()
        if stripped == "---":
            separator_idx = i
            break

    if separator_idx is None:
        # No separator found — return content as-is with a warning
        print("WARNING: No --- separator found in file", file=sys.stderr)
        return content

    # Return everything after the separator, stripping leading blank lines
    body_lines = lines[separator_idx + 1:]
    # Strip leading empty lines
    while body_lines and body_lines[0].strip() == "":
        body_lines.pop(0)

    return "\n".join(body_lines)


# ── Main blinding logic ──────────────────────────────────────────

def blind_main(seed):
    """Blind 40 Phase 2 outputs."""
    files = list_phase2_files()
    assert len(files) == 40, f"Expected 40 files, got {len(files)}"

    # Shuffle with fixed seed
    rng = random.Random(seed)
    indices = list(range(len(files)))
    rng.shuffle(indices)

    # Create output directory
    BLINDED_DIR.mkdir(parents=True, exist_ok=True)

    # Generate mapping and blinded files
    mapping = {}
    for new_idx, orig_idx in enumerate(indices):
        output_num = new_idx + 1
        output_id = f"output-{output_num:03d}"
        orig_file = files[orig_idx]

        content = orig_file.read_text(encoding="utf-8")
        body = strip_header(content)

        blinded_content = f"# Output #{output_num:03d}\n\n{body}"

        out_path = BLINDED_DIR / f"{output_id}.md"
        out_path.write_text(blinded_content, encoding="utf-8")

        mapping[output_id] = orig_file.name

    # Write mapping (secret)
    mapping_path = BLINDING_DIR / "mapping-secret.json"
    mapping_path.write_text(
        json.dumps(mapping, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    # Write seed record
    seed_record = (
        f"# Seed Record — Main Blinding\n\n"
        f"- **Seed**: {seed}\n"
        f"- **Method**: `random.Random({seed}).shuffle()`\n"
        f"- **Input**: 40 Phase 2 files in canonical order "
        f"(cs{{1,2}}-{{condition}}-run{{1-5}})\n"
        f"- **Output**: `blinded/output-{{001..040}}.md`\n"
        f"- **Mapping**: `blinding/mapping-secret.json` (git-ignored)\n"
    )
    seed_record_path = BLINDING_DIR / "seed-record.md"
    seed_record_path.write_text(seed_record, encoding="utf-8")

    print(f"Generated {len(mapping)} blinded outputs in {BLINDED_DIR}")
    print(f"Mapping saved to {mapping_path}")
    print(f"Seed record saved to {seed_record_path}")


def blind_calibration(seed):
    """Blind 5 calibration outputs from Phase 1."""
    files = list_calibration_files()
    assert len(files) == 5, f"Expected 5 calibration files, got {len(files)}"

    # Shuffle with separate seed
    rng = random.Random(seed)
    indices = list(range(len(files)))
    rng.shuffle(indices)

    # Create output directory
    CALIBRATION_DIR.mkdir(parents=True, exist_ok=True)

    # Generate mapping and blinded files
    mapping = {}
    for new_idx, orig_idx in enumerate(indices):
        output_num = new_idx + 1
        cal_id = f"calibration-{output_num:03d}"
        orig_file = files[orig_idx]

        content = orig_file.read_text(encoding="utf-8")
        body = strip_header(content)

        blinded_content = f"# Calibration #{output_num:03d}\n\n{body}"

        out_path = CALIBRATION_DIR / f"{cal_id}.md"
        out_path.write_text(blinded_content, encoding="utf-8")

        mapping[cal_id] = orig_file.name

    # Write calibration mapping (secret)
    mapping_path = CALIBRATION_DIR / "mapping-secret.json"
    mapping_path.write_text(
        json.dumps(mapping, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(f"Generated {len(mapping)} calibration outputs in {CALIBRATION_DIR}")
    print(f"Calibration mapping saved to {mapping_path}")


# ── CLI ───────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Blind LLM outputs for third-party evaluation"
    )
    parser.add_argument(
        "--seed", type=int, default=42,
        help="Random seed for main blinding (default: 42)"
    )
    parser.add_argument(
        "--calibration", action="store_true",
        help="Also generate calibration outputs (seed=142)"
    )
    args = parser.parse_args()

    blind_main(args.seed)

    if args.calibration:
        blind_calibration(seed=142)

    print("\nDone.")


if __name__ == "__main__":
    main()
