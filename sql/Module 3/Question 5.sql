-- Which products contribute to 80% of our Total Revenue? {Pareto Analysis(80/20 Rule)}

WITH product_revenue AS
(
    SELECT
        p.product_id,
        p.product_name,
        SUM(od.final_item_price) AS revenue
    FROM swiftbasket.products p
    JOIN swiftbasket.order_details od
        ON p.product_id = od.product_id
    GROUP BY
        p.product_id,
        p.product_name
),

revenue_analysis AS
(
    SELECT
        product_id,
        product_name,
        revenue,

        SUM(revenue) OVER (
            ORDER BY revenue DESC
        ) AS running_revenue,

        SUM(revenue) OVER () AS total_revenue
    FROM product_revenue
)

SELECT
    product_name,
    revenue,
    running_revenue,
    ROUND(
        (running_revenue * 100.0) / total_revenue,
        2
    ) AS cumulative_percentage
FROM revenue_analysis
WHERE (running_revenue * 100.0) / total_revenue <= 80
ORDER BY revenue DESC;