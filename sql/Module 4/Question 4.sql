-- Dark Store Performance

SELECT d.store_name,
	   COUNT(*) AS total_orders,
	   SUM(o.total_order_value) AS total_revenue,
	   AVG(o.total_order_value) AS average_order_value
FROM swiftbasket.orders o
JOIN swiftbasket.dark_stores d
ON d.store_id = o.store_id
GROUP BY store_name
ORDER BY total_revenue DESC,
		 total_orders DESC,
		 d.store_name ASC;

-- select * from swiftbasket.orders
-- select * from swiftbasket.dark_stores