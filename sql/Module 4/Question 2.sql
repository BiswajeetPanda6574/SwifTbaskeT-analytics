-- Which payment method generates the highest revenue, anfd how many orders were placed using each payment method? (Payment Method Analysis)

SELECT payment_method,
	   COUNT(*) AS total_orders,
	   SUM(total_order_value) AS total_revenue,
	   AVG(total_order_value) AS average_order_value
FROM swiftbasket.orders
GROUP BY payment_method
ORDER BY total_revenue DESC;
