import pandas as pd
import numpy as np
import json
import random
from datetime import datetime, timedelta
import time

def load_json(filepath: str) -> dict:
    with open(filepath, 'r') as f:
        return json.load(f)

def load_csvs():
    try:
        customers = pd.read_csv('customers.csv')
        stores = pd.read_csv('darkstores.csv')
        riders = pd.read_csv('riders.csv')
        return customers, stores, riders
    except FileNotFoundError as e:
        raise FileNotFoundError(f"Missing required input file: {e}")

def validate_inputs(customers: pd.DataFrame, stores: pd.DataFrame, riders: pd.DataFrame, config: dict):
    if 'Customer_ID' not in customers.columns:
        raise ValueError("customers.csv missing 'Customer_ID' column.")
    if 'Store_ID' not in stores.columns:
        raise ValueError("darkstores.csv missing 'Store_ID' column.")
    if 'Rider_ID' not in riders.columns or 'Store_ID' not in riders.columns or 'Rider_Status' not in riders.columns:
        raise ValueError("riders.csv missing required columns ('Rider_ID', 'Store_ID', 'Rider_Status').")
    
    active_riders = riders[riders['Rider_Status'] == 'Active']
    if active_riders.empty:
        raise ValueError("No active riders found in riders.csv.")

def generate_order_timestamps_and_slots(config: dict, n: int):
    start_date = datetime.strptime(config['metadata']['simulation_period']['start_date'], "%Y-%m-%d")
    end_date = datetime.strptime(config['metadata']['simulation_period']['end_date'], "%Y-%m-%d")
    
    date_range = (end_date - start_date).days + 1
    
    # Read frequency rules from JSON
    freq_rules = config.get('order_frequency_rules', {})
    wkday_mult = freq_rules.get('weekday_multiplier', 1.0)
    wkend_mult = freq_rules.get('weekend_multiplier', 1.25)
    peak_mult = freq_rules.get('peak_hour_multiplier', 1.6)
    fest_mult = freq_rules.get('festival_multiplier', 1.4)
    
    days = list(range(date_range))
    day_weights = []
        
    for d in days:
        current_date = start_date + timedelta(days=d)
        weight = wkend_mult if current_date.weekday() >= 5 else wkday_mult
        
        # Stochastically apply festival multiplier to roughly 8% of days based on rules
        if np.random.rand() < 0.08:
            weight *= fest_mult
            
        day_weights.append(weight)
        
    day_probs = np.array(day_weights) / sum(day_weights)
    
    hour_weights = {6: 0.02, 7: 0.03, 8: 0.04, 9: 0.05, 10: 0.05, 11: 0.05, 12: 0.06, 13: 0.09, 14: 0.08, 15: 0.03, 16: 0.03, 17: 0.04, 18: 0.08, 19: 0.10, 20: 0.11, 21: 0.08, 22: 0.05, 23: 0.04}

    peak_hours_list = [12, 13, 14, 18, 19, 20, 21]
    
    hours = list(hour_weights.keys())
    adjusted_hour_weights = []
    
    for h in hours:
        w = hour_weights[h]
        if h in peak_hours_list:
            w *= peak_mult
        adjusted_hour_weights.append(w)
        
    hour_probs = np.array(adjusted_hour_weights) / sum(adjusted_hour_weights)
    
    random_days = np.random.choice(days, n, p=day_probs)
    random_hours = np.random.choice(hours, n, p=hour_probs)
    random_minutes = np.random.randint(0, 60, n)
    random_seconds = np.random.randint(0, 60, n)
    
    timestamps = []
    slots = []
    peak_hours = []
    
    for i in range(n):
    	dt = start_date + timedelta(
            days=int(random_days[i]),
            hours=int(random_hours[i]),
            minutes=int(random_minutes[i]),
            seconds=int(random_seconds[i])
    	)

    	if dt > end_date.replace(hour=23, minute=59, second=59):
            dt = end_date.replace(hour=23, minute=59, second=59)

    	timestamps.append(dt)

    	slot_start = dt.replace(minute=0, second=0, microsecond=0)
    	slot_end = slot_start + timedelta(hours=1)
    	slots.append(f"{slot_start.strftime('%I:%M %p')} - {slot_end.strftime('%I:%M %p')}")

    	is_peak = "Yes" if int(random_hours[i]) in peak_hours_list else "No"
    	peak_hours.append(is_peak)
        
    records = sorted(
        zip(timestamps, slots, peak_hours),
        key=lambda x: x[0]
    )
    
    timestamps, slots, peak_hours = map(np.array, zip(*records))
    
    return timestamps, slots, peak_hours

def assign_customer(customers: pd.DataFrame, n: int):
    customer_ids = customers['Customer_ID'].values
    return np.random.choice(customer_ids, n)

