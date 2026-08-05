import json
import random
import sys
from typing import Dict, Any

import pandas as pd
import numpy as np

# ==========================================================
# CONFIGURATION & INITIALIZATION
# ==========================================================
SEED = 42
random.seed(SEED)
np.random.seed(SEED)

JSON_FILE = 'master_darkstores_v1.json'
OUTPUT_FILE = 'darkstores.csv'


def load_config(filepath: str) -> Dict[str, Any]:
    """Loads and returns the JSON configuration file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"CRITICAL ERROR: Configuration file '{filepath}' not found.")
    except json.JSONDecodeError as e:
        raise ValueError(f"CRITICAL ERROR: Configuration file '{filepath}' is malformed JSON. Details: {e}")


def generate_darkstores(config: Dict[str, Any]) -> pd.DataFrame:
    """Generates the dark stores dataset based entirely on the JSON config."""
    
    # 1. Extract foundational configurations
    try:
        target_stores = config['metadata']['target_dark_stores']
        city = config['metadata']['city']
        areas = config['areas']
        store_types = config['store_types']
        gen_rules = config['generation_rules']
    except KeyError as e:
        raise KeyError(f"CRITICAL ERROR: Missing required key in JSON configuration: {e}")

    # Check that we have exactly the required number of areas available
    if len(areas) != target_stores:
        raise ValueError(f"CRITICAL ERROR: Expected {target_stores} areas in JSON, found {len(areas)}.")

    # 2. Define exact deterministic distributions for exactly 12 stores
    # Ensure exact Store Type distribution: Large = 3, Medium = 6, Micro = 3
    store_types_list = (['Large'] * 3) + (['Medium'] * 6) + (['Micro'] * 3)
    random.shuffle(store_types_list)
    
    # Ensure exact Status distribution: Active = 10, Maintenance = 1, Under Expansion = 1
    status_list = (['Active'] * 10) + (['Maintenance'] * 1) + (['Under Expansion'] * 1)
    random.shuffle(status_list)

    stores_data = []

    # 3. Deterministically generate each store row
    for index, area_obj in enumerate(areas, start=1):
        # Read format generation rules dynamically from JSON
        store_id = gen_rules['store_id_format'].format(index=index)
        area_name = area_obj['name']
        pincode = area_obj['pincode']
        store_name = gen_rules['store_name_format'].replace('{Area}', area_name)
        
        # Select type and status from exact shuffled lists
        store_type = store_types_list[index - 1]
        current_status = status_list[index - 1]
        
        # Extract constraints for the assigned store type
        type_constraints = store_types[store_type]
        
        # Service Radius (1 decimal place)
        radius_min = type_constraints['service_radius_km']['min']
        radius_max = type_constraints['service_radius_km']['max']
        service_radius = round(random.uniform(radius_min, radius_max), 1)
        
        # Storage Capacity (Integer)
        storage_min = type_constraints['storage_capacity']['min']
        storage_max = type_constraints['storage_capacity']['max']
        storage_capacity = random.randint(storage_min, storage_max)
        
        # Daily Order Capacity (Integer)
        order_min = type_constraints['daily_order_capacity']['min']
        order_max = type_constraints['daily_order_capacity']['max']
        daily_order_capacity = random.randint(order_min, order_max)
        
        # Temperature Control (Boolean mapped directly from JSON)
        temperature_control = type_constraints['temperature_control']
        
        # Append to dataset
        stores_data.append({
            "Store_ID": store_id,
            "Store_Name": store_name,
            "City": city,
            "Area": area_name,
            "Pincode": pincode,
            "Store_Type": store_type,
            "Service_Radius_KM": service_radius,
            "Storage_Capacity": storage_capacity,
            "Temperature_Control": temperature_control,
            "Daily_Order_Capacity": daily_order_capacity,
            "Current_Status": current_status
        })
        
    # Build dataframe and strictly order columns using JSON final_columns config
    df = pd.DataFrame(stores_data)
    if 'final_columns' in gen_rules:
        df = df[gen_rules['final_columns']]
        
    return df


def validate_dataset(df: pd.DataFrame, config: Dict[str, Any]) -> None:
    """Validates the generated dataframe against strict data quality and business rules."""
    
    target_stores = config['metadata']['target_dark_stores']
    
    # Check Row Count
    if len(df) != target_stores:
        raise ValueError(f"VALIDATION FAILED: Expected {target_stores} stores, generated {len(df)}.")
        
    # Check Missing Values
    if df.isnull().values.any():
        raise ValueError("VALIDATION FAILED: Null values detected in the generated dataset.")
        
    # Check Unique Constraints
    for col in ['Store_ID', 'Store_Name', 'Area', 'Pincode']:
        if df[col].duplicated().any():
            raise ValueError(f"VALIDATION FAILED: Duplicates found in unique column '{col}'.")
            
    # Validate Store Types & Statuses
    valid_types = list(config['store_types'].keys())
    valid_statuses = list(config['store_status'].keys())
    
    if not df['Store_Type'].isin(valid_types).all():
        raise ValueError("VALIDATION FAILED: Invalid Store_Type found.")
        
    if not df['Current_Status'].isin(valid_statuses).all():
        raise ValueError("VALIDATION FAILED: Invalid Current_Status found.")
        
    # Validate Ranges & Constraints Contextually
    for _, row in df.iterrows():
        store_type = row['Store_Type']
        limits = config['store_types'][store_type]
        
        if not (limits['service_radius_km']['min'] <= row['Service_Radius_KM'] <= limits['service_radius_km']['max']):
            raise ValueError(f"VALIDATION FAILED: Service_Radius_KM out of bounds for {row['Store_ID']}.")
            
        if not (limits['storage_capacity']['min'] <= row['Storage_Capacity'] <= limits['storage_capacity']['max']):
            raise ValueError(f"VALIDATION FAILED: Storage_Capacity out of bounds for {row['Store_ID']}.")
            
        if not (limits['daily_order_capacity']['min'] <= row['Daily_Order_Capacity'] <= limits['daily_order_capacity']['max']):
            raise ValueError(f"VALIDATION FAILED: Daily_Order_Capacity out of bounds for {row['Store_ID']}.")
            
        if row['Temperature_Control'] != limits['temperature_control']:
            raise ValueError(f"VALIDATION FAILED: Temperature_Control mismatch for {row['Store_ID']}.")


def print_summary(df: pd.DataFrame) -> None:
    """Prints a detailed statistical summary of the generated dark stores."""
    print("=" * 50)
    print(" DARK STORES GENERATION SUMMARY")
    print("=" * 50)
    print(f"Total Stores                  : {len(df)}")
    
    print("\nStore Type Distribution:")
    print(df['Store_Type'].value_counts(normalize=True).mul(100).round(1).astype(str) + '%')
    
    print("\nStatus Distribution:")
    print(df['Current_Status'].value_counts(normalize=True).mul(100).round(1).astype(str) + '%')
    
    print("\nAverages:")
    print(f"Average Storage Capacity      : {df['Storage_Capacity'].mean():.0f} units")
    print(f"Average Daily Order Capacity  : {df['Daily_Order_Capacity'].mean():.0f} orders")
    print(f"Average Service Radius        : {df['Service_Radius_KM'].mean():.1f} KM")
    
    print("\nData Quality:")
    print(f"Null Count                    : {df.isnull().sum().sum()}")
    print(f"Duplicate Count (Store_ID)    : {df.duplicated(subset=['Store_ID']).sum()}")
    print("=" * 50)


def main():
    try:
        # Load constraints
        config = load_config(JSON_FILE)
        
        # Generate data deterministically
        df_stores = generate_darkstores(config)
        
        # Enforce validation guards
        validate_dataset(df_stores, config)
        
        # Output strictly structured CSV
        df_stores.to_csv(OUTPUT_FILE, index=False, encoding='utf-8')
        
        # Logging
        print(f"Successfully generated {len(df_stores)} records. Exported to '{OUTPUT_FILE}'.\n")
        print_summary(df_stores)
        
    except Exception as e:
        print(f"\n{str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()