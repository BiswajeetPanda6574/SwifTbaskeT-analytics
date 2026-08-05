# SwiftBasket — Quick-Commerce SQL Analytics

SwiftBasket is a **quick-commerce analytics project** inspired by platforms like Zepto. It uses synthetic data generated with **Python**, a **PostgreSQL** database, and business-oriented **SQL analysis** to explore customers, orders, products, inventory, deliveries, and returns.

## Project Overview

The project consists of **8 interconnected datasets**:

- Products
- Customers
- Dark Stores
- Orders
- Order Details
- Riders
- Inventory
- Returns

The datasets were generated using **Python and AI-assisted prompt design** with business rules to simulate a realistic quick-commerce environment.

> The full Orders and Order Details datasets contain hundreds of thousands of rows. Sample versions are included in this repository due to file-size limitations.

## SQL Analysis

The project contains **50 business SQL problems across 10 modules**.

**Current Progress:** 40/50 queries completed across 8/10 modules.

SQL concepts used include:

- Multi-table Joins
- CTEs
- Window Functions
- Aggregations
- Subqueries
- Conditional Logic
- Customer, Inventory & Logistics Analysis

Each SQL file contains the **business question followed by its SQL solution**.

## Project Structure

```text
SwiftBaskeT-analytics/
│
├── data/                 # CSV datasets
├── data_generation/      # Python & JSON generation files
├── sql/                  # Business SQL problems
├── PROJECT_PROGRESS.md
└── README.md
```

## Tech Stack

**Python | PostgreSQL | SQL | Pandas | GitHub**

## Key Highlights

- Built an **8-table quick-commerce dataset** using Python.
- Worked with transactional datasets containing **hundreds of thousands of records**.
- Designed and loaded the data into **PostgreSQL** for analysis.
- Created **50 business-oriented SQL problems** covering multiple areas of quick-commerce.
- Applied **Joins, CTEs, Window Functions and Aggregations** for business analysis.

## Project Status

🚧 **In Development**

- ✅ Data generation completed
- ✅ PostgreSQL database setup
- ✅ SQL Modules 1–8 completed
- 🔄 SQL Modules 9–10 in progress
- 📊 Power BI dashboard planned
