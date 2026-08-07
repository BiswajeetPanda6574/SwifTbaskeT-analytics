-- Which pairs of products are most frequently purchased together in the same order? (Market Based Analysis)

WITH product_pairs AS(
	SELECT od1.product_id AS product_1,
		   od2.product_id AS product_2,
		   COUNT(*) AS times_bought_together
	FROM swiftbasket.order_details od1
	JOIN swiftbasket.order_details od2
		ON od1.order_id = od2.order_id
		AND od1.product_id < od2.product_id
	GROUP BY od1.product_id,
		  	 od2.product_id
)
SELECT p1.product_name AS product_1,
	   p2.product_name AS product_2,
	   times_bought_together
FROM product_pairs pp
JOIN swiftbasket.products p1
	ON pp.product_1 = p1.product_id
JOIN swiftbasket.products p2
	ON pp.product_2 = p2.product_id
ORDER BY times_bought_together DESC
LIMIT 10;