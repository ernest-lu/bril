import csv
import sys
from collections import defaultdict
from statistics import geometric_mean

STATS = {
    "geomean": geometric_mean,
    "min": min,
    "max": max,
}


def normalize():
    # Read input CSV.
    reader = csv.DictReader(sys.stdin)
    in_data = list(reader)

    baseline_rows = [
        row for row in in_data if row["run"] == "baseline" and row["result"].isdigit()
    ]
    # Get normalization baselines.
    baselines = {row["benchmark"]: int(row["result"]) for row in baseline_rows}

    # Write output CSV back out.
    writer = csv.DictWriter(sys.stdout, reader.fieldnames)
    writer.writeheader()
    ratios = defaultdict(list)
    for row in in_data:
        if row["result"].isdigit():
            ratio = int(row["result"]) / baselines[row["benchmark"]]
            ratios[row["run"]].append(ratio)
            row["result"] = ratio
            writer.writerow(row)

    # Print stats.
    for run, rs in ratios.items():
        for name, func in STATS.items():
            print(
                "{}({}) = {:.2f}".format(name, run, func(rs)),
                file=sys.stderr,
            )


if __name__ == "__main__":
    normalize()
