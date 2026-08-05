-- Which are the Top 10 Best-Selling Products by quantity sold ?

SELECT p.product_name, 
	   SUM(o2.quantity) AS quantity_sold
FROM swiftbasket.products p
JOIN swiftbasket.order_details o2
ON p.product_id = o2.product_id
GROUP BY p.product_id,
		 p.product_name
ORDER BY quantity_sold DESC,
		 p.product_name ASC
LIMIT 10;

-- SELECT * from swiftbasket.products




