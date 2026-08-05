import pandas as pd
import numpy as np
import json
import random
import time
import sys

def load_json(filepath: str) -> dict:
    with open(filepath, 'r') as f:
        return json.load(f)

def load_data():
    try:
        orders = pd.read_csv('orders.csv')
        details = pd.read_csv('order_details.csv')
        return orders, details
    except FileNotFoundError as e:
        print(f"Critical Error: Missing required input file. {e}")
        sys.exit(1)

def generate_returns(orders: pd.DataFrame, details: pd.DataFrame, config: dict) -> pd.DataFrame:
    # 1. Merge details with orders to identify eligible items based on Order_Status
    eligible_items = details.merge(
        orders[['Order_ID', 'Order_Status', 'Order_Timestamp']], 
        on='Order_ID', 
        how='inner'
    )
    
    # Strictly filter to only "Delivered" orders
    eligible_items = eligible_items[eligible_items['Order_Status'] == 'Delivered'].copy()
    
    # 2. Determine returns via base_return_probability
    base_prob = config['return_rate_rules']['base_return_probability']
    mask = np.random.rand(len(eligible_items)) < base_prob
    returns = eligible_items[mask].copy()
    
    n = len(returns)
    
    if n == 0:
        print("Warning: No returns generated based on the probability.")
        return pd.DataFrame(columns=config['global_rules']['columns'])
        
    # 3. Generate Return_Reason
    reason_dist = config['return_reason_rules']['distribution']
    returns['Return_Reason'] = np.random.choice(
        list(reason_dist.keys()),
        p=list(reason_dist.values()),
        size=n
    )
    
    # 4. Generate Return_Status
    status_dist = config['return_status_rules']['distribution']
    returns['Return_Status'] = np.random.choice(
        list(status_dist.keys()),
        p=list(status_dist.values()),
        size=n
    )
    
    # 5. Generate Return_Date based on Order_Timestamp and JSON offset distribution
    offset_dist = config['return_date_rules']['offset_days_distribution']
    offset_choices = [int(k) for k in offset_dist.keys()]
    offset_probs = list(offset_dist.values())
    offsets = np.random.choice(offset_choices, p=offset_probs, size=n)
    
    order_ts = pd.to_datetime(returns['Order_Timestamp'])
    # Adding directly to datetime ensures Return_Date >= Order_Timestamp even if offset is 0
    returns['Return_Date'] = (order_ts + pd.to_timedelta(offsets, unit='D')).dt.strftime('%Y-%m-%d %H:%M:%S')
    
    # 6. Calculate Refund_Amount
    status_mult = config['refund_rules']['status_multiplier']
    mult_array = returns['Return_Status'].map(status_mult).values
    returns['Refund_Amount'] = np.round(returns['Final_Item_Price'] * mult_array, 2)
    
    # 7. Generate deterministic Return_ID
    id_fmt = config['global_rules']['id_format']
    returns['Return_ID'] = [id_fmt.format(index=i+1) for i in range(n)]
    
    # 8. Select and order columns as per configuration
    cols = config['global_rules']['columns']
    return returns[cols].copy()

