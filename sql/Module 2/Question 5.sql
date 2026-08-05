-- Find products whose total sales are greater then the average sales of all products.

SELECT p.product_id,
	   p.product_name,
	   p.category,
	   revenue.product_revenue
FROM
(
	SELECT product_id,
		   SUM(final_item_price) AS product_revenue
	FROM swiftbasket.order_details 
	GROUP BY product_id
) revenue
JOIN swiftbasket.products p
	ON revenue.product_id = p.product_id
WHERE revenue.product_revenue > (
				SELECT AVG(product_revenue)
				FROM
				(
					SELECT SUM(final_item_price) AS product_revenue
					FROM swiftbasket.order_details
					GROUP BY product_id
				) avg_revenue
)
ORDER BY revenue.product_revenue DESC;


-- select * from swiftbasket.products
-- select * from swiftbasket.order_details