-- Identify the Top selling product in each category based on revenue.

-- Without CTE

SELECT category,
	   product,
	   revenue
FROM 
(SELECT
    p.category,
    p.product_name AS product,
    SUM(od.final_item_price) AS revenue,
    ROW_NUMBER() OVER(
        PARTITION BY p.category
        ORDER BY SUM(od.final_item_price) DESC,
                 p.product_name ASC
    ) AS rn
FROM swiftbasket.products p
JOIN swiftbasket.order_details od
ON p.product_id = od.product_id
GROUP BY
    p.category,
    p.product_id,
    p.product_name
)ranked_products
WHERE rn = 1;


-- Using CTE

WITH product_revenue AS(
SELECT p.category,
	   p.product_name AS product,
	   SUM(od.final_item_price) AS revenue
FROM swiftbasket.products p
JOIN swiftbasket.order_details od
ON p.product_id = od.product_id
GROUP BY p.category,
		 p.product_id,
		 p.product_name
),
ranked_products AS
(
	SELECT *,
	   	   ROW_NUMBER() OVER(
	   			PARTITION BY category
	   			ORDER BY revenue DESC, product ASC
	   	   ) AS rn
FROM product_revenue
)
SELECT category,
	   product,
	   revenue
FROM ranked_products
WHERE rn = 1;


-- select * from swiftbasket.products



