-- How is the revenue of each product category growing or declining month over month? (Month-over-Month Category Growth)

WITH monthly_category_revenue AS(
	SELECT DATE_TRUNC('month', o.order_timestamp) AS month,
		   p.category,
	       SUM(od.final_item_price) AS monthly_revenue
	FROM swiftbasket.order_details od
	JOIN swiftbasket.orders o
		ON o.order_id = od.order_id
	JOIN swiftbasket.products p
		ON od.product_id = p.product_id
	GROUP BY DATE_TRUNC('month', o.order_timestamp),
			 p.category
),
revenue_with_previous AS(
	SELECT month,
		   category,
		   monthly_revenue,
		   LAG(monthly_revenue) OVER(
			PARTITION BY category
			ORDER BY month
		   ) AS previous_month_revenue
	FROM monthly_category_revenue
)
SELECT month,
	   category,
	   monthly_revenue,
	   previous_month_revenue,
	   ROUND((monthly_revenue - previous_month_revenue) * 100.0
	   / NULLIF(previous_month_revenue, 0), 2) AS mom_growth_percentage
FROM revenue_with_previous
ORDER BY category,
		 month;