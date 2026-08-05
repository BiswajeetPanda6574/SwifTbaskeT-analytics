-- What is the Average Basket Size ?

SELECT AVG(total_items) AS average_basketsize
FROM (SELECT order_id, 
	     	 SUM(quantity) AS total_items
	  FROM swiftbasket.order_details
	  GROUP BY order_id) AS basket;