def assign_store_and_rider(stores: pd.DataFrame, riders: pd.DataFrame, n: int):
    active_riders = riders[riders['Rider_Status'] == 'Active']
    
    store_riders_map = active_riders.groupby('Store_ID')['Rider_ID'].apply(list).to_dict()
    valid_stores = [s for s in stores['Store_ID'].values if s in store_riders_map and len(store_riders_map[s]) > 0]
    
    if not valid_stores:
        raise ValueError("No valid stores with active riders.")
        
    assigned_stores = np.random.choice(valid_stores, n)
    
    assigned_riders = []
    for store in assigned_stores:
        assigned_riders.append(random.choice(store_riders_map[store]))
        
    return assigned_stores, np.array(assigned_riders)

def generate_weather(config: dict, timestamps: np.ndarray):
    monthly_weather = config["weather_rules"]["monthly_weather"]

    weather = []
    daily_weather = {}

    for ts in timestamps:
        date_key = ts.date()

        if date_key not in daily_weather:

            month = ts.strftime("%m")

            if month not in monthly_weather:
                month = "09"

            month_dist = monthly_weather[month]

            conditions = [
                "Clear",
                "Cloudy",
                "Rain",
                "Heavy Rain"
            ]

            probs = [
                month_dist["clear_day"],
                month_dist["cloudy_day"],
                month_dist["rain_day"],
                month_dist["heavy_rain_day"]
            ]

            daily_weather[date_key] = np.random.choice(
                conditions,
                p=probs
            )

        weather.append(daily_weather[date_key])

    return np.array(weather)

def generate_festivals(config: dict, n: int):
    fest_flags = config['festival_rules']['flags']
    return np.random.choice(list(fest_flags.keys()), n, p=list(fest_flags.values()))

def generate_order_source(config: dict, n: int):
    src_dist = config['order_source_rules']['distribution']
    return np.random.choice(list(src_dist.keys()), n, p=list(src_dist.values()))

def generate_status(config: dict, n: int):
    status_dist = config['order_status_rules']['distribution']
    statuses = np.random.choice(list(status_dist.keys()), n, p=list(status_dist.values()))
    
    reasons_list = config['order_status_rules']['cancellation_reasons']
    reasons = np.where(
        statuses == 'Cancelled', 
        np.random.choice(reasons_list, n), 
        None
    )
    return statuses, reasons

def generate_payment(config: dict, statuses: np.ndarray, n: int):
    methods_dist = config['payment_rules']['methods_distribution']
    methods = np.random.choice(list(methods_dist.keys()), n, p=list(methods_dist.values()))
    
    payment_statuses = np.empty(n, dtype=object)
    
    for i in range(n):
        if statuses[i] == 'Delivered':
            payment_statuses[i] = 'Paid'
        elif statuses[i] == 'Cancelled':
            if methods[i] == 'Cash on Delivery':
                payment_statuses[i] = 'Pending'
            else:
                payment_statuses[i] = random.choice(['Refunded', 'Pending'])
        else:
            if methods[i] == 'Cash on Delivery':
                payment_statuses[i] = 'Pending'
            else:
                payment_statuses[i] = 'Refunded'
                
    return methods, payment_statuses

def generate_distance(config: dict, n: int):
    dist_config = config['delivery_rules']['distance_km']
    min_dist = dist_config['min']
    max_dist = dist_config['max']
    mean_dist = dist_config['mean']
    
    scale = mean_dist - min_dist
    distances = np.random.exponential(scale, n) + min_dist
    distances = np.clip(distances, min_dist, max_dist)
    return np.round(distances, 2)

def generate_delivery_time(config: dict, distances: np.ndarray, weather: np.ndarray, peak: np.ndarray, festivals: np.ndarray, n: int):
    est_config = config['delivery_rules']['estimated_time_mins']
    act_config = config['delivery_rules']['actual_time_mins']
    weather_impact = config['weather_rules']['impact']
    fest_impact = config['festival_rules']['impact']
    
    est_times = np.zeros(n)
    act_times = np.zeros(n)
    
    for i in range(n):
        base_est = 10 + (distances[i] * 2.5)
        weather_mult = weather_impact.get(weather[i], {}).get('actual_time_multiplier', 1.0)
        peak_add = 5 if peak[i] == 'Yes' else 0
        fest_add = fest_impact.get('Yes', {}).get('actual_time_penalty_mins', 0) if festivals[i] == 'Yes' else 0
        
        est = base_est * weather_mult
        if peak[i] == 'Yes' or festivals[i] == 'Yes':
            est += peak_add + fest_add
            
        est = max(est_config['min'], min(est_config['max'], est))
        est_times[i] = est
        
        act = np.random.normal(est, 3)
        act = act * weather_mult
        act += peak_add + fest_add
        act = max(act_config['min'], min(act_config['max'], act))
        act_times[i] = act
        
    return np.round(est_times).astype(int), np.round(act_times).astype(int)

