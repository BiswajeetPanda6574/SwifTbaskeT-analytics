-- Ordrer Status Dashboard

SELECT COUNT(CASE WHEN order_status = 'Delivered' THEN 1 END) AS delivered_orders,
	   COUNT(CASE WHEN order_status = 'Cancelled' THEN 1 END) AS cancelled_orders,
	   COUNT(CASE WHEN order_status = 'Returned' THEN 1 END) AS returned_orders,
	   COUNT(CASE WHEN order_status = 'Failed' THEN 1 END) AS failed_orders,

	   ROUND(COUNT(CASE WHEN order_status = 'Delivered' THEN 1 END) * 100.0 / COUNT(*), 2) AS delivered_pct,
	   ROUND(COUNT(CASE WHEN order_status = 'Cancelled' THEN 1 END) * 100.0 / COUNT(*), 2) AS cancelled_pct,
	   ROUND(COUNT(CASE WHEN order_status = 'Returned' THEN 1 END) * 100.0 / COUNT(*), 2) AS returned_pct,
	   ROUND(COUNT(CASE WHEN order_status = 'Failed' THEN 1 END) * 100.0 / COUNT(*), 2) AS failed_pct
FROM swiftbasket.orders;


-- select * from swiftbasket.orders