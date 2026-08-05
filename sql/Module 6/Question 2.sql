-- What percentage of the company's total product revenue is contributed by each category(Category Revenue Contribution)

WITH category_revenue AS(
	SELECT p.category,
		   SUM(od.final_item_price) AS category_revenue
	FROM swiftbasket.order_details od
	JOIN swiftbasket.products p
		ON od.product_id =p.product_id
	GROUP BY p.category
),
revenue_analysis AS (
	SELECT category,
		   category_revenue,
		   SUM(category_revenue) OVER() AS total_revenue
	FROM category_revenue
)
SELECT category,
	   category_revenue,
	   total_revenue,
	   ROUND(category_revenue * 100.0 / total_revenue, 2) AS revenue_contribution_percentage
FROM revenue_analysis
ORDER BY revenue_contribution_percentage DESC;