def validate_returns(returns: pd.DataFrame, orders: pd.DataFrame, details: pd.DataFrame):
    print("Running strict validations...")
    errors = []
    
    # Unique Return_ID check
    if returns['Return_ID'].duplicated().any():
        errors.append("Duplicate Return_ID found.")
        
    # No NULL values check
    if returns.isnull().any().any():
        errors.append("NULL values found in output.")
        
    # Order_ID exists check
    if not returns['Order_ID'].isin(orders['Order_ID']).all():
        errors.append("Generated returns contain invalid Order_IDs not present in orders.csv.")
        
    # (Order_ID, Product_ID) exists check
    merged_op = returns[['Order_ID', 'Product_ID']].merge(
        details[['Order_ID', 'Product_ID']],
        on=['Order_ID', 'Product_ID'],
        how='left',
        indicator=True
    )
    if (merged_op['_merge'] != 'both').any():
        errors.append("Generated returns contain invalid (Order_ID, Product_ID) combinations.")
        
    # Only Delivered Orders returned check
    merged_orders = returns[['Order_ID']].merge(orders[['Order_ID', 'Order_Status']], on='Order_ID')
    if (merged_orders['Order_Status'] != 'Delivered').any():
        errors.append("Returns generated for non-Delivered orders.")
        
    # Refund constraints checks
    if (returns['Refund_Amount'] < 0).any():
        errors.append("Negative Refund_Amount found.")
        
    val_df = returns.merge(details[['Order_ID', 'Product_ID', 'Final_Item_Price']], on=['Order_ID', 'Product_ID'])
    
    if not (
        (val_df['Refund_Amount'] < val_df['Final_Item_Price']) |
        np.isclose(
            val_df['Refund_Amount'],
            val_df['Final_Item_Price'],
            atol=0.01
        )
    ).all():
        errors.append("Refund_Amount exceeds Final_Item_Price beyond allowable tolerance.")
        
    pending_rejected = returns[returns['Return_Status'].isin(['Pending', 'Rejected'])]
    if (pending_rejected['Refund_Amount'] != 0).any():
        errors.append("Refund_Amount is not EXACTLY 0 for Pending/Rejected returns.")
        
    approved = val_df[val_df['Return_Status'] == 'Approved']
    if not np.isclose(approved['Refund_Amount'], approved['Final_Item_Price'], atol=0.01).all():
        errors.append("Refund_Amount does not exactly match Final_Item_Price for Approved returns.")
        
    # Return_Date sequence check
    val_dates = returns[['Order_ID', 'Return_Date']].merge(orders[['Order_ID', 'Order_Timestamp']], on='Order_ID')
    if (pd.to_datetime(val_dates['Return_Date']) < pd.to_datetime(val_dates['Order_Timestamp'])).any():
        errors.append("Return_Date is earlier than Order_Timestamp.")
        
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
    
    config = load_json('master_returns_v1.json')
    orders, details = load_data()
    
    print("Generating Returns...")
    returns_df = generate_returns(orders, details, config)
    
    validate_returns(returns_df, orders, details)
    
    print("\nSaving to returns.csv...")
    returns_df.to_csv("returns.csv", index=False)
    print("[✓] returns.csv has been successfully generated.")
    
    elapsed_time = time.time() - start_time
    
    # Summary Metrics Calculation
    total_returns = len(returns_df)
    total_details = len(details)
    return_rate = (total_returns / total_details) * 100 if total_details > 0 else 0
    
    status_counts = returns_df['Return_Status'].value_counts(normalize=True) * 100
    approved_pct = status_counts.get('Approved', 0)
    rejected_pct = status_counts.get('Rejected', 0)
    pending_pct = status_counts.get('Pending', 0)
    
    avg_refund = returns_df['Refund_Amount'].mean()
    total_refund = returns_df['Refund_Amount'].sum()
    top_reasons = returns_df['Return_Reason'].value_counts().head(3)
    
    # Summary Metrics Print
    print("\n--- SUMMARY METRICS ---")
    print(f"Total Returns:            {total_returns:,}")
    print(f"Overall Return Rate:      {return_rate:.2f}% (of all order details)")
    print(f"Approved Returns:         {approved_pct:.2f}%")
    print(f"Rejected Returns:         {rejected_pct:.2f}%")
    print(f"Pending Returns:          {pending_pct:.2f}%")
    print(f"Average Refund Amount:    ₹{avg_refund:.2f}")
    print(f"Total Refund Amount:      ₹{total_refund:,.2f}")
    print("\nTop Return Reasons:")
    for reason, count in top_reasons.items():
        print(f"  - {reason}: {count:,}")
    print(f"\nGeneration Time:          {elapsed_time:.2f} seconds")

if __name__ == "__main__":
    main()