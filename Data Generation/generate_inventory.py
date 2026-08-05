import json
import random
import re
import sys
from datetime import datetime, timedelta
from typing import Dict, Any, Tuple, List

import pandas as pd
import numpy as np

# ==========================================================
# CONFIGURATION & INITIALIZATION
# ==========================================================
SEED = 42
random.seed(SEED)
np.random.seed(SEED)

JSON_FILE = 'master_inventory_v1.json'
PRODUCTS_FILE = 'products.csv'
DARKSTORES_FILE = 'darkstores.csv'
OUTPUT_FILE = 'inventory.csv'

SIMULATION_BASELINE_DATE = datetime(2025, 4, 1)

# ==========================================================
# HELPER FUNCTIONS (JSON PARSERS)
# ==========================================================
def extract_percentage(text: str) -> float:
    """Extracts the first percentage value found in a string."""
    match = re.search(r'(\d+)%', text)
    if match:
        return float(match.group(1)) / 100.0
    return 0.0

def extract_percentage_range(text: str) -> Tuple[float, float]:
    """Extracts a percentage range like '55-65%' from a string."""
    match = re.search(r'(\d+)-(\d+)%', text)
    if match:
        return float(match.group(1)) / 100.0, float(match.group(2)) / 100.0
    return 0.0, 0.0

def build_velocity_map(velocity_mapping: Dict[str, List[str]]) -> Dict[str, str]:
    """Reverses the velocity mapping to map Category -> Velocity."""
    cat_to_velocity = {}
    for velocity, categories in velocity_mapping.items():
        for category in categories:
            cat_to_velocity[category] = velocity
    return cat_to_velocity

