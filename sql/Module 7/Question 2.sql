-- How many orders do customers typically buy in a single order? (Customer Basket Size Analysis)

WITH basket_size AS (
    SELECT
        o.order_id,
        COUNT(od.product_id) AS total_products,
        SUM(od.final_item_price) AS order_value
    FROM swiftbasket.orders o
    JOIN swiftbasket.order_details od
        ON o.order_id = od.order_id
    GROUP BY o.order_id
),

basket_category AS (
    SELECT
        order_id,
        total_products,
        order_value,

        CASE
            WHEN total_products BETWEEN 1 AND 3
                THEN 'Small Basket'
            WHEN total_products BETWEEN 4 AND 6
                THEN 'Medium Basket'
            ELSE 'Large Basket'
        END AS basket_type

    FROM basket_size
)

SELECT
    basket_type,
    COUNT(order_id) AS total_orders,
    ROUND(AVG(total_products), 2) AS avg_products_per_order,
    ROUND(AVG(order_value), 2) AS avg_order_value

FROM basket_category

GROUP BY basket_type

ORDER BY
    CASE
        WHEN basket_type = 'Small Basket' THEN 1
        WHEN basket_type = 'Medium Basket' THEN 2
        WHEN basket_type = 'Large Basket' THEN 3
    END;