-- Order-status performance across dark stores (Order Status Performance by Dark Store)

SELECT ds.store_id,
	   ds.store_name,
	   COUNT(o.order_id) AS total_orders,
	   COUNT(
			CASE 
				WHEN o.order_status = 'Delivered' THEN 1
				END
	   ) AS delivered_orders,
	   COUNT(
			CASE
				WHEN o.order_status = 'Cancelled' THEN 1
				END
	   ) AS cancelled_orders,
	   COUNT(
			CASE
				WHEN o.order_status = 'Failed' THEN 1
				END
	   ) AS failed_orders,
	   ROUND(
			COUNT(
				CASE 
					WHEN o.order_status = 'Delivered' THEN 1
					END
			) * 100.0 / NULLIF(COUNT(o.order_id), 0), 2) AS delivery_rate_percentage,
		ROUND(
			COUNT(
				CASE 
					WHEN o.order_status = 'Cancelled' THEN 1
					END
			) * 100.0 / NULLIF(COUNT(o.order_id), 0), 2) AS cancellation_rate_percentage
FROM swiftbasket.orders o
JOIN swiftbasket.dark_stores ds
ON ds.store_id = o.store_id
GROUP BY ds.store_id, ds.store_name
ORDER BY delivery_rate_percentage DESC;
			