# ==========================================================
# CORE GENERATOR
# ==========================================================
def generate_inventory(config: Dict[str, Any], df_products: pd.DataFrame, df_stores: pd.DataFrame) -> pd.DataFrame:
    """Main generation logic combining Products, Stores, and JSON Rules."""
    
    # 1. Parse JSON Rules dynamically
    business_rules = {r['name']: r['logic'] for r in config['business_rules']}
    
    # Extract store assortment depths
    assortment_rule = business_rules.get("Assortment Depth by Store Type", "")
    assortment_limits = {
        "Micro": extract_percentage_range(re.search(r'Micro.*?(\d+-\d+%)', assortment_rule).group(1)),
        "Medium": extract_percentage_range(re.search(r'Medium.*?(\d+-\d+%)', assortment_rule).group(1)),
        "Large": extract_percentage_range(re.search(r'Large.*?(\d+-\d+%)', assortment_rule).group(1))
    }
    
    # Extract location biases
    premium_rule = business_rules.get("Premium Location Assortment", "")
    budget_rule = business_rules.get("Budget Location Assortment", "")
    
    premium_locations = [loc.strip(" '[],") for loc in re.search(r'\[(.*?)\]', premium_rule).group(1).split(',')]
    budget_locations = [loc.strip(" '[],") for loc in re.search(r'\[(.*?)\]', budget_rule).group(1).split(',')]
    
    premium_bias = extract_percentage(premium_rule)
    budget_bias = extract_percentage(budget_rule)
    
    # Reorder level multipliers
    reorder_rules = config['reorder_level_rules']
    reorder_multipliers = {
        k: extract_percentage(v) for k, v in reorder_rules.items()
    }
    
    cat_to_velocity = build_velocity_map(config['product_category_rules']['velocity_mapping'])
    stock_rules = config['stock_rules']
    
    inventory_records = []
    inventory_seq = 1
    batch_seq = 1

    print("Generating inventory deterministically. This may take a moment...")

    # 2. Iterate through each dark store
    for _, store in df_stores.iterrows():
        store_id = store['Store_ID']
        store_type = store['Store_Type']
        store_area = store['Area']
        temp_controlled = str(store.get('Temperature_Control', 'False')).lower() in ['true', '1', 'yes']
        
        # 3. Filter eligible products (Temperature Control Guardrail)
        eligible_products = df_products.copy()
        if not temp_controlled:
            # Exclude frozen/refrigerated if store lacks temp control
            eligible_products = eligible_products[
                ~eligible_products['Storage_Type'].isin(['Refrigerated', 'Frozen'])
            ]
            
        if len(eligible_products) == 0:
            continue

        # 4. Calculate Assortment Sample Size based on eligible products
        min_pct, max_pct = assortment_limits.get(store_type, (0.50, 0.60))
        target_sku_count = int(len(eligible_products) * random.uniform(min_pct, max_pct))

        # 5. Apply Location Biases for Weighted Sampling
        weights = np.ones(len(eligible_products))
        tiers = eligible_products['Brand_Tier'].values
        
        if store_area in premium_locations:
            weights = np.where(tiers == 'Premium', weights * (1.0 + premium_bias), weights)
        elif store_area in budget_locations:
            weights = np.where(tiers == 'Budget', weights * (1.0 + budget_bias), weights)
            
        # Normalize weights
        weights /= weights.sum()
        
        # Select product indices without replacement
        selected_indices = np.random.choice(
            eligible_products.index, 
            size=target_sku_count, 
            replace=False, 
            p=weights
        )
        selected_products = eligible_products.loc[selected_indices]

        # 6. Generate Inventory Record for each selected product
        for _, product in selected_products.iterrows():
            prod_id = product['Product_ID']
            category = product['Category']
            shelf_life = float(product['Shelf_Life_Days'])
            
            # Identify Velocity & Stock Rule
            velocity = cat_to_velocity.get(category, 'Medium')
            stock_rule = stock_rules.get(category, {"min": 10, "max": 50})
            
            # Stock & Reorder Levels
            max_stock = stock_rule['max']
            min_stock = stock_rule['min']
            reorder_level = int(max_stock * reorder_multipliers.get(velocity, 0.25))
            
            # Determine Out of Stock Probability based on Velocity
            if velocity == 'Fast':
                oos_prob = random.uniform(0.08, 0.10)
            elif velocity == 'Medium':
                oos_prob = random.uniform(0.04, 0.05)
            else:
                oos_prob = random.uniform(0.01, 0.02)

            # Determine Current Stock
            if random.random() < oos_prob:
                current_stock = 0
            else:
                current_stock = random.randint(min_stock, max_stock)
                
            # Inventory Status Logic
            if current_stock == 0:
                inv_status = "Out of Stock"
            elif current_stock <= reorder_level:
                inv_status = "Low Stock"
            else:
                inv_status = "In Stock"

            # Dates Generation
            days_ago = random.randint(1, 30)
            last_restock = SIMULATION_BASELINE_DATE - timedelta(days=days_ago)
            
            # Next Restock Logic
            if inv_status == "Out of Stock":
                # Urgent Replenishment Rule (within 48 hrs of baseline)
                next_restock = SIMULATION_BASELINE_DATE + timedelta(days=random.randint(0, 2))
            else:
                # Based on Velocity
                if velocity == 'Fast':
                    add_days = random.randint(3, 5)
                elif velocity == 'Medium':
                    add_days = random.randint(5, 8)
                else:
                    add_days = random.randint(8, 15)
                next_restock = last_restock + timedelta(days=add_days)
                # Ensure next_restock is strictly in the future relative to last_restock
                if next_restock <= last_restock:
                    next_restock = last_restock + timedelta(days=1)

            # Batch ID (e.g. B250401001)
            date_str = last_restock.strftime("%y%m%d")
            batch_id = f"B{date_str}{batch_seq:04d}"
            batch_seq += 1
            
            # Expiry Date Logic
            is_perishable = str(product.get('Is_Perishable', 'False')).lower() in ['true', '1', 'yes']
            if is_perishable:
                remaining_pct = random.uniform(0.50, 0.95)
                remaining_life_days = int(shelf_life * remaining_pct)
                expiry_date = (last_restock + timedelta(days=remaining_life_days)).strftime('%Y-%m-%d')
            else:
                expiry_date = "Not Applicable"

            # Primary Key
            inventory_id = f"INV{inventory_seq:06d}"
            inventory_seq += 1

            inventory_records.append({
                "Inventory_ID": inventory_id,
                "Store_ID": store_id,
                "Product_ID": prod_id,
                "Current_Stock": current_stock,
                "Reorder_Level": reorder_level,
                "Last_Restock_Date": last_restock.strftime('%Y-%m-%d'),
                "Next_Restock_Date": next_restock.strftime('%Y-%m-%d'),
                "Batch_ID": batch_id,
                "Expiry_Date": expiry_date,
                "Inventory_Status": inv_status
            })

    # 7. Create final DataFrame matching schema strictly
    df_inv = pd.DataFrame(inventory_records)
    df_inv = df_inv[config['global_rules']['column_schema']]
    return df_inv

