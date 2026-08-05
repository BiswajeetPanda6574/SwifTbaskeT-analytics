-- Average Order Value by Customer Segment

SELECT c.membership,
	   COUNT(DISTINCT c.customer_id) AS Customers,
	   COUNT(o.order_id) AS Orders,
	   SUM(o.total_order_value) AS Revenue,
	   AVG(o.total_order_value) AS AOV
FROM swiftbasket.customers c
JOIN swiftbasket.orders o
ON o.customer_id = c.customer_id
GROUP BY c.membership
ORDER BY AOV DESC;