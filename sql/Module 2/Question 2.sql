-- Identify the Top 3 Customers in each membership type based on total spending.

SELECT * 
FROM
(
	SELECT c.customer_id,
		   c.customer_name,
		   c.membership,
		   c.loyalty_score,
		   SUM(o.total_order_value) AS total_spending,
		   DENSE_RANK() OVER(
				PARTITION BY c.membership
				ORDER BY SUM(o.total_order_value) DESC
		   ) AS customer_rank
	FROM swiftbasket.customers c
	JOIN swiftbasket.orders o
		ON c.customer_id = o.customer_id
	GROUP BY c.customer_id,
			 c.customer_name,
			 c.membership,
			 c.loyalty_score
)t
WHERE customer_rank <= 3
ORDER BY membership,
		 customer_rank;

-- select * from swiftbasket.customers