-- Supplier lead time and reliability: actual delivery time (shipped - order
-- date), late-delivery rate (shipped after required_date), ranked per
-- supplier. Joined product -> supplier via order_details since Northwind's
-- orders table has no direct supplier link (an order can span suppliers
-- through its line items).

WITH order_supplier_lines AS (
    SELECT DISTINCT
        o.order_id,
        o.order_date,
        o.required_date,
        o.shipped_date,
        p.supplier_id
    FROM orders o
    JOIN order_details od ON od.order_id = o.order_id
    JOIN products p ON p.product_id = od.product_id
    WHERE o.shipped_date IS NOT NULL  -- exclude unshipped orders from lead-time calc
),
lead_times AS (
    SELECT
        supplier_id,
        order_id,
        (shipped_date - order_date) AS lead_time_days,
        CASE WHEN shipped_date > required_date THEN 1 ELSE 0 END AS is_late
    FROM order_supplier_lines
)
SELECT
    s.supplier_id,
    s.company_name,
    s.country,
    COUNT(lt.order_id) AS orders_supplied,
    ROUND(AVG(lt.lead_time_days), 1) AS avg_lead_time_days,
    ROUND(100.0 * SUM(lt.is_late) / NULLIF(COUNT(lt.order_id), 0), 1) AS late_delivery_pct,
    RANK() OVER (ORDER BY AVG(lt.lead_time_days) ASC) AS rank_by_fastest_avg_lead_time,
    RANK() OVER (ORDER BY 100.0 * SUM(lt.is_late) / NULLIF(COUNT(lt.order_id), 0) ASC) AS rank_by_lowest_late_pct
FROM suppliers s
JOIN lead_times lt ON lt.supplier_id = s.supplier_id
GROUP BY s.supplier_id, s.company_name, s.country
HAVING COUNT(lt.order_id) >= 3  -- suppliers with too few orders make noisy averages
ORDER BY rank_by_fastest_avg_lead_time;
