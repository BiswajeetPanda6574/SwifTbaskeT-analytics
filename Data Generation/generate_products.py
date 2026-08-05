#!/usr/bin/env python3
"""
QuickCommerce BI - Product Catalog Generator
Region: Bengaluru
Description: Reads master_products_v2.json and generates a highly realistic, 
             rebalanced, and validated products.csv for enterprise BI usage.
"""

import json
import random
import re
import pandas as pd
import numpy as np

# Deterministic generation for reproducible BI datasets
random.seed(42)
np.random.seed(42)

INPUT_JSON = "master_products_v2.json"
OUTPUT_CSV = "products.csv"
TARGET_TOTAL_PRODUCTS = 2500

# 4. Weighted Category Targets
CATEGORY_WEIGHTS = {
    "Fruits & Vegetables": 0.08,
    "Dairy, Bread & Eggs": 0.08,
    "Meat & Fish": 0.05,
    "Staples & Grocery": 0.15,
    "Snacks": 0.18,
    "Beverages": 0.10,
    "Frozen Foods": 0.05,
    "Beauty & Personal Care": 0.12,
    "Household Essentials": 0.10,
    "Baby Care": 0.04,
    "Fashion & Lifestyle": 0.02,
    "Pharmacy": 0.02,
    "Pet Care": 0.01
}

def clean_str(s):
    """Removes special characters for SKU generation."""
    return re.sub(r'[^A-Za-z0-9]', '', str(s).upper())

def generate_sku(brand, item, variant, size_val):
    """Generates a realistic and unique SKU."""
    b = clean_str(brand)[:3]
    i = clean_str(item)[:3]
    v = clean_str(variant)[:3] if variant else "REG"
    s = str(size_val).replace('.', '')
    return f"{b}-{i}-{v}-{s}"

def generate_name(brand, item, type_val, variant, flavour, size_val, unit):
    """Builds a natural sounding product name without redundancy."""
    parts = [brand]
    
    # 2. Prevent natural redundancies (e.g., "Milk Cow Milk")
    if type_val and item.lower() in type_val.lower():
        parts.append(type_val)
    else:
        parts.append(item)
        if type_val: 
            parts.append(type_val)
            
    if variant and variant.lower() not in [p.lower() for p in parts]:
        parts.append(variant)
    if flavour and flavour.lower() not in [p.lower() for p in parts]:
        parts.append(flavour)
    
    # Final cleanup of adjacent duplicates
    clean_parts = []
    seen = set()
    for p in parts:
        if p and p.lower() not in seen:
            clean_parts.append(p)
            seen.add(p.lower())
            
    base_name = " ".join(clean_parts)
    return f"{base_name} {size_val} {unit}"

def get_discount_percentage():
    """Returns discount based on specified realistic distribution."""
    bracket = np.random.choice([1, 2, 3, 4], p=[0.20, 0.35, 0.30, 0.15])
    if bracket == 1:   return random.uniform(0, 5)
    elif bracket == 2: return random.uniform(5, 10)
    elif bracket == 3: return random.uniform(10, 20)
    else:              return random.uniform(20, 35)

def get_gross_margin(category):
    """Returns category-specific gross margin percentages."""
    cat = category.lower()
    if "fruits" in cat or "vegetables" in cat: return random.uniform(0.15, 0.25)
    if "beauty" in cat or "personal" in cat: return random.uniform(0.30, 0.50)
    if "electronics" in cat or "kitchen" in cat: return random.uniform(0.10, 0.20)
    if "pharmacy" in cat or "health" in cat: return random.uniform(0.15, 0.30)
    return random.uniform(0.20, 0.35)

