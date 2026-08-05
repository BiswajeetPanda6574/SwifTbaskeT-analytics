-- Repeat vs New Customers

WITH first_orders AS(
	SELECT customer_id,
		   DATE_TRUNC('month', MIN(order_timestamp)) AS first_order_month
	FROM swiftbasket.orders
	GROUP BY customer_id
)

SELECT DATE_TRUNC('month', o.order_timestamp) AS month,
	   COUNT(DISTINCT o.customer_id) AS total_customers,
	   COUNT(DISTINCT CASE
	   		WHEN DATE_TRUNC('month', o.order_timestamp) = fo.first_order_month
			THEN o.customer_id
			END) AS new_customers,
		COUNT(DISTINCT CASE
	   		WHEN DATE_TRUNC('month', o.order_timestamp) <> fo.first_order_month
			THEN o.customer_id
			END) AS repeat_customers
FROM swiftbasket.orders o
JOIN first_orders fo
ON o.customer_id = fo.customer_id
GROUP BY DATE_TRUNC('month', o.order_timeStamp)
ORDER BY month;