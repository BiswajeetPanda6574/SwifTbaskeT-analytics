-- Customer Purchase Frequency

WITH order_gaps AS(
	SELECT customer_id,
		   order_id,
		   total_order_value,
		   order_timestamp,
		   order_timestamp::date-
		   	LAG(order_timestamp::date) OVER(
				PARTITION BY customer_id
				ORDER BY order_timestamp
			) AS days_between_orders
	FROM swiftbasket.orders
)
SELECT customer_id,
	   COUNT(order_id) AS total_orders,
	   SUM(total_order_value) AS total_revenue,
	   ROUND(AVG(days_between_orders), 2) AS avg_days_beween_orders
FROM order_gaps
GROUP BY customer_id
ORDER BY total_orders DESC;