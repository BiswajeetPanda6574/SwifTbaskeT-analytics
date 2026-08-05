-- Find the 7-day moving average of revenue

WITH daily_sales AS
(
	SELECT DATE_TRUNC('day', order_timestamp) AS day,
		   SUM(total_order_value) AS daily_revenue
	FROM swiftbasket.orders
	GROUP BY DATE_TRUNC('day', order_timestamp)
)
SELECT day,
	   daily_revenue,
	   ROUND(AVG(daily_revenue)
	   OVER(
			ORDER BY day
			ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
	   ), 2) AS moving_average_7_days
FROM daily_sales 
ORDER BY day;