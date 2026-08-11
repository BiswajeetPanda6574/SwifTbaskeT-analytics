-- For each product category, what percentage of customers have purchased from that category more than once?(Category Repeat Purchase Rate)

WITH category_customers AS (
    SELECT
        p.category,
        COUNT(DISTINCT o.customer_id) AS unique_customers,
        SUM(od.final_item_price) AS total_revenue

    FROM swiftbasket.order_details od

    JOIN swiftbasket.orders o
        ON od.order_id = o.order_id

    JOIN swiftbasket.products p
        ON od.product_id = p.product_id

    GROUP BY
        p.category
),

customer_base AS (
    SELECT
        COUNT(DISTINCT customer_id) AS total_customers
    FROM swiftbasket.orders
)

SELECT
    cc.category,
    cc.unique_customers,
    cb.total_customers,

    ROUND(
        cc.unique_customers * 100.0
        / NULLIF(cb.total_customers, 0),
        2
    ) AS customer_penetration_percentage,

    ROUND(cc.total_revenue, 2) AS total_revenue

FROM category_customers cc

CROSS JOIN customer_base cb

ORDER BY
    customer_penetration_percentage DESC;