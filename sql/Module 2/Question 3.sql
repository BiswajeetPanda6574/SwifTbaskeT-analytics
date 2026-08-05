-- Find customers who have not placed any order in the last 90 days.

SELECT c.customer_id,
	   c.customer_name,
	   MAX(o.order_timestamp) AS last_order_details
from swiftbasket.customers c
JOIN swiftbasket.orders o
ON c.customer_id = o.customer_id
GROUP BY c.customer_id,
		 c.customer_name
HAVING MAX(order_timestamp) < DATE '2025-10-30'- INTERVAL '90 days'
ORDER BY last_order_details;


-- select * from swiftbasket.orders