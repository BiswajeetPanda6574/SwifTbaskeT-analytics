import pandas as pd
import numpy as np
import json
import random
import bisect
import time
import sys

def load_json(filepath: str) -> dict:
    with open(filepath, 'r') as f:
        return json.load(f)

def load_data():
    try:
        orders = pd.read_csv('orders.csv')
        products = pd.read_csv('products.csv')
        return orders, products
    except FileNotFoundError as e:
        print(f"Critical Error: Missing required input file. {e}")
        sys.exit(1)

def generate_order_details(orders: pd.DataFrame, products: pd.DataFrame, config: dict) -> pd.DataFrame:
    all_prods = products.to_dict('records')
    all_prods_sorted = sorted(all_prods, key=lambda x: x['Selling_Price'])
    prices = [p['Selling_Price'] for p in all_prods_sorted]
    
    # Pre-group products by category for O(1) lookups
    prods_by_cat = {}
    for p in all_prods:
        c = p.get('Category', 'Unknown')
        if c not in prods_by_cat:
            prods_by_cat[c] = []
        prods_by_cat[c].append(p)
        
    themes = config['basket_composition_rules']['themes']
    theme_keys = list(themes.keys())
    theme_probs = config['basket_composition_rules']['theme_probability']
    
    # Precompute theme pools to eliminate redundant nested loops over 300,000+ orders
    theme_pools = {}
    for t_name, t_cats in themes.items():
        pool = []
        for c in t_cats:
            if c in prods_by_cat:
                pool.extend(prods_by_cat[c])
        # Fallback if a theme yields no products
        theme_pools[t_name] = pool if pool else all_prods
    
    qty_rules = config['quantity_rules']['distributions']
    qty_map = config['quantity_rules']['category_mapping']
    max_discount_pct = config['discount_rules']['max_discount_percentage']
    
    id_fmt = config.get('id_format', 'OD{index:08d}')
    detail_id_counter = 1
    
    order_details_list = []
    
    # Use itertuples for significant performance boost over iterrows
    for order_row in orders.itertuples():
        order_id = order_row.Order_ID
        target_value = round(order_row.Total_Order_Value, 2)
        
        # Pick a realistic basket theme
        theme_name = random.choices(theme_keys, weights=theme_probs)[0]
        theme_pool = theme_pools[theme_name]
            
        basket_items = {} 
        current_subtotal = 0.0
        
        # Max subtotal bounds (to respect max 40% discount limit)
        max_subtotal = target_value / (1 - max_discount_pct)
        
        # Basket Generation Loop
        while current_subtotal < target_value:
            max_allowed = max_subtotal - current_subtotal
            
            candidate_pool = theme_pool if random.random() < 0.85 else all_prods
            p = random.choice(candidate_pool)
            
            # Enforce max price boundary smoothly using binary search
            if p['Selling_Price'] > max_allowed:
                idx = bisect.bisect_right(prices, max_allowed)
                if idx > 0:
                    p = all_prods_sorted[random.randint(0, idx - 1)]
                else:
                    # Target gap is smaller than cheapest product - fallback to absolute cheapest
                    p = all_prods_sorted[0]
                    
            price = p['Selling_Price']
            
            # Failsafe against potential infinite loop if price data is flawed
            if price <= 0:
                raise ValueError(f"Invalid Product Selling_Price: {price} for Product_ID {p.get('Product_ID')}")
                
            cat = p.get('Category', 'Unknown')
            
            qty_profile = qty_map.get(cat, 'default')
            q_choices = qty_rules.get(qty_profile, qty_rules['default'])
            q_weights = qty_rules.get(f"{qty_profile}_weights", qty_rules['default_weights'])
            q = random.choices(q_choices, weights=q_weights)[0]
            
            # Downscale quantity if adding multiple exceeds allowed threshold
            while q > 1 and (current_subtotal + price * q) > max_subtotal:
                q -= 1
                
            pid = p['Product_ID']
            if pid in basket_items:
                basket_items[pid]['qty'] += q
            else:
                basket_items[pid] = {'price': price, 'qty': q, 'pid': pid}
                
            current_subtotal += (price * q)
            
        # Distribute Discount proportionally to item subtotal to hit Target exactly
        total_discount = current_subtotal - target_value
        items_list = list(basket_items.values())
        
        for item in items_list:
            item['subtotal'] = item['price'] * item['qty']
            item['discount'] = round(total_discount * (item['subtotal'] / current_subtotal), 2)
            item['final_price'] = item['subtotal'] - item['discount']
            
        # Math verification and cent-level rounding reconciler 
        current_final = sum(i['final_price'] for i in items_list)
        diff = round(target_value - current_final, 2)
        
        if diff != 0:
            steps = int(abs(diff) * 100)
            sign = 1 if diff > 0 else -1
            # Sort with pid fallback to guarantee cross-platform determinism
            items_list.sort(key=lambda x: (x['subtotal'], x['pid']), reverse=True)
            
            idx_mod = 0
            for _ in range(steps):
                it = items_list[idx_mod % len(items_list)]
                it['final_price'] = round(it['final_price'] + sign * 0.01, 2)
                it['discount'] = round(it['subtotal'] - it['final_price'], 2)
                idx_mod += 1
                
        # Append finalized records
        for item in items_list:
            order_details_list.append({
                'Order_Detail_ID': id_fmt.format(index=detail_id_counter),
                'Order_ID': order_id,
                'Product_ID': item['pid'],
                'Quantity': item['qty'],
                'Selling_Price': item['price'],
                'Item_Discount': item['discount'],
                'Final_Item_Price': item['final_price']
            })
            detail_id_counter += 1
            
    df = pd.DataFrame(order_details_list)
    return df[config['columns']]

