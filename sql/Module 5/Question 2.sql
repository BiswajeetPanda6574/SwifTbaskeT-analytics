-- Top 5 Customers by Revenue in Each Month

WITH monthly_customer_revenue AS(
	SELECT DATE_TRUNC('month', order_timestamp) AS month,
		   customer_id,
		   SUM(total_order_value) AS total_revenue
	FROM swiftbasket.orders
	GROUP BY DATE_TRUNC('month', order_timestamp),
			 customer_id
),
ranked_customers AS(
	SELECT month,
		   customer_id,
		   total_revenue,
		   ROW_NUMBER() OVER(
		   		PARTITION BY month
				ORDER BY total_revenue DESC
		   ) AS rn
	FROM monthly_customer_revenue
)
SELECT month,
	   customer_id,
	   total_revenue,
	   rn AS rank
FROM ranked_customers
WHERE rn <= 5
ORDER BY month,
	  	 rn;