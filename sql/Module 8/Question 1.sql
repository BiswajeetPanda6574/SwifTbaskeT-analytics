-- Retention & Cohort Analysis

WITH customer_cohorts AS(
	SELECT customer_id,
		   DATE_TRUNC('month', MIN(order_timestamp)) AS cohort_month
	FROM swiftbasket.orders
	GROUP BY customer_id
),
cohort_activity AS(
	SELECT cc.cohort_month,
		   DATE_TRUNC('month', o.order_timestamp) AS activity_month,
		   o.customer_id
	FROM customer_cohorts cc
	JOIN swiftbasket.orders o
		ON cc.customer_id = o.customer_id
	GROUP BY cc.cohort_month,
			 DATE_TRUNC('month', o.order_timestamp),
			 o.customer_id
),
cohort_size AS(
	SELECT cohort_month,
		   COUNT(*) AS cohort_customers
	FROM customer_cohorts
	GROUP BY cohort_month
)
SELECT ca.cohort_month,
	   ca.activity_month,
	   cs.cohort_customers,
	   COUNT(DISTINCT ca.customer_id) AS acyive_customers,
	   ROUND(COUNT(DISTINCT ca.customer_id) * 100.0 / cs.cohort_customers, 2) AS retention_percentage
	   FROM cohort_activity ca
	   JOIN cohort_size cs
	   	ON ca.cohort_month = cs.cohort_month
	   GROUP BY ca.cohort_month,
	   			ca.activity_month,
				cs.cohort_customers
	   ORDER BY ca.cohort_month,
	   	  	  	ca.activity_month;