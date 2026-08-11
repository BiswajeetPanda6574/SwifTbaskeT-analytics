-- High-Value but Low-Frequency Customers

WITH customer_metrics AS(
	SELECT customer_id,
		   COUNT(order_id) AS total_orders,
		   SUM(total_order_value) AS total_revenue,
		   AVG(total_order_value) AS avg_order_value
	FROM swiftbasket.orders
	GROUP BY customer_id
),
customer_benchmarks AS(
	SELECT customer_id,
		   total_orders,
		   total_revenue,
		   avg_order_value,
		   AVG(total_revenue) OVER() AS avg_customer_revenue,
		   AVG(total_orders) OVER() AS avg_customer_orders
	FROM customer_metrics
)
SELECT customer_id,
	   total_orders,
	   ROUND(total_revenue, 2) AS total_revenue,
	   ROUND(avg_order_value, 2) AS avg_order_value
FROM customer_benchmarks
WHERE total_revenue > avg_customer_revenue
	AND total_orders > avg_customer_orders
ORDER BY total_revenue DESC;