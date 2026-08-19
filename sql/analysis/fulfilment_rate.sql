-- Order fulfilment rate and delay distribution: what share of orders ship
-- on/before the required date, and how delay is distributed into buckets
-- for a Power BI histogram-style visual.

WITH shipped_orders AS (
    SELECT
        order_id,
        order_date,
        required_date,
        shipped_date,
        (shipped_date - required_date) AS days_vs_required  -- negative = early/on-time
    FROM orders
    WHERE shipped_date IS NOT NULL AND required_date IS NOT NULL
),
bucketed AS (
    SELECT
        *,
        CASE
            WHEN days_vs_required <= 0 THEN 'On time or early'
            WHEN days_vs_required BETWEEN 1 AND 7 THEN 'Late 1-7 days'
            WHEN days_vs_required BETWEEN 8 AND 14 THEN 'Late 8-14 days'
            ELSE 'Late 15+ days'
        END AS delay_bucket
    FROM shipped_orders
)
SELECT
    delay_bucket,
    COUNT(*) AS order_count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS pct_of_orders,
    ROUND(AVG(days_vs_required), 1) AS avg_days_vs_required
FROM bucketed
GROUP BY delay_bucket
ORDER BY
    CASE delay_bucket
        WHEN 'On time or early' THEN 1
        WHEN 'Late 1-7 days' THEN 2
        WHEN 'Late 8-14 days' THEN 3
        ELSE 4
    END;