def generate_delivery_fee(config: dict, distances: np.ndarray, weather: np.ndarray, peak: np.ndarray, n: int):
    fee_config = config['delivery_rules']['delivery_fee']
    weather_impact = config['weather_rules']['impact']
    threshold = fee_config['base_free_threshold_km']
    rate = fee_config['rate_per_km_above_threshold']
    
    fees = np.zeros(n)
    for i in range(n):
        base_fee = 0 if distances[i] <= threshold else (distances[i] - threshold) * rate
        surge = weather_impact.get(weather[i], {}).get('surge_fee', 0.0)
        peak_surge = 10.0 if peak[i] == 'Yes' else 0.0
        fees[i] = base_fee + surge + peak_surge
        
    return np.round(fees, 2)

def generate_coupon(config: dict, n: int):
    coupon_config = config['coupon_rules']
    prob = coupon_config['probability']
    min_disc = coupon_config['discount_range_inr']['min']
    max_disc = coupon_config['discount_range_inr']['max']
    
    has_coupon = np.random.choice([True, False], n, p=[prob, 1 - prob])
    discounts = np.where(has_coupon, np.random.uniform(min_disc, max_disc, n), 0.0)
    return np.round(discounts, 2)

def generate_total_order_value(n: int, fees: np.ndarray, coupons: np.ndarray, festivals: np.ndarray, config: dict):
    base_baskets = np.random.lognormal(mean=np.log(350), sigma=0.5, size=n)
    base_baskets = np.clip(base_baskets, 100, 3000)
    
    fest_impact = config['festival_rules']['impact']
    
    total_values = np.zeros(n)
    final_coupons = np.zeros(n)
    
    for i in range(n):
        basket = base_baskets[i]
        if festivals[i] == 'Yes':
            basket *= fest_impact['Yes']['average_basket_multiplier']
            
        max_coupon = basket * 0.40
        discount = min(coupons[i], max_coupon)
        
        if basket + fees[i] - discount <= 0:
            discount = 0
            
        final_coupons[i] = discount
        total_values[i] = basket + fees[i] - discount
        
    return np.round(total_values, 2), np.round(final_coupons, 2)

def generate_rating(config: dict, statuses: np.ndarray, est_times: np.ndarray, act_times: np.ndarray, weather: np.ndarray, n: int):
    rating_dist = config['rating_rules']['distribution']
    choices = [int(k) for k in rating_dist.keys()]
    probs = list(rating_dist.values())
    
    base_ratings = np.random.choice(choices, n, p=probs)
    final_ratings = np.empty(n, dtype=object)
    
    for i in range(n):
        if statuses[i] in ['Cancelled', 'Failed']:
            final_ratings[i] = None
            continue
            
        r = base_ratings[i]
        
        if act_times[i] > (est_times[i] + 15):
            r = min(r, 3)
            
        if weather[i] == 'Heavy Rain' and act_times[i] <= est_times[i]:
            r = max(r, 4)
            
        final_ratings[i] = r
        
    return final_ratings

def validate_orders(df: pd.DataFrame, customers: pd.DataFrame, stores: pd.DataFrame, riders: pd.DataFrame):
    if df.duplicated().any():
        raise AssertionError("Validation Failed: Completely duplicated rows found.")
        
    if df['Order_ID'].duplicated().any():
        raise AssertionError("Validation Failed: Duplicate Order_IDs found.")
        
    if not df['Customer_ID'].isin(customers['Customer_ID']).all():
        raise AssertionError("Validation Failed: Invalid Customer_IDs found.")
        
    if not df['Store_ID'].isin(stores['Store_ID']).all():
        raise AssertionError("Validation Failed: Invalid Store_IDs found.")
        
    if not df['Rider_ID'].isin(riders['Rider_ID']).all():
        raise AssertionError("Validation Failed: Invalid Rider_IDs found.")
        
    active_riders = riders[riders['Rider_Status'] == 'Active']
    merged_rider_store = df[['Rider_ID', 'Store_ID']].merge(active_riders[['Rider_ID', 'Store_ID']], on='Rider_ID', suffixes=('', '_rider'))
    if not (merged_rider_store['Store_ID'] == merged_rider_store['Store_ID_rider']).all():
        raise AssertionError("Validation Failed: Rider assigned to incorrect store.")
        
    if (df['Total_Order_Value'] < 0).any() or (df['Delivery_Fee'] < 0).any() or (df['Coupon_Discount'] < 0).any() or (df['Delivery_Distance_km'] < 0).any():
        raise AssertionError("Validation Failed: Negative monetary or distance values found.")
        
    if df[df['Order_Status'] == 'Delivered']['Cancellation_Reason'].notnull().any():
        raise AssertionError("Validation Failed: Delivered orders have cancellation reasons.")
        
    if df[df['Order_Status'].isin(['Cancelled', 'Failed'])]['Customer_Delivery_Rating'].notnull().any():
        raise AssertionError("Validation Failed: Cancelled/Failed orders have delivery ratings.")

    if not df['Estimated_Delivery_Time'].between(10, 30).all():
        raise AssertionError("Validation Failed: Estimated delivery time out of bounds.")

    if not df['Actual_Delivery_Time'].between(8, 45).all():
        raise AssertionError("Validation Failed: Actual delivery time out of bounds.")
        
    mandatory = ['Order_ID', 'Customer_ID', 'Store_ID', 'Rider_ID', 'Order_Timestamp', 'Total_Order_Value']
    if df[mandatory].isnull().any().any():
        raise AssertionError("Validation Failed: Missing values in mandatory fields.")

