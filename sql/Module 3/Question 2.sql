-- Find the cumulative(running total) revenue month by month.

WITH monthly_sales AS
(
    SELECT
        DATE_TRUNC('month', order_timestamp) AS month,
        SUM(total_order_value) AS monthly_revenue
    FROM swiftbasket.orders
    GROUP BY DATE_TRUNC('month', order_timestamp)
)

SELECT
    TO_CHAR(month, 'Mon YYYY') AS month,
    monthly_revenue,
    SUM(monthly_revenue)
        OVER(ORDER BY month) AS running_total_revenue
FROM monthly_sales
ORDER BY monthly_sales.month;