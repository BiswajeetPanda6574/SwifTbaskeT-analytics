-- Dark Store Order Share

WITH store_metrics AS(
	SELECT ds.store_id,
		   ds.store_name,
		   COUNT(o.order_id) AS total_orders,
		   SUM(o.total_order_value) AS total_revenue
	FROM swiftbasket.orders o
	JOIN swiftbasket.dark_stores ds
	ON ds.store_id = o.store_id
	GROUP BY ds.store_id, ds.store_name
)
SELECT store_id,
	   store_name,
	   total_orders,
	   total_revenue,
	   ROUND(total_orders * 100.0 / SUM(total_orders)OVER(), 2) AS order_share_percentage,
	   ROUND(total_revenue * 100.0 / SUM(total_revenue)OVER(), 2) AS revenue_share_percentage
FROM store_metrics
ORDER BY order_share_percentage DESC;