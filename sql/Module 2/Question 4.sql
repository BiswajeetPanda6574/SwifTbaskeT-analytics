-- Find the Top 5 customers by total spending in each area

SELECT *
FROM
(
	SELECT c.customer_id,
		   c.customer_name,
		   c.area,
		   SUM(o.total_order_value) AS total_spending,
		   DENSE_RANK() OVER(
				PARTITION BY c.area
				ORDER BY SUM(total_order_value) DESC
		   ) AS customer_rank
	FROM swiftbasket.customers c
	JOIN swiftbasket.orders o
		ON c.customer_id = o.customer_id
	GROUP BY c.customer_id,
			 c.customer_name,
			 c.area
) ranked_customers
WHERE customer_rank <= 5
ORDER BY area,
		 customer_rank,
		 total_spending DESC,
		 customer_id;

-- select * from swiftbasket.customers