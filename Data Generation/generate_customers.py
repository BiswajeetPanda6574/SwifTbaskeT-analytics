import json
import random
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from faker import Faker

# ==========================================================
# CONFIGURATION & INITIALIZATION
# ==========================================================
SEED = 42
random.seed(SEED)
np.random.seed(SEED)
fake = Faker('en_IN')
Faker.seed(SEED)

JSON_FILE = 'master_customers_v1.json'
OUTPUT_FILE = 'customers.csv'
TARGET_CUSTOMERS = 15000

# Date constraints
PROJECT_START = datetime(2025, 4, 1)
PROJECT_END = datetime(2025, 9, 30)

# ==========================================================
# HELPER FUNCTIONS
# ==========================================================
def parse_age_range(age_str):
    """Parses age string formats like '18-22' or '31-51+' and returns min, max"""
    age_str = age_str.replace('+', '')
    parts = age_str.split('-')
    if len(parts) == 1:
        return int(parts[0]), 60 # Assume 60 as a safe upper bound for open-ended
    return int(parts[0]), int(parts[1])

def generate_random_date(start_date, end_date):
    """Generates a random datetime between start and end dates."""
    time_between_dates = end_date - start_date
    days_between_dates = time_between_dates.days
    if days_between_dates <= 0:
        return start_date
    random_number_of_days = random.randrange(days_between_dates)
    return start_date + timedelta(days=random_number_of_days)

