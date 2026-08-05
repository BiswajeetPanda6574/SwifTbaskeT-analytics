-- How much revenue did each product category generate every? (Monthly Category Revenue)

SELECT DATE_TRUNC('month', o.order_timestamp) AS month,
	   p.category,
	   SUM(od.final_item_price) AS total_revenue
FROM swiftbasket.order_details od
JOIN swiftbasket.orders o
	ON od.order_id = o.order_id
JOIN swiftbasket.products p
	ON p.product_id = od.product_id
GROUP BY DATE_TRUNC('month', o.order_timestamp),
		 p.category
ORDER BY month,
	     p.category;