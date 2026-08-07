-- Who is the highest-spending customer in each product category?(Top Spending Customer in Each Category)

WITH customer_category_revenue AS(
	SELECT p.category,
		   c.customer_id,
		   c.customer_name,
		   SUM(od.final_item_price) AS total_product_revenue
	FROM swiftbasket.customers c
	JOIN swiftbasket.orders o
		ON o.customer_id = c.customer_id
	JOIN swiftbasket.order_details od
		ON od.order_id = o.order_id
	JOIN swiftbasket.products p
		ON p.product_id = od.product_id
	GROUP BY p.category,
		     c.customer_id,
			 c.customer_name
),
ranked_customers AS(
	SELECT category,
		   customer_id,
		   customer_name,
		   total_product_revenue,
		   ROW_NUMBER() OVER(
		   	PARTITION BY category
			ORDER BY total_product_revenue DESC
		   ) AS rn
	FROM customer_category_revenue
)
SELECT category,
	   customer_id,
	   customer_name,
	   total_product_revenue
FROM ranked_customers
WHERE rn = 1
ORDER BY category;