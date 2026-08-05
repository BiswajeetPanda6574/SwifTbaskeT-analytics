-- How is SwiftBasket performing overall?

SELECT ROUND(SUM(total_order_value), 2) AS total_revenue,
	   COUNT(order_id) AS total_orders,
	   COUNT(DISTINCT customer_id) AS active_customers,
	   ROUND(AVG(total_order_value), 2) AS average_order_value,
	   (SELECT COUNT(*) FROM swiftbasket.returns) AS returned_items,
	   ROUND(
			(SELECT COUNT(*)
			FROM swiftbasket.returns)::NUMERIC/
			(SELECT COUNT(*) FROM swiftbasket.order_details) * 100, 2) AS return_rate_percent
FROM swiftbasket.orders;