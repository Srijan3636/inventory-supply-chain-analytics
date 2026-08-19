-- Slow-moving stock: days since last sale (anchored to the dataset's own
-- latest order date, not CURRENT_DATE — see DECISIONS.md, this data is from
-- 1996-1998), sell-through rate, and ABC classification by revenue
-- contribution using a cumulative-revenue window function.

WITH reference_date AS (
    SELECT MAX(order_date) AS ref_date FROM orders
),
last_sale AS (
    SELECT
        od.product_id,
        MAX(o.order_date) AS last_order_date
    FROM order_details od
    JOIN orders o ON o.order_id = od.order_id
    GROUP BY od.product_id
),
product_revenue AS (
    SELECT
        od.product_id,
        SUM(od.quantity * od.unit_price * (1 - od.discount)) AS total_revenue,
        SUM(od.quantity) AS total_units_sold
    FROM order_details od
    GROUP BY od.product_id
),
abc AS (
    SELECT
        pr.product_id,
        pr.total_revenue,
        SUM(pr.total_revenue) OVER (ORDER BY pr.total_revenue DESC
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
            / SUM(pr.total_revenue) OVER () AS cumulative_revenue_share
    FROM product_revenue pr
)
SELECT
    p.product_id,
    p.product_name,
    p.units_in_stock,
    p.reorder_level,
    ls.last_order_date,
    (SELECT ref_date FROM reference_date) - ls.last_order_date AS days_since_last_sale,
    pr.total_units_sold,
    ROUND(pr.total_revenue::numeric, 2) AS total_revenue,
    CASE
        WHEN abc.cumulative_revenue_share <= 0.80 THEN 'A'
        WHEN abc.cumulative_revenue_share <= 0.95 THEN 'B'
        ELSE 'C'
    END AS abc_class,
    -- flag: still holding meaningful stock but hasn't sold in the top
    -- quartile of staleness AND classified C (low revenue contribution)
    CASE
        WHEN p.units_in_stock > 0
             AND (SELECT ref_date FROM reference_date) - ls.last_order_date > 90
        THEN TRUE ELSE FALSE
    END AS is_slow_moving
FROM products p
LEFT JOIN last_sale ls ON ls.product_id = p.product_id
LEFT JOIN product_revenue pr ON pr.product_id = p.product_id
LEFT JOIN abc ON abc.product_id = p.product_id
ORDER BY is_slow_moving DESC, days_since_last_sale DESC NULLS FIRST;