def calculate_pricing(price_range, category, size_multiplier=1.0):
    """Calculates valid MRP, Selling Price, and Cost Price."""
    min_p, max_p = price_range["min"], price_range["max"]
    base_mrp = random.uniform(min_p, max_p) * size_multiplier
    
    mrp = round(base_mrp)
    
    # 3. Round prices to Indian retail endings (x5, x9)
    if mrp > 30:
        base_ten = (mrp // 10) * 10
        remainder = mrp % 10
        if remainder < 4:
            mrp = base_ten - 1 if base_ten > 0 else base_ten + 5
        elif remainder < 8:
            mrp = base_ten + 5
        else:
            mrp = base_ten + 9
            
    discount_pct = get_discount_percentage()
    selling_price = round(mrp * (1 - (discount_pct / 100)), 2)
    
    # Safety checks
    if selling_price >= mrp:
        selling_price = float(mrp)
        discount_pct = 0.0
        
    margin = get_gross_margin(category)
    cost_price = round(selling_price * (1 - margin), 2)
    
    if cost_price >= selling_price:
        cost_price = round(selling_price * 0.90, 2)
        
    return mrp, selling_price, cost_price, round(discount_pct, 1)

def extract_base_combinations(json_data):
    """Flattens the JSON into raw combinations."""
    combos = []
    for cat in json_data.get("categories", []):
        cat_name = cat["category_name"]
        for sub in cat.get("sub_categories", []):
            sub_name = sub["sub_category_name"]
            storage = sub["storage_type"]
            gst = sub["gst_percentage"]
            shelf_life = sub["base_shelf_life_days"]
            
            for brand in sub.get("brands", []):
                brand_name = brand["name"]
                brand_tier = brand["tier"]
                
                for item in sub.get("items", []):
                    item_name = item["item_name"]
                    types = item.get("types", [None]) or [None]
                    variants = item.get("variants", [None]) or [None]
                    flavours = item.get("flavours", [None]) or [None]
                    
                    for t in types:
                        for v in variants:
                            for f in flavours:
                                for s in item.get("sizes", []):
                                    combos.append({
                                        "Category": cat_name,
                                        "Sub_Category": sub_name,
                                        "Brand": brand_name,
                                        "Brand_Tier": brand_tier,
                                        "Item": item_name,
                                        "Type": t,
                                        "Variant": v,
                                        "Flavour": f,
                                        "Unit": s["unit"],
                                        "Size": s["value"],
                                        "Price_Range": s["price_range"],
                                        "Storage_Type": storage,
                                        "GST": gst,
                                        "Shelf_Life": shelf_life,
                                        "Size_Multiplier": 1.0
                                    })
    return combos

def rebalance_catalog(combos):
    """
    Applies weighted targets. Upsamples via realistic size scaling.
    """
    df = pd.DataFrame(combos)
    rebalanced = []
    
    for cat in df['Category'].unique():
        cat_items = df[df['Category'] == cat].to_dict('records')
        weight = CATEGORY_WEIGHTS.get(cat, 0.05)
        target_count = int(TARGET_TOTAL_PRODUCTS * weight)
        
        if len(cat_items) >= target_count:
            # Downsample if we have too many base combinations
            rebalanced.extend(random.sample(cat_items, target_count))
        else:
            # 1. Upsample by creating valid intermediate sizes
            rebalanced.extend(cat_items)
            needed = target_count - len(cat_items)
            
            for _ in range(needed):
                base_item = random.choice(cat_items).copy()
                scale_factor = random.choice([1.25, 1.5, 2.0, 3.0])
                
                # Apply size transformation based on unit type
                if base_item["Unit"] in ["g", "ml"]:
                    base_item["Size"] = int(base_item["Size"] * scale_factor)
                elif base_item["Unit"] in ["kg", "L"]:
                    base_item["Size"] = round(base_item["Size"] * scale_factor, 1)
                else:
                    base_item["Size"] += int(scale_factor)
                
                base_item["Size_Multiplier"] = scale_factor
                rebalanced.append(base_item)
                
    return rebalanced

def generate_dataset():
    print("Loading JSON Master...")
    with open(INPUT_JSON, 'r', encoding='utf-8') as f:
        master_data = json.load(f)
        
    global_rules = master_data.get("global_rules", {})
    rating_ranges = global_rules.get("rating_ranges", {})
    
    print("Extracting Combinations...")
    base_combos = extract_base_combinations(master_data)
    
    print("Rebalancing Categories via Weights...")
    balanced_combos = rebalance_catalog(base_combos)
    random.shuffle(balanced_combos)
    
    dataset = []
    seen_skus = set()
    
    # Ensure uniqueness during construction
    seen_combos = set()
    
    print(f"Generating realistic products...")
    for item in balanced_combos:
        # Check combination uniqueness
        combo_key = (item["Brand"], item["Item"], item["Type"], item["Variant"], item["Flavour"], item["Size"])
        if combo_key in seen_combos:
            continue
        seen_combos.add(combo_key)
        
        product_id = f"P{len(dataset)+1:06d}"
        
        # Name & SKU
        base_sku = generate_sku(item["Brand"], item["Item"], item["Variant"], item["Size"])
        sku = base_sku
        counter = 1
        while sku in seen_skus:
            sku = f"{base_sku}-{counter}"
            counter += 1
        seen_skus.add(sku)
        
        name = generate_name(
            item["Brand"], item["Item"], item["Type"], 
            item["Variant"], item["Flavour"], item["Size"], item["Unit"]
        )
            
        # Pricing
        mrp, sp, cp, disc = calculate_pricing(item["Price_Range"], item["Category"], item["Size_Multiplier"])
        
        # Ratings
        tier = item["Brand_Tier"]
        r_min, r_max = rating_ranges[tier]["min"], rating_ranges[tier]["max"]
        rating = round(random.uniform(r_min, r_max), 1)
        
        # Status
        status = np.random.choice(
            ["Available", "Low Stock", "Out Of Stock", "Discontinued"], 
            p=[0.92, 0.05, 0.02, 0.01]
        )
        
        # Launch Status
        launch = np.random.choice(["Regular", "New Arrival", "Seasonal"], p=[0.90, 0.05, 0.05])
        if any(word in name.lower() for word in ["mango", "strawberry", "winter", "summer", "monsoon"]):
            launch = "Seasonal"
            
        # Perishable
        is_perish = True if item["Storage_Type"] in ["Refrigerated", "Frozen"] else False
        if "Fruits" in item["Category"] or "Vegetables" in item["Category"]:
            is_perish = True
            
        dataset.append({
            "Product_ID": product_id,
            "SKU": sku,
            "Product_Name": name,
            "Brand": item["Brand"],
            "Brand_Tier": item["Brand_Tier"],
            "Category": item["Category"],
            "Sub_Category": item["Sub_Category"],
            "Item": item["Item"],
            "Type": item["Type"] if item["Type"] else "",
            "Variant": item["Variant"] if item["Variant"] else "",
            "Flavour": item["Flavour"] if item["Flavour"] else "",
            "Unit": item["Unit"],
            "Size": item["Size"],
            "MRP": mrp,
            "Selling_Price": sp,
            "Cost_Price": cp,
            "Discount_Percentage": disc,
            "Shelf_Life_Days": item["Shelf_Life"],
            "Storage_Type": item["Storage_Type"],
            "GST_Percentage": item["GST"],
            "Is_Perishable": is_perish,
            "Product_Status": status,
            "Average_Rating": rating,
            "Launch_Status": launch
        })
        
    return pd.DataFrame(dataset)

def validate_and_export(df):
    print("\nRunning Quality Checks...")
    
    # Ensure optional text columns never contain empty strings or NaNs (pandas safe)
    df[['Type', 'Variant', 'Flavour']] = df[['Type', 'Variant', 'Flavour']].replace(r'^\s*$', 'Not Applicable', regex=True).fillna('Not Applicable')
    
    # 5. Full Combination validation checks
    combo_subset = ['Brand', 'Item', 'Type', 'Variant', 'Flavour', 'Size']
    duplicates_count = df.duplicated(subset=combo_subset).sum()
    assert duplicates_count == 0, f"Found {duplicates_count} duplicated product combinations!"
    
    assert df["Product_ID"].duplicated().sum() == 0, "Duplicate Product IDs found!"
    assert df["SKU"].duplicated().sum() == 0, "Duplicate SKUs found!"
    assert (df["Selling_Price"] > df["MRP"]).sum() == 0, "Selling Price > MRP detected!"
    assert (df["Cost_Price"] >= df["Selling_Price"]).sum() == 0, "Cost Price >= Selling Price detected!"
    assert df.isnull().sum().sum() == 0, "Null values detected in dataset!"
    
    # Export
    df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8')
    print(f"Validation Passed. Exported {len(df)} rows to {OUTPUT_CSV}")

def print_statistics(df):
    print("\n====================================================")
    print("DATASET GENERATION SUMMARY")
    print("====================================================")
    print(f"Total Products Generated: {len(df)}")
    print(f"Duplicate Full-Combinations: 0 (Validated)")
    print(f"Null Values Count: {df.isnull().sum().sum()}")
    
    print("\nProducts per Category (Weighted Distribution):")
    print(df['Category'].value_counts().to_string())
    
    print("\nAverage Selling Price by Category:")
    print(df.groupby('Category')['Selling_Price'].mean().round(2).to_string())
    print("====================================================\n")

if __name__ == "__main__":
    df_products = generate_dataset()
    validate_and_export(df_products)
    print_statistics(df_products)