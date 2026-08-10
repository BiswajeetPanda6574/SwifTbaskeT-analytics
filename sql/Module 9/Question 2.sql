-- How does each dark store rank by revenue within its month? (Dark Store Revenue Ranking by Month)

WITH monthly_store_revenue AS(
	SELECT DATE_TRUNC('month', o.order_timestamp) AS month,
	 	   ds.store_id,
		   ds.store_name,
		   SUM(o.total_order_value) AS monthly_revenue
	FROM swiftbasket.orders o
	JOIN swiftbasket.dark_stores ds
	ON o.store_id = ds.store_id
	GROUP BY DATE_TRUNC('month', o.order_timestamp),
			 ds.store_id,
			 ds.store_name
),
ranked_stores AS(
	SELECT month,
		   store_id,
		   store_name,
		   monthly_revenue,
		   RANK() OVER(
			PARTITION BY month
			ORDER BY monthly_revenue DESC
		   ) AS revenue_rank
	FROM monthly_store_revenue
)
SELECT month,
	   store_id,
	   store_name,
	   monthly_revenue,
	   revenue_rank
FROM ranked_stores
ORDER BY month,
	  	 revenue_rank;