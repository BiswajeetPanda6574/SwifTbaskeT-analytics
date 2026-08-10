-- Dark stores whose revenue is growing or declining month over month (Dark Store Revenue Growth)

WITH monthly_store_revenue AS (
    SELECT
        DATE_TRUNC('month', o.order_timestamp) AS month,
        ds.store_id,
        ds.store_name,
        SUM(o.total_order_value) AS monthly_revenue

    FROM swiftbasket.orders o

    JOIN swiftbasket.dark_stores ds
        ON o.store_id = ds.store_id

    GROUP BY
        DATE_TRUNC('month', o.order_timestamp),
        ds.store_id,
        ds.store_name
),

store_growth AS (
    SELECT
        month,
        store_id,
        store_name,
        monthly_revenue,

        LAG(monthly_revenue) OVER (
            PARTITION BY store_id
            ORDER BY month
        ) AS previous_month_revenue

    FROM monthly_store_revenue
)

SELECT
    month,
    store_name,
    monthly_revenue,
    previous_month_revenue,

    ROUND(
        (monthly_revenue - previous_month_revenue)
        * 100.0
        / NULLIF(previous_month_revenue, 0),
        2
    ) AS mom_growth_percentage

FROM store_growth

ORDER BY store_name,
    	 month;