-- Do higher discounts actually result in customers buying more unit? (Discount Effectiveness Analysis)

WITH discount_analysis AS (
	SELECT 
		CASE 
			WHEN item_discount <= 10 THEN 'No/Low Discount'
			WHEN item_discount <= 20 THEN 'Medium Discount'
			ELSE 'High Discount'
		END AS discount_band,
		quantity,
		final_item_price
	FROM swiftbasket.order_details
)

SELECT discount_band,
	   COUNT(*) AS total_line_items,
	   SUM(quantity) AS total_units_sold,
	   ROUND(AVG(quantity), 2) AS avg_quantity_per_item,
	   ROUND(SUM(final_item_price), 2) AS total_revenue
FROM discount_analysis
GROUP BY discount_band
ORDER BY 
	CASE 
		WHEN discount_band = 'No/Low Discount' THEN 1
		WHEN discount_band = 'Medium Discount' THEN 2
		WHEN discount_band = 'High Discount' THEN 3
	END;