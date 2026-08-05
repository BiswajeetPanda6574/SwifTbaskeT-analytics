-- What percentage of all orders contained each product(Product Penetration Rate)

SELECT p.product_id,
	   p.product_name,
	   COUNT(DISTINCT od.order_id) AS orders_containing_poduct,

	   (SELECT COUNT(*)
	   FROM swiftbasket.orders) AS total_orders,

	   ROUND(
		COUNT(DISTINCT od.order_id) * 100.0 /
		(SELECT COUNT(*)
		FROM swiftbasket.orders), 2) AS penetration_percentage
FROM swiftbasket.products p
JOIN swiftbasket.order_details od
	ON od.product_id = p.product_id
GROUP BY p.product_id,
	 	 p.product_name
ORDER BY penetration_percentage DESC;