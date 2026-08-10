-- Which darkstores recieve the most orders across different delivery slots, and what is their revenue performance? (Delivry Slot Performance)

SELECT ds.store_name,
	   o.delivery_slot,
	   COUNT(o.order_id) AS total_orders,
	   SUM(o.total_order_value) AS total_revenue,
	   ROUND(AVG(o.total_order_value), 2) AS avg_order_value
FROM swiftbasket.orders o	   
JOIN swiftbasket.dark_stores ds
ON o.store_id = ds.store_id
GROUP BY ds.store_name,
	 	 o.delivery_slot
ORDER BY total_orders DESC,
	   	 total_revenue DESC;