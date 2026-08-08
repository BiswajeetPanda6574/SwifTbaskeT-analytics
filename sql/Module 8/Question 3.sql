-- Customer Lifetime Value(CLV)

WITH customer_metrics AS(
	SELECT customer_id,
		   COUNT(order_id) AS total_orders,
		   SUM(total_order_value) AS total_revenue,
		   AVG(total_order_value) AS avg_revenue,
		   MIN(order_timestamp::date) AS first_order_date,
		   MAX(order_timestamp::date) AS last_order_date
	FROM swiftbasket.orders
	GROUP BY customer_id
)
SELECT customer_id,
	   total_orders,
	   ROUND(total_revenue, 2) AS total_revenue,
	   ROUND(avg_revenue, 2) AS avg_revenue,
	   last_order_date - first_order_date AS customer_lifetime_days,
	   ROUND(total_orders * 30.0 /
	   NULLIF(last_order_date - first_order_date, 0), 2) AS avg_orders_per_month
FROM customer_metrics
ORDER BY total_revenue DESC;