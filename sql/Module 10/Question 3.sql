-- Which product categories are purchased by the largest no of unique customers? (Category with the highest Customer Reach)

WITH category_metrics AS(
	SELECT p.category,
		   COUNT(DISTINCT o.customer_id) AS unique_customers,
		   COUNT(DISTINCT o.order_id) AS unique_products,
		   SUM(od.final_item_price) AS total_revenue
	FROM swiftbasket.order_details od
	JOIN swiftbasket.orders o
		ON od.order_id = o.order_id
	JOIN swiftbasket.products p
		ON od.product_id = p.product_id
	GROUP BY p.category
)
SELECT category,
	   unique_customers,
	   unique_products,
	   ROUND(total_revenue, 2) AS total_revenue,
	   ROUND(total_revenue / NULLIF(unique_customers, 0), 2) AS avg_revenue_per_customer
FROM category_metrics
ORDER BY unique_customers DESC;