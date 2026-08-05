-- How much did revenue grow or decline every month compared to the previous month? (Month-Over-Month Revenue)

With monthly_sales AS
(
	SELECT DATE_TRUNC('month', order_timestamp) AS month,
		   SUM(total_order_value) AS monthly_revenue
	FROM swiftbasket.orders
	GROUP BY DATE_TRUNC('month',order_timestamp)
),
revenue_lag AS
(
	SELECT month,
		   monthly_revenue,
		   LAG(monthly_revenue) OVER (ORDER BY month) AS previous_month_revenue
	FROM monthly_sales
)
SELECT month,
	   monthly_revenue,
	   previous_month_revenue,
	   monthly_revenue - previous_month_revenue AS revenue_difference,
	   ROUND(
		  ((monthly_revenue - previous_month_revenue) * 100.0)
		  / NULLIF (previous_month_revenue, 0), 2) AS growth_percentage
FROM revenue_lag
ORDER BY month;

-- select * from swiftbasket.orders
-- select * from swiftbasket.order_details