-- Customer Reactivation(Customer who became inactive and later returned)

WITH customer_orders AS(
	SELECT customer_id,
		   order_id,
		   order_timestamp::date AS order_date,
		   LAG(order_timestamp::date) OVER(
				PARTITION BY customer_id
				ORDER BY order_timestamp
		   ) AS previous_order_date
	FROM swiftbasket.orders
),
reactivation_events AS(
	SELECT customer_id,
		   order_id,
		   order_date AS reactivation_date,
		   order_date - previous_order_date AS days_since_previous_order
	FROM customer_orders
	WHERE previous_order_date IS NOT NULL
		AND order_date - previous_order_date >= 60
),
orders_after_reactivation AS (
    SELECT
        r.customer_id,
        r.order_id,
        r.reactivation_date,
        r.days_since_previous_order,
        COUNT(o2.order_id) AS orders_after_reactivation

    FROM reactivation_events r

    LEFT JOIN swiftbasket.orders o2
        ON o2.customer_id = r.customer_id
       AND o2.order_timestamp::date > r.reactivation_date

    GROUP BY
        r.customer_id,
        r.order_id,
        r.reactivation_date,
        r.days_since_previous_order
)

SELECT
    customer_id,
    reactivation_date,
    days_since_previous_order,
    orders_after_reactivation

FROM orders_after_reactivation

ORDER BY
    reactivation_date;