def validate_details(df: pd.DataFrame, orders: pd.DataFrame, products: pd.DataFrame):
    print("Running strict validations...")
    errors = []
    
    if df['Order_Detail_ID'].duplicated().any():
        errors.append("Duplicate Order_Detail_ID found.")
    
    if df.duplicated(subset=['Order_ID', 'Product_ID']).any():
        errors.append("Duplicate (Order_ID, Product_ID) combination found.")
        
    if not df['Product_ID'].isin(products['Product_ID']).all():
        errors.append("Invalid Product_IDs found.")
        
    if not df['Order_ID'].isin(orders['Order_ID']).all():
        errors.append("Invalid Order_IDs found.")
        
    if df.isnull().any().any():
        errors.append("NULL values detected in output.")
        
    if (df['Quantity'] <= 0).any() or not pd.api.types.is_integer_dtype(df['Quantity']):
        errors.append("Quantities must be positive integers.")
        
    if (df['Selling_Price'] <= 0).any():
        errors.append("Non-positive Selling_Price found.")
        
    if (df['Item_Discount'] < 0).any():
        errors.append("Negative Item_Discount found.")
        
    if (df['Final_Item_Price'] < 0).any():
        errors.append("Negative Final_Item_Price found.")
        
    expected_math = round(df['Selling_Price'] * df['Quantity'] - df['Item_Discount'], 2)
    actual_math = round(df['Final_Item_Price'], 2)
    if not np.isclose(expected_math, actual_math).all():
        errors.append("Final_Item_Price formula failed.")
        
    # Order Value Reconciliation Check (Mandatory ±0.01 tolerance)
    agg = df.groupby('Order_ID')['Final_Item_Price'].sum().round(2)
    merged = agg.reset_index().merge(orders[['Order_ID', 'Total_Order_Value']], on='Order_ID')
    merged['diff'] = abs(merged['Final_Item_Price'] - merged['Total_Order_Value'])
    
    if (merged['diff'] > 0.011).any():
        errors.append("Order total reconciliation failed (Tolerance ±0.01 breached).")
        
    if errors:
        print("\n--- VALIDATION FAILED ---")
        for e in errors:
            print(f"[X] {e}")
        sys.exit(1)
    else:
        print("[✓] All validations passed successfully!")

def main():
    start_time = time.time()
    
    # Ensure determinism
    random.seed(42)
    np.random.seed(42)
    
    config = load_json('master_order_details_v1.json')
    orders, products = load_data()
    
    print("Generating Order Details...")
    df = generate_order_details(orders, products, config)
    
    validate_details(df, orders, products)
    
    print("\nSaving to order_details.csv...")
    df.to_csv("order_details.csv", index=False)
    print("[✓] order_details.csv has been successfully generated.")
    
    elapsed_time = time.time() - start_time
    
    # Print summary
    print("\n--- SUMMARY METRICS ---")
    print(f"Total Order Details generated:  {len(df):,}")
    print(f"Total Orders fulfilled:         {df['Order_ID'].nunique():,}")
    print(f"Avg Items per Basket:           {len(df) / df['Order_ID'].nunique():.2f}")
    print(f"Average Final Item Price:       ₹{df['Final_Item_Price'].mean():.2f}")
    print(f"Avg Item Discount:              ₹{df['Item_Discount'].mean():.2f}")
    print(f"Total Portfolio Value:          ₹{df['Final_Item_Price'].sum():,.2f}")
    print(f"Generation Time:                {elapsed_time:.2f} seconds")

if __name__ == "__main__":
    main()