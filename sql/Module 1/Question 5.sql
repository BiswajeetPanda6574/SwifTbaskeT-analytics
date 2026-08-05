-- Find the Customers who have never returned any item

SELECT c.customer_id,
	   c.customer_name
FROM swiftbasket.customers c
LEFT JOIN swiftbasket.orders o
	ON c.customer_id = o.customer_id
JOIN swiftbasket.order_details od
	ON o.order_id = od.order_id
LEFT JOIN swiftbasket.returns r
	ON r.order_id = od.order_id
WHERE r.return_id IS NULL
GROUP BY c.customer_id,
		 c.customer_name
HAVING COUNT(r.return_id) = 0;


-- SELECT * from swiftbasket.customers
-- SELECT * from swiftbasket.returns