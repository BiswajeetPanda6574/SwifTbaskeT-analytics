-- Customer Repeat Purchase Rate(What % of customers have made more than one purchase)

WITH product_revenue AS (
    SELECT
        p.category,
        p.product_id,
        p.product_name,
        SUM(od.final_item_price) AS product_revenue
    FROM swiftbasket.products p
    JOIN swiftbasket.order_details od
        ON p.product_id = od.product_id
    GROUP BY
        p.category,
        p.product_id,
        p.product_name
),

revenue_comparison AS (
    SELECT
        category,
        product_id,
        product_name,
        product_revenue,

        AVG(product_revenue) OVER (
            PARTITION BY category
        ) AS category_avg_revenue

    FROM product_revenue
)

SELECT
    category,
    product_id,
    product_name,
    ROUND(product_revenue, 2) AS product_revenue,
    ROUND(category_avg_revenue, 2) AS category_avg_revenue,
    ROUND(product_revenue - category_avg_revenue, 2) AS difference_from_average

FROM revenue_comparison

WHERE product_revenue < category_avg_revenue

ORDER BY
    category,
    product_revenue ASC;