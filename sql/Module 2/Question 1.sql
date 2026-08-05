-- Identify Top 10 Most Valuable Customers based on total spending

SELECT c.customer_id,
	   c.customer_name,
	   c.membership,
	   c.loyalty_score,
	   COUNT(o.order_id) AS number_of_orders,
	   SUM(o.total_order_value) AS total_spending
FROM swiftbasket.customers c
JOIN swiftbasket.orders o
ON o.customer_id = c.customer_id
GROUP BY c.customer_id,
		 c.customer_name,
		 c.membership,
	   	 c.loyalty_score
ORDER BY total_spending DESC,
		 c.loyalty_score DESC
LIMIT 10;

-- select * from swiftbasket.customers;
-- select * from swiftbasket.orders;