def save_orders(df: pd.DataFrame):
    df.to_csv('orders.csv', index=False)

def main():
    start_time = time.time()
    
    random.seed(42)
    np.random.seed(42)
    
    config = load_json('master_orders_v1.json')
    n = config['metadata']['target_orders']
    id_format = config['global_rules']['id_format']
    cols = config['global_rules']['columns']
    
    customers, stores, riders = load_csvs()
    validate_inputs(customers, stores, riders, config)
    
    order_ids = [id_format.format(index=i+1) for i in range(n)]
    
    timestamps, slots, peak_hours = generate_order_timestamps_and_slots(config, n)
    
    customer_ids = assign_customer(customers, n)
    store_ids, rider_ids = assign_store_and_rider(stores, riders, n)
    
    weather = generate_weather(config, timestamps)
    festivals = generate_festivals(config, n)
    order_source = generate_order_source(config, n)
    
    statuses, cancellation_reasons = generate_status(config, n)
    payment_methods, payment_statuses = generate_payment(config, statuses, n)
    
    distances = generate_distance(config, n)
    est_times, act_times = generate_delivery_time(config, distances, weather, peak_hours, festivals, n)
    fees = generate_delivery_fee(config, distances, weather, peak_hours, n)
    
    raw_coupons = generate_coupon(config, n)
    total_values, final_coupons = generate_total_order_value(n, fees, raw_coupons, festivals, config)
    
    ratings = generate_rating(config, statuses, est_times, act_times, weather, n)
    
    df = pd.DataFrame({
        'Order_ID': order_ids,
        'Customer_ID': customer_ids,
        'Store_ID': store_ids,
        'Rider_ID': rider_ids,
        'Order_Timestamp': timestamps,
        'Delivery_Slot': slots,
        'Payment_Method': payment_methods,
        'Payment_Status': payment_statuses,
        'Order_Status': statuses,
        'Cancellation_Reason': cancellation_reasons,
        'Delivery_Fee': fees,
        'Coupon_Discount': final_coupons,
        'Estimated_Delivery_Time': est_times,
        'Actual_Delivery_Time': act_times,
        'Delivery_Distance_km': distances,
        'Total_Order_Value': total_values,
        'Weather_Condition': weather,
        'Peak_Hour': peak_hours,
        'Festival_Flag': festivals,
        'Order_Source': order_source,
        'Customer_Delivery_Rating': ratings
    })
    
    df = df[cols]
    
    validate_orders(df, customers, stores, riders)
    
    save_orders(df)
    
    elapsed_time = time.time() - start_time
    
    print(f"Total Orders: {len(df)}")
    print(f"Delivered: {len(df[df['Order_Status'] == 'Delivered'])}")
    print(f"Cancelled: {len(df[df['Order_Status'] == 'Cancelled'])}")
    print(f"Failed: {len(df[df['Order_Status'] == 'Failed'])}")
    print(f"Average Delivery Time: {df['Actual_Delivery_Time'].mean():.2f}")
    print(f"Average Order Value: {df['Total_Order_Value'].mean():.2f}")
    print(f"Average Delivery Fee: {df['Delivery_Fee'].mean():.2f}")
    print(f"Average Rating: {df['Customer_Delivery_Rating'].dropna().mean():.2f}")
    print("\nOrders per Store:\n", df['Store_ID'].value_counts().to_string())
    print("\nOrders per Payment Method:\n", df['Payment_Method'].value_counts().to_string())
    print("\nOrders per Status:\n", df['Order_Status'].value_counts().to_string())
    print("\nOrders per Weather:\n", df['Weather_Condition'].value_counts().to_string())
    print("\nOrders per Source:\n", df['Order_Source'].value_counts().to_string())
    print(f"\nGeneration Time: {elapsed_time:.2f} seconds")

if __name__ == "__main__":
    main()