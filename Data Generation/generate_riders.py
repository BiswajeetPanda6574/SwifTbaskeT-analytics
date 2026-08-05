"""
generate_riders.py

QuickCommerce BI — Bengaluru — Simulation Period 2025-04-01 to 2025-09-30

Deterministic, JSON-driven synthetic rider master data generator.

Inputs (read-only, single source of truth):
    - master_riders_v1.json  : all business rules (status distribution,
                                rating rules, delivery-time rules, store
                                capacity ranges, validation rules, etc.)
    - darkstores.csv          : Store_ID / Store_Type master data

Output:
    - riders.csv : Rider_ID, Rider_Name, Store_ID, Rider_Status,
                    Average_Rating, Average_Delivery_Time_Min

No business rule is hardcoded. Rider counts, status probabilities, rating
distribution, and delivery-time distribution are all derived dynamically
from master_riders_v1.json at runtime. Running this script multiple times
against the same inputs always produces identical output (random.seed(42),
numpy.random.seed(42)).

Usage:
    python generate_riders.py
"""

from __future__ import annotations

import json
import random
import re
from pathlib import Path
from typing import Any, Dict, List, Set

import numpy as np
import pandas as pd

from resources.indian_names import MALE_FIRST_NAMES, FEMALE_FIRST_NAMES, SURNAMES

# --------------------------------------------------------------------------
# Constants / deterministic seeding
# --------------------------------------------------------------------------

RANDOM_SEED: int = 42
DEFAULT_JSON_PATH: str = "master_riders_v1.json"
DEFAULT_CSV_PATH: str = "darkstores.csv"
OUTPUT_CSV_PATH: str = "riders.csv"


# --------------------------------------------------------------------------
# Input loading & validation
# --------------------------------------------------------------------------

def load_master_config(json_path: str) -> Dict[str, Any]:
    """Load and structurally validate the master business-rules JSON."""
    path = Path(json_path)
    if not path.exists():
        raise FileNotFoundError(f"Required config file not found: {json_path}")
    try:
        with path.open("r", encoding="utf-8") as f:
            config: Dict[str, Any] = json.load(f)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Failed to parse {json_path}: {exc}") from exc

    required_top_keys = [
        "rider_status", "rating_rules", "delivery_time_rules",
        "store_assignment_rules", "validation_rules",
    ]
    missing = [k for k in required_top_keys if k not in config]
    if missing:
        raise ValueError(f"{json_path} is missing required keys: {missing}")
    return config


def load_darkstores(csv_path: str) -> pd.DataFrame:
    """Load and validate dark store master data."""
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"Required config file not found: {csv_path}")
    df = pd.read_csv(path)

    required_cols = {"Store_ID", "Store_Type"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"{csv_path} is missing required columns: {missing}")
    if df["Store_ID"].isnull().any() or df["Store_Type"].isnull().any():
        raise ValueError(f"{csv_path} contains NULL Store_ID or Store_Type values.")
    if df["Store_ID"].duplicated().any():
        raise ValueError(f"{csv_path} contains duplicate Store_ID values.")
    return df


def get_max_name_occurrence(config: Dict[str, Any]) -> int:
    """Dynamically parse the max name occurrence limit from JSON validation rules."""
    for rule in config.get("validation_rules", []):
        if rule.get("check") == "duplicate_name_limit":
            match = re.search(r'(\d+)', rule.get("condition", ""))
            if match:
                return int(match.group(1))
    return 3  # Fallback if pattern is not found


# --------------------------------------------------------------------------
# Rider count derivation (fully JSON-driven — no hardcoded totals/ranges)
# --------------------------------------------------------------------------

def compute_rider_counts_per_store(
    darkstores: pd.DataFrame, capacity_by_store_type: Dict[str, Dict[str, int]]
) -> Dict[str, int]:
    """
    Determine how many riders each store receives, using the min/max rider
    capacity range defined per Store_Type inside master_riders_v1.json.
    Counts are drawn deterministically from a uniform integer distribution
    within each store's [min_riders, max_riders] range.
    """
    counts: Dict[str, int] = {}
    for _, row in darkstores.iterrows():
        store_id, store_type = row["Store_ID"], row["Store_Type"]

        if store_type not in capacity_by_store_type:
            raise ValueError(
                f"Store_Type '{store_type}' for {store_id} has no capacity "
                f"range defined in master_riders_v1.json."
            )

        bounds = capacity_by_store_type[store_type]
        min_r, max_r = int(bounds["min_riders"]), int(bounds["max_riders"])
        if min_r > max_r:
            raise ValueError(f"Invalid capacity range for Store_Type '{store_type}'.")

        counts[store_id] = int(np.random.randint(min_r, max_r + 1))
    return counts


def build_store_sequence(rider_counts: Dict[str, int]) -> List[str]:
    """Expand {store_id: count} into a flat, ordered list of store ids (one per rider)."""
    sequence: List[str] = []
    for store_id, count in rider_counts.items():
        sequence.extend([store_id] * count)
    return sequence


def generate_rider_ids(count: int) -> List[str]:
    """Generate sequential, unique Rider_IDs: RID0001, RID0002, ..."""
    return [f"RID{str(i).zfill(4)}" for i in range(1, count + 1)]


