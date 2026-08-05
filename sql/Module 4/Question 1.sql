-- Customer Segmentation by Spending

SELECT c.customer_id,
	   c.customer_name,
	   COALESCE(SUM(o.total_order_value), 0) AS total_spending,
	   CASE
	   		WHEN COALESCE(SUM(o.total_order_value), 0) >= 14000 THEN 'Premium'
			WHEN COALESCE(SUM(o.total_order_value), 0) BETWEEN 8000 AND 13999 THEN 'Gold'
			ELSE 'Standard'
		END AS Segement
FROM swiftbasket.customers c
LEFT JOIN swiftbasket.orders o
ON o.customer_id = c.customer_id
GROUP BY c.customer_id,
	  	 c.customer_name
ORDER BY total_spending DESC;