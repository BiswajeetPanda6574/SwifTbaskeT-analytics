-- What  % of total company revenue comes from the Top 10 customers?(Customer Revenue Concentration)

With customer_revenue AS(
	SELECT customer_id,
		   SUM(total_order_value) AS total_revenue
		   FROM swiftbasket.orders 
		   GROUP BY customer_id
),
top_10_customers AS(
	SELECT customer_id,
		   total_revenue
	FROM customer_revenue
	ORDER BY total_revenue DESC
	LIMIT 10
),
revenue_summary AS(
	SELECT SUM(total_revenue) AS top_10_revenue,
		   (
			SELECT SUM(total_revenue)
			FROM customer_revenue
		   ) AS total_company_revenue
	FROM top_10_customers
)
SELECT top_10_revenue,
	   total_company_revenue,
	   ROUND(top_10_revenue * 100.0 / NULLIF(total_company_revenue, 0), 2) AS top_10_revenue_contribution_percentage
FROM revenue_summary;