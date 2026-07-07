"""
Krippendorff's α calculator for human coding reliability
投资者情感论文 — Expression Typology (5 categories, nominal)

Usage:
    python krippendorff_alpha.py <path_to_coded_workbook.xlsx>

Requirements:
    pip install krippendorff pandas openpyxl
"""

import sys
import pandas as pd
import krippendorff


CODE_MAP = {
    "Information sharing": 1,
    "Policy evaluation": 2,
    "Market expectation": 3,
    "Emotional venting": 4,
    "Other/Mixed": 5,
}


def main():
    if len(sys.argv) < 2:
        print("Usage: python krippendorff_alpha.py <workbook.xlsx>")
        sys.exit(1)

    path = sys.argv[1]
    df = pd.read_excel(path, sheet_name="Coding")

    # Filter rows where both coders have filled values
    mask = df["Coder A"].notna() & df["Coder B"].notna()
    coded = df[mask].copy()
    n_total = len(coded)

    if n_total == 0:
        print("❌ No double-coded rows found. Fill columns E and F first.")
        sys.exit(1)

    # Map labels to numeric codes
    coder_a = coded["Coder A"].map(CODE_MAP).values
    coder_b = coded["Coder B"].map(CODE_MAP).values

    # Check for unmapped values
    a_unmapped = coded.loc[~coded["Coder A"].isin(CODE_MAP), "Coder A"].unique()
    b_unmapped = coded.loc[~coded["Coder B"].isin(CODE_MAP), "Coder B"].unique()
    if len(a_unmapped) > 0:
        print(f"⚠️  Unmapped labels in Coder A: {a_unmapped}")
    if len(b_unmapped) > 0:
        print(f"⚠️  Unmapped labels in Coder B: {b_unmapped}")

    # Krippendorff's α (nominal)
    alpha = krippendorff.alpha(
        reliability_values=[coder_a, coder_b],
        level_of_measurement="nominal",
    )

    n_agree = (coder_a == coder_b).sum()
    pct_agree = n_agree / n_total

    # Per-category agreement
    print(f"{'='*50}")
    print(f"  HUMAN CODING RELIABILITY REPORT")
    print(f"{'='*50}")
    print(f"  Double-coded rows:   {n_total}")
    print(f"  Agreements:          {n_agree}")
    print(f"  Simple % agreement:  {pct_agree:.2%}")
    print(f"  Krippendorff's α:    {alpha:.3f}")
    print(f"  Target α ≥ 0.80:     {'✅ PASS' if alpha >= 0.80 else '❌ BELOW THRESHOLD'}")
    print(f"  Minimum α ≥ 0.667:   {'✅ PASS (exploratory)' if alpha >= 0.667 else '❌ UNACCEPTABLE'}")
    print(f"{'='*50}")

    # Per-category breakdown
    print(f"\n📊 Per-category agreement:")
    for label, code in CODE_MAP.items():
        a_this = (coder_a == code)
        b_this = (coder_b == code)
        both = a_this & b_this
        either = a_this | b_this
        if either.sum() > 0:
            cat_agree = both.sum() / either.sum()
            a_count = a_this.sum()
            b_count = b_this.sum()
            print(f"  {label:25s}  A={a_count:3d}  B={b_count:3d}  agreement={cat_agree:.1%}")

    # Final distribution (using G column if available, else Coder A)
    if "Final (adjudicated)" in coded.columns:
        g_mask = coded["Final (adjudicated)"].notna()
        final_series = coded["Coder A"].copy()
        final_series.loc[g_mask] = coded.loc[g_mask, "Final (adjudicated)"]
    else:
        final_series = coded["Coder A"]

    print(f"\n📊 Final distribution (using adjudicated labels where available):")
    dist = final_series.value_counts()
    for label, count in dist.items():
        print(f"  {label:25s}  {count:3d}  ({count/n_total:.1%})")

    # Per-stage distribution
    print(f"\n📊 Per-stage distribution:")
    for stage in sorted(coded["Stage"].unique()):
        stage_data = coded[coded["Stage"] == stage]
        stage_final = stage_data["Coder A"].copy()
        g_s = stage_data["Final (adjudicated)"].notna()
        stage_final.loc[g_s] = stage_data.loc[g_s, "Final (adjudicated)"]
        dist_s = stage_final.value_counts()
        print(f"  Stage {int(stage)} (n={len(stage_data)}):")
        for label, count in dist_s.items():
            print(f"    {label:25s}  {count:2d}")


if __name__ == "__main__":
    main()
