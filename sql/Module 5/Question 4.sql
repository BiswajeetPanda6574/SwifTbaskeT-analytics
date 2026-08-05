-- Customer Churn Risk

WITH last_orders AS(
	SELECT customer_id,
		   MAX(order_timestamp::date) AS last_order_date
	FROM swiftbasket.orders
	GROUP BY customer_id
)

SELECT customer_id,
	   last_order_date,
	   DATE'2025-09-30' - last_order_date AS days_since_last_order,
	   CASE
	   		WHEN DATE'2025-09-3' - last_order_date <= 30 THEN 'Active'
			WHEN DATE'2025-09-30' - last_order_date <= 60 THEN 'At Risk'
			ELSE 'Churned'
		END AS churn_status
FROM last_orders
ORDER BY days_since_last_order DESC,
		 customer_id ASC;