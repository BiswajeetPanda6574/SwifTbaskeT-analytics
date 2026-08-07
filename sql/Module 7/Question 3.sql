-- Which are the Top 3 performing dark stores every month based on revenue? (Darkstores by Revenue in Each Month)

WITH monthly_store_revenue AS(
	SELECT DATE_TRUNC('month', o.order_timestamp) AS month,
		   d.store_id,
		   d.store_name,
		   SUM(o.total_order_value) AS total_revenue
	FROM swiftbasket.orders o
	JOIN swiftbasket.dark_stores d
	ON o.store_id = d.store_id
	GROUP BY DATE_TRUNC('month', o.order_timestamp),
			 d.store_id,
			 d.store_name
),
ranked_stores AS(
	SELECT month,
		   store_id,
		   store_name,
		   total_revenue,
		   ROW_NUMBER() OVER(
			PARTITION BY month
			ORDER BY total_revenue DESC
		   ) AS rn
	FROM monthly_store_revenue
)
SELECT month,
	   store_id,
	   store_name,
	   total_revenue,
	   rn AS rank
FROM ranked_stores
WHERE rn <= 3 
ORDER BY month,
	 	 rn;


-- select * from swiftbasket.orders
-- select * from swiftbasket.dark_stores