# ==========================================================
# VALIDATION
# ==========================================================
def validate_inventory(df: pd.DataFrame, df_stores: pd.DataFrame, df_products: pd.DataFrame, config: Dict[str, Any]):
    """Enforces strict data quality constraints before export."""
    print("Validating generated inventory...")

    # 1. Uniqueness
    if df['Inventory_ID'].duplicated().any():
        raise ValueError("VALIDATION FAILED: Duplicate Inventory_IDs found.")
    if df['Batch_ID'].duplicated().any():
        raise ValueError("VALIDATION FAILED: Duplicate Batch_IDs found.")

    # 2. Foreign Key Integrity
    valid_stores = set(df_stores['Store_ID'])
    valid_products = set(df_products['Product_ID'])
    if not df['Store_ID'].isin(valid_stores).all():
        raise ValueError("VALIDATION FAILED: Invalid Store_IDs present.")
    if not df['Product_ID'].isin(valid_products).all():
        raise ValueError("VALIDATION FAILED: Invalid Product_IDs present.")

    # 3. Numeric Bounds
    if (df['Current_Stock'] < 0).any():
        raise ValueError("VALIDATION FAILED: Current_Stock cannot be negative.")
    if (df['Reorder_Level'] < 0).any():
        raise ValueError("VALIDATION FAILED: Reorder_Level cannot be negative.")

    # 4. Dates Logic
    df['last_dt'] = pd.to_datetime(df['Last_Restock_Date'])
    df['next_dt'] = pd.to_datetime(df['Next_Restock_Date'])
    if (df['next_dt'] <= df['last_dt']).any():
        raise ValueError("VALIDATION FAILED: Next_Restock_Date must be after Last_Restock_Date.")
    
    # 5. Inventory Status Consistency
    oos = df[df['Inventory_Status'] == 'Out of Stock']
    if not (oos['Current_Stock'] == 0).all():
        raise ValueError("VALIDATION FAILED: Status 'Out of Stock' but Current_Stock != 0.")
    
    ls = df[df['Inventory_Status'] == 'Low Stock']
    if not ((ls['Current_Stock'] <= ls['Reorder_Level']) & (ls['Current_Stock'] > 0)).all():
        raise ValueError("VALIDATION FAILED: 'Low Stock' mathematical inconsistency.")

    # Cleanup temp columns
    df.drop(columns=['last_dt', 'next_dt'], inplace=True)
    
    # 6. Null check
    if df.isnull().values.any():
        raise ValueError("VALIDATION FAILED: Null values detected.")

    # 7. Assortment Size Validation
    business_rules = {r['name']: r['logic'] for r in config['business_rules']}
    assortment_rule = business_rules.get("Assortment Depth by Store Type", "")
    assortment_limits = {
        "Micro": extract_percentage_range(re.search(r'Micro.*?(\d+-\d+%)', assortment_rule).group(1)),
        "Medium": extract_percentage_range(re.search(r'Medium.*?(\d+-\d+%)', assortment_rule).group(1)),
        "Large": extract_percentage_range(re.search(r'Large.*?(\d+-\d+%)', assortment_rule).group(1))
    }

    for _, store in df_stores.iterrows():
        store_id = store['Store_ID']
        store_type = store['Store_Type']
        temp_controlled = str(store.get('Temperature_Control', 'False')).lower() in ['true', '1', 'yes']
        
        eligible_products = df_products.copy()
        if not temp_controlled:
            eligible_products = eligible_products[~eligible_products['Storage_Type'].isin(['Refrigerated', 'Frozen'])]
            
        if len(eligible_products) == 0:
            continue
            
        store_inventory = df[df['Store_ID'] == store_id]
        sku_count = len(store_inventory)
        
        min_pct, max_pct = assortment_limits.get(store_type, (0.50, 0.60))
        min_skus = int(len(eligible_products) * min_pct)
        max_skus = int(len(eligible_products) * max_pct)
        
        if not (min_skus <= sku_count <= max_skus):
            raise ValueError(f"VALIDATION FAILED: Store {store_id} ({store_type}) has {sku_count} SKUs. Expected between {min_skus} and {max_skus} (based on {len(eligible_products)} eligible products).")

    print("✓ All Validations Passed.")

# ==========================================================
# SUMMARY
# ==========================================================
def print_summary(df: pd.DataFrame, df_stores: pd.DataFrame):
    print("\n" + "="*50)
    print(" INVENTORY GENERATION SUMMARY")
    print("="*50)
    
    total_records = len(df)
    print(f"Total Inventory Records       : {total_records:,}")
    
    # Merge for store type analysis
    df_merged = df.merge(df_stores[['Store_ID', 'Store_Type']], on='Store_ID', how='left')
    
    print("\nRecords per Store Type:")
    type_counts = df_merged['Store_Type'].value_counts()
    for stype, count in type_counts.items():
        print(f" - {stype:<10} : {count:,} records")
        
    print("\nInventory Status Distribution:")
    status_counts = df['Inventory_Status'].value_counts(normalize=True) * 100
    for status, pct in status_counts.items():
        print(f" - {status:<15} : {pct:.1f}%")

    print(f"\nAverage Current Stock         : {df['Current_Stock'].mean():.1f} units")
    print(f"Average Reorder Level         : {df['Reorder_Level'].mean():.1f} units")
    
    perishable = len(df[df['Expiry_Date'] != 'Not Applicable'])
    non_perishable = total_records - perishable
    print(f"Perishable Records            : {perishable:,}")
    print(f"Non-perishable Records        : {non_perishable:,}")
    
    print(f"\nNull Count                    : {df.isnull().sum().sum()}")
    print(f"Duplicate Count               : {df.duplicated().sum()}")
    print("="*50)

# ==========================================================
# EXECUTION PIPELINE
# ==========================================================
def main():
    try:
        # 1. Load Configurations & Data
        with open(JSON_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
            
        try:
            df_products = pd.read_csv(PRODUCTS_FILE)
            df_stores = pd.read_csv(DARKSTORES_FILE)
        except FileNotFoundError as e:
            raise FileNotFoundError(f"CRITICAL ERROR: Data dependency missing. {e}")

        # Ensure required columns exist in mocked/provided CSVs
        if 'Brand_Tier' not in df_products.columns:
            df_products['Brand_Tier'] = 'Popular'  # Fallback for robustness
            
        # 2. Generate Inventory
        df_inventory = generate_inventory(config, df_products, df_stores)
        
        # 3. Validate Inventory
        validate_inventory(df_inventory, df_stores, df_products, config)
        
        # 4. Export
        df_inventory.to_csv(OUTPUT_FILE, index=False, encoding='utf-8')
        print(f"\nSuccess! Generated '{OUTPUT_FILE}'.")
        
        # 5. Summary
        print_summary(df_inventory, df_stores)
        
    except Exception as e:
        print(f"\n{str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()