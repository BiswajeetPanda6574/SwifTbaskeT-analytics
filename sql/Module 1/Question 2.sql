-- Monthly Orders Trend

SELECT COUNT(order_id) AS orders,
	   DATE_TRUNC('month', order_timestamp) AS order_month,
	   SUM(total_order_value) AS monthly_revenue
FROM swiftbasket.orders
GROUP BY order_month
ORDER BY order_month ASC;