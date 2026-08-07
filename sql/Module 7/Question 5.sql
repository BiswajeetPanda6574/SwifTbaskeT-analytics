-- Customers who bought Product A but never bought product B

SELECT DISTINCT c.customer_id,
				c.customer_name
FROM swiftbasket.customers c
JOIN swiftbasket.orders o
	ON c.customer_id = o.customer_id
JOIN swiftbasket.order_details od
	ON o.order_id = od.order_id
JOIN swiftbasket.products p
	ON p.product_id = od.product_id
WHERE p.product_name = 'Pringles Potato Chips Baked Classic Salted 90.0 g'
AND NOT EXISTS(
	SELECT 1
	FROM swiftbasket.orders o1
	JOIN swiftbasket.order_details od1
		ON o1.order_id = od1.order_id
	JOIN swiftbasket.products p1
		ON od1.product_id = p1.product_id
	WHERE o1.customer_id = c.customer_id
		AND p1.product_name = 'Fortune Chakki Atta Maida Select 15.0 kg'
)
ORDER BY customer_name;

-- select product_name from swiftbasket.products