# --------------------------------------------------------------------------
# Rider name generation
# --------------------------------------------------------------------------

def build_name_pool() -> List[str]:
    """
    Build a large, deterministically shuffled pool of realistic Indian full
    names (first name + surname), spanning common Karnataka / pan-India
    naming conventions and both male and female first names.
    """
    first_names = MALE_FIRST_NAMES + FEMALE_FIRST_NAMES
    combos = [f"{first} {last}" for first in first_names for last in SURNAMES]
    rng = random.Random(RANDOM_SEED)
    rng.shuffle(combos)
    return combos


def assign_rider_names(store_sequence: List[str], name_pool: List[str], max_name_occurrence: int) -> List[str]:
    """
    Assign a Rider_Name to each rider (riders represented positionally by
    the store they belong to, per store_sequence), enforcing:
      - dynamically fetched max_name_occurrence of any name dataset-wide
      - no duplicate Rider_Name + Store_ID combination
    """
    if not name_pool:
        raise ValueError("Name pool is empty; cannot assign rider names.")

    name_usage_count: Dict[str, int] = {name: 0 for name in name_pool}
    used_in_store: Dict[str, Set[str]] = {}
    assigned_names: List[str] = []

    for store_id in store_sequence:
        store_used = used_in_store.setdefault(store_id, set())
        chosen = None
        for candidate in name_pool:
            if name_usage_count[candidate] < max_name_occurrence and candidate not in store_used:
                chosen = candidate
                break

        if chosen is None:
            raise RuntimeError(
                "Name pool exhausted under duplicate-name constraints; "
                "expand MALE_FIRST_NAMES / FEMALE_FIRST_NAMES / SURNAMES."
            )

        name_usage_count[chosen] += 1
        store_used.add(chosen)
        assigned_names.append(chosen)

    return assigned_names


# --------------------------------------------------------------------------
# Status / rating / delivery-time generation (distribution-driven from JSON)
# --------------------------------------------------------------------------

def generate_rider_statuses(count: int, status_config: Dict[str, Any]) -> List[str]:
    """Assign Rider_Status per the allowed values & percentage distribution in JSON."""
    allowed = status_config["allowed_values"]
    dist_pct = status_config["distribution_percentage"]

    missing = [s for s in allowed if s not in dist_pct]
    if missing:
        raise ValueError(f"rider_status.distribution_percentage missing entries for: {missing}")

    probabilities = np.array([dist_pct[status] for status in allowed], dtype=float)
    if not np.isclose(probabilities.sum(), 100.0, atol=0.5):
        raise ValueError("rider_status.distribution_percentage must sum to ~100.")
    probabilities = probabilities / probabilities.sum()

    return list(np.random.choice(allowed, size=count, p=probabilities))


def generate_ranged_values(count: int, distribution: List[Dict[str, Any]]) -> np.ndarray:
    """
    Generate `count` float values drawn uniformly from the [low, high] ranges
    listed in `distribution`, weighted by each range's configured percentage
    share. Used for both Average_Rating and Average_Delivery_Time_Min.
    """
    ranges = [tuple(item["range"]) for item in distribution]
    percentages = np.array([item["percentage"] for item in distribution], dtype=float)

    if not np.isclose(percentages.sum(), 100.0, atol=0.5):
        raise ValueError(f"Distribution percentages must sum to ~100, got {percentages.sum()}.")
    probabilities = percentages / percentages.sum()

    range_choices = np.random.choice(len(ranges), size=count, p=probabilities)
    values = np.empty(count, dtype=float)
    for i, idx in enumerate(range_choices):
        low, high = ranges[idx]
        values[i] = np.random.uniform(low, high)
    return values


# --------------------------------------------------------------------------
# Validation (mirrors master_riders_v1.json -> validation_rules)
# --------------------------------------------------------------------------

def validate_riders(
    df: pd.DataFrame, config: Dict[str, Any], valid_store_ids: Set[str], max_name_occurrence: int
) -> None:
    """Run every validation check required by master_riders_v1.json before export."""

    if df.isnull().values.any():
        raise ValueError("Validation failed: NULL values present in riders dataset.")

    if df["Rider_ID"].duplicated().any():
        raise ValueError("Validation failed: duplicate Rider_ID found.")

    invalid_stores = set(df["Store_ID"]) - valid_store_ids
    if invalid_stores:
        raise ValueError(f"Validation failed: invalid Store_ID(s) found: {invalid_stores}")

    allowed_status = set(config["rider_status"]["allowed_values"])
    invalid_status = set(df["Rider_Status"]) - allowed_status
    if invalid_status:
        raise ValueError(f"Validation failed: invalid Rider_Status value(s): {invalid_status}")

    r_min, r_max = config["rating_rules"]["minimum"], config["rating_rules"]["maximum"]
    if not df["Average_Rating"].between(r_min, r_max).all():
        raise ValueError(f"Validation failed: Average_Rating outside [{r_min}, {r_max}].")

    d_min, d_max = config["delivery_time_rules"]["minimum"], config["delivery_time_rules"]["maximum"]
    if not df["Average_Delivery_Time_Min"].between(d_min, d_max).all():
        raise ValueError(f"Validation failed: Average_Delivery_Time_Min outside [{d_min}, {d_max}].")

    name_counts = df["Rider_Name"].value_counts()
    offenders = name_counts[name_counts > max_name_occurrence]
    if not offenders.empty:
        raise ValueError(
            f"Validation failed: Rider_Name exceeds max occurrence of "
            f"{max_name_occurrence}: {offenders.to_dict()}"
        )

    if df.duplicated(subset=["Rider_Name", "Store_ID"]).any():
        raise ValueError("Validation failed: duplicate Rider_Name + Store_ID combination found.")


# --------------------------------------------------------------------------
# Summary reporting
# --------------------------------------------------------------------------

def print_summary(df: pd.DataFrame, darkstores: pd.DataFrame) -> None:
    """Print the required generation summary to stdout."""
    merged = df.merge(darkstores[["Store_ID", "Store_Type"]], on="Store_ID", how="left")

    print("=" * 60)
    print("RIDER GENERATION SUMMARY")
    print("=" * 60)
    print(f"Total Riders: {len(df)}")

    print("\nRiders per Store:")
    print(df["Store_ID"].value_counts().sort_index().to_string())

    print("\nStore Type Distribution:")
    print(merged["Store_Type"].value_counts().to_string())
    
    print("\nAverage Riders per Store Type:")
    riders_per_store = df.groupby("Store_ID").size().reset_index(name="rider_count")
    store_type_counts = riders_per_store.merge(darkstores[["Store_ID", "Store_Type"]], on="Store_ID", how="left")
    avg_riders_per_type = store_type_counts.groupby("Store_Type")["rider_count"].mean().round(2)
    print(avg_riders_per_type.to_string())

    print("\nStatus Distribution:")
    status_pct = (df["Rider_Status"].value_counts(normalize=True) * 100).round(2)
    print(status_pct.to_string())

    print(f"\nAverage Rating: {df['Average_Rating'].mean():.2f}")
    print(f"Average Delivery Time (min): {df['Average_Delivery_Time_Min'].mean():.2f}")

    dup_names = df["Rider_Name"].value_counts()
    dup_names = dup_names[dup_names > 1]
    print(f"\nDuplicate Names (appearing more than once): {len(dup_names)}")

    print(f"Null Count: {int(df.isnull().sum().sum())}")
    dup_combo_count = int(df.duplicated(subset=["Rider_Name", "Store_ID"]).sum())
    print(f"Duplicate (Rider_Name + Store_ID) Count: {dup_combo_count}")
    print("=" * 60)


# --------------------------------------------------------------------------
# Orchestration
# --------------------------------------------------------------------------

def generate_riders(
    json_path: str = DEFAULT_JSON_PATH, csv_path: str = DEFAULT_CSV_PATH
) -> pd.DataFrame:
    """Build, validate, and return the full riders DataFrame."""
    random.seed(RANDOM_SEED)
    np.random.seed(RANDOM_SEED)

    config = load_master_config(json_path)
    darkstores = load_darkstores(csv_path)

    max_name_occurrence = get_max_name_occurrence(config)

    rider_counts = compute_rider_counts_per_store(
        darkstores, config["store_assignment_rules"]["capacity_by_store_type"]
    )
    store_sequence = build_store_sequence(rider_counts)
    total_riders = len(store_sequence)
    if total_riders == 0:
        raise ValueError("No riders were generated; check capacity_by_store_type ranges.")

    rider_ids = generate_rider_ids(total_riders)

    name_pool = build_name_pool()
    rider_names = assign_rider_names(store_sequence, name_pool, max_name_occurrence)

    rider_statuses = generate_rider_statuses(total_riders, config["rider_status"])

    ratings = generate_ranged_values(
        total_riders, config["rating_rules"]["distribution_logic"]["target_ranges"]
    )
    ratings = np.round(ratings, config["rating_rules"]["rounding_decimals"])

    delivery_times = generate_ranged_values(
        total_riders, config["delivery_time_rules"]["distribution_percentage"]
    )
    delivery_times = np.round(delivery_times, config["delivery_time_rules"]["rounding_decimals"])

    df = pd.DataFrame({
        "Rider_ID": rider_ids,
        "Rider_Name": rider_names,
        "Store_ID": store_sequence,
        "Rider_Status": rider_statuses,
        "Average_Rating": ratings,
        "Average_Delivery_Time_Min": delivery_times,
    })

    validate_riders(
        df, 
        config, 
        valid_store_ids=set(darkstores["Store_ID"]), 
        max_name_occurrence=max_name_occurrence
    )
    print_summary(df, darkstores)

    return df


def export_riders(df: pd.DataFrame, output_path: str = OUTPUT_CSV_PATH) -> None:
    """Export the validated riders DataFrame to UTF-8 CSV."""
    df.to_csv(output_path, index=False, encoding="utf-8")
    print(f"\nExported {len(df)} riders to '{output_path}'")


def main() -> None:
    riders_df = generate_riders()
    export_riders(riders_df)


if __name__ == "__main__":
    main()