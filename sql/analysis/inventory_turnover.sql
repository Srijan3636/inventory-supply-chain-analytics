-- Inventory turnover proxy per product and category.
--
-- Northwind has no historical stock-level table, only a single current
-- units_in_stock snapshot per product (see DECISIONS.md). True turnover
-- (COGS / average inventory over a period) is not computable from this data.
-- What IS computable: units sold (from order_details, which is a real
-- transaction log) relative to current stock. Named explicitly as a proxy
-- so the column can't be mistaken for textbook turnover if this file is
-- read out of context.

WITH units_sold AS (
    SELECT
        od.product_id,
        SUM(od.quantity) AS total_units_sold,
        COUNT(DISTINCT o.order_id) AS order_count
    FROM order_details od
    JOIN orders o ON o.order_id = od.order_id
    GROUP BY od.product_id
)
SELECT
    p.product_id,
    p.product_name,
    c.category_name,
    p.units_in_stock,
    p.reorder_level,
    COALESCE(us.total_units_sold, 0) AS total_units_sold,
    COALESCE(us.order_count, 0)      AS order_count,
    ROUND(
        COALESCE(us.total_units_sold, 0)::numeric / NULLIF(p.units_in_stock, 0), 2
    ) AS turnover_proxy_using_current_stock,
    RANK() OVER (
        PARTITION BY c.category_name
        ORDER BY COALESCE(us.total_units_sold, 0)::numeric / NULLIF(p.units_in_stock, 0) DESC NULLS LAST
    ) AS turnover_rank_within_category
FROM products p
JOIN categories c ON c.category_id = p.category_id
LEFT JOIN units_sold us ON us.product_id = p.product_id
ORDER BY c.category_name, turnover_rank_within_category;