def load_json(filepath):
    """Loads the master configuration JSON."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

# ==========================================================
# MAIN GENERATOR FUNCTION
# ==========================================================
def generate_customers(config, num_customers):
    customers = []
    
    # 1. Pre-calculate distributions from JSON
    # Personas
    personas = config['personas']
    persona_names = [p['persona_name'] for p in personas]
    persona_weights = [p['distribution_percentage'] for p in personas]
    
    # Global Payment Methods
    payment_methods = list(config['payment_methods'].keys())
    payment_weights = list(config['payment_methods'].values())
    
    # Memberships
    memberships = list(config['memberships'].keys())
    membership_weights = list(config['memberships'].values())
    
    # Customer Status
    statuses = list(config['customer_status'].keys())
    status_weights = list(config['customer_status'].values())
    
    # Areas & Pincodes
    areas_data = config['areas']
    
    # 2. Generate records row by row
    print(f"Generating {num_customers} customers. Please wait...")
    
    name_counts = {}
    name_locations = set()
    
    residential_map = {
        "Student": ["Hostel", "PG", "Apartment"],
        "Working Professional": ["Apartment", "Gated Community", "Independent House"],
        "Parent": ["Apartment", "Villa", "Independent House", "Gated Community"],
        "Grocery Planner": ["Apartment", "Independent House"],
        "Fitness Enthusiast": ["Apartment", "Gated Community"],
        "Sick Day Customer": ["Apartment", "Independent House", "PG", "Gated Community"],
        "Host / Party Buyer": ["Apartment", "Villa", "Gated Community"]
    }
    
    for i in range(1, num_customers + 1):
        # Primary Key
        customer_id = f"C{i:06d}"
        
        # Location Details
        area_obj = random.choice(areas_data)
        area = area_obj['name']
        pincode = area_obj['pincode']
        city = config['cities'][0]
        
        # Gender & Name Generation with Uniqueness Rules
        while True:
            gender = random.choice(['Male', 'Female'])
            if gender == 'Male':
                name = f"{fake.first_name_male()} {fake.last_name()}"
            else:
                name = f"{fake.first_name_female()} {fake.last_name()}"
            
            name_count = name_counts.get(name, 0)
            location_key = (name, area, pincode)
            
            # Ensure name appears max 3 times total, and never in the same location twice
            if name_count < 3 and location_key not in name_locations:
                name_counts[name] = name_count + 1
                name_locations.add(location_key)
                break
        
        # Persona Assignment
        persona = random.choices(personas, weights=persona_weights, k=1)[0]
        
        # Age
        min_age, max_age = parse_age_range(persona['age_range'])
        age = random.randint(min_age, max_age)
        
        # Occupation
        occupation = random.choice(persona['occupations'])
        
        # Monthly Income (Rounded to nearest 500)
        income_min, income_max = persona['monthly_income_range']['min'], persona['monthly_income_range']['max']
        raw_income = random.uniform(income_min, income_max)
        monthly_income = int(round(raw_income / 500) * 500)
        
        # Residential Type mapped to Persona
        residential_type = random.choice(residential_map.get(persona['persona_name'], config['residential_types']))
        
        # Payment Method & Membership (Using persona preferred for payment, global for membership)
        payment_method = random.choice(persona['preferred_payment_methods'])
        membership = random.choices(memberships, weights=membership_weights, k=1)[0]
        customer_status = random.choices(statuses, weights=status_weights, k=1)[0]
        
        # Dates Logic
        # Rule: Reg Date must allow a Last Order Date inside the Project Window. 
        # Capping Reg Date at Sep 29, 2025 so at least 1 day remains for order.
        reg_start = datetime(2024, 4, 1)
        reg_end = datetime(2025, 9, 29) 
        registration_date = generate_random_date(reg_start, reg_end)
        
        # Last Order Date: Must be AFTER registration AND within Project Duration (Apr '25 - Sep '25)
        # If registration is before Apr '25, order can be anywhere in Apr-Sep '25.
        # If registration is during Apr-Sep '25, order must be after registration.
        last_order_start = max(registration_date + timedelta(days=1), PROJECT_START)
        last_order_date = generate_random_date(last_order_start, PROJECT_END)
        
        # Purchasing Behaviours
        preferred_category = random.choice(persona['preferred_categories'])
        preferred_time = persona['preferred_order_time']
        
        # Average Basket Value (Rounded to nearest 10)
        abv_min, abv_max = persona['average_basket_value']['min'], persona['average_basket_value']['max']
        raw_abv = random.uniform(abv_min, abv_max)
        avg_basket_value = int(round(raw_abv / 10) * 10)
        
        # Average Orders Per Month
        ord_min, ord_max = persona['average_orders_per_month']['min'], persona['average_orders_per_month']['max']
        avg_orders_per_month = random.randint(ord_min, ord_max)
        
        # Tenure Calculations
        tenure_days = (last_order_date - registration_date).days
        tenure_months = max(1, tenure_days / 30.0)
        
        # Lifetime Value Calculation
        # LTV = Base Spend + Random Variance. Bound by JSON global rules.
        calculated_ltv = int(tenure_months * avg_orders_per_month * avg_basket_value)
        ltv_bounds = config['global_rules']['lifetime_value_ranges'].get(persona['persona_name'], {"min": avg_basket_value, "max": 250000})
        
        # Ensure older active customers naturally hit higher LTV bounds by skewing based on tenure
        ltv_multiplier = min(1.5, 1.0 + (tenure_months / 24))
        lifetime_value = int(calculated_ltv * ltv_multiplier)
        
        # Clamp to bounds and guarantee LTV >= ABV
        lifetime_value = max(lifetime_value, ltv_bounds['min'], avg_basket_value)
        lifetime_value = min(lifetime_value, ltv_bounds['max'])
        
        # Loyalty Score Calculation (0-100)
        # Weights: Frequency (30%), ABV (20%), Tenure (20%), Membership (15%), Status (15%)
        freq_score = min(30, (avg_orders_per_month / 20) * 30)
        abv_score = min(20, (avg_basket_value / 3000) * 20)
        tenure_score = min(20, (tenure_months / 18) * 20)
        member_score = 15 if membership == 'Quick Pass' else 0
        status_score = 15 if customer_status == 'Active' else 0
        
        loyalty_score = int(freq_score + abv_score + tenure_score + member_score + status_score)
        
        # COD Eligibility
        if customer_status == 'Blocked':
            cod_eligible = False
        else:
            # Small percentage (5%) of non-blocked users lose COD due to repeated refusals
            cod_eligible = False if random.random() < 0.05 else True

        # Append to dataset
        customers.append({
            "Customer_ID": customer_id,
            "Customer_Name": name,
            "Gender": gender,
            "Age": age,
            "Age_Group": persona['age_range'],
            "Customer_Persona": persona['persona_name'],
            "Occupation": occupation,
            "Monthly_Income": monthly_income,
            "City": city,
            "Area": area,
            "Pincode": pincode,
            "Residential_Type": residential_type,
            "Preferred_Payment_Method": payment_method,
            "Membership": membership,
            "Registration_Date": registration_date.strftime('%Y-%m-%d'),
            "Last_Order_Date": last_order_date.strftime('%Y-%m-%d'),
            "Preferred_Order_Time": preferred_time,
            "Preferred_Category": preferred_category,
            "Average_Basket_Value": avg_basket_value,
            "Average_Orders_Per_Month": avg_orders_per_month,
            "Lifetime_Value": lifetime_value,
            "Loyalty_Score": loyalty_score,
            "COD_Eligible": cod_eligible,
            "Customer_Status": customer_status
        })
        
    return pd.DataFrame(customers)

# ==========================================================
# VALIDATION
# ==========================================================
def validate_data(df):
    print("\n--- Running Data Validations ---")
    
    # 1. Primary Key Uniqueness
    assert df['Customer_ID'].nunique() == len(df), "ERROR: Duplicate Customer IDs found."
    
    # 2. No Null Values
    assert df.isnull().sum().sum() == 0, "ERROR: Null values found in dataset."
    
    # 3. Date Logic Causality
    df['Reg_Date_dt'] = pd.to_datetime(df['Registration_Date'])
    df['Last_Order_dt'] = pd.to_datetime(df['Last_Order_Date'])
    invalid_dates = df[df['Reg_Date_dt'] >= df['Last_Order_dt']]
    assert len(invalid_dates) == 0, "ERROR: Found records where Last Order Date is before/on Registration Date."
    
    # 4. LTV Sanity
    invalid_ltv = df[df['Lifetime_Value'] < df['Average_Basket_Value']]
    assert len(invalid_ltv) == 0, "ERROR: Found records where LTV is less than Average Basket Value."
    
    # 5. Loyalty Score Bounds
    assert df['Loyalty_Score'].between(0, 100).all(), "ERROR: Loyalty Score out of bounds (0-100)."
    
    print("✓ All Validations Passed Successfully.")
    
    # Cleanup temp datetime columns used for validation
    df = df.drop(columns=['Reg_Date_dt', 'Last_Order_dt'])
    return df

# ==========================================================
# EXECUTION & EXPORT
# ==========================================================
if __name__ == "__main__":
    # Load JSON Configurations
    config = load_json(JSON_FILE)
    
    # Generate Data
    df_customers = generate_customers(config, TARGET_CUSTOMERS)
    
    # Validate
    df_customers = validate_data(df_customers)
    
    # Export
    df_customers.to_csv(OUTPUT_FILE, index=False, encoding='utf-8')
    print(f"\nSuccessfully generated and saved {TARGET_CUSTOMERS} records to {OUTPUT_FILE}")
    
    # ==========================================================
    # SUMMARY PRINT
    # ==========================================================
    print("\n" + "="*50)
    print(" DATA GENERATION SUMMARY")
    print("="*50)
    print(f"Total Customers            : {len(df_customers)}")
    print("\nGender Distribution:")
    print(df_customers['Gender'].value_counts(normalize=True).mul(100).round(1).astype(str) + '%')
    
    print("\nPersona Distribution:")
    print(df_customers['Customer_Persona'].value_counts(normalize=True).mul(100).round(1).astype(str) + '%')
    
    print("\nPayment Distribution:")
    print(df_customers['Preferred_Payment_Method'].value_counts(normalize=True).mul(100).round(1).astype(str) + '%')
    
    print("\nMembership Distribution:")
    print(df_customers['Membership'].value_counts(normalize=True).mul(100).round(1).astype(str) + '%')
    
    print("\nTop 5 Area Distribution:")
    print(df_customers['Area'].value_counts().head(5))
    
    print("\nAverages:")
    print(f"Average Income             : ₹{df_customers['Monthly_Income'].mean():,.2f}")
    print(f"Average Basket Value       : ₹{df_customers['Average_Basket_Value'].mean():,.2f}")
    print(f"Average Lifetime Value     : ₹{df_customers['Lifetime_Value'].mean():,.2f}")
    print(f"Average Loyalty Score      : {df_customers['Loyalty_Score'].mean():.1f} / 100")
    
    print("\nQuality Checks:")
    print(f"Null Count                 : {df_customers.isnull().sum().sum()}")
    print(f"Duplicate Customer IDs     : {df_customers.duplicated(subset=['Customer_ID']).sum()}")
    print("="*50)