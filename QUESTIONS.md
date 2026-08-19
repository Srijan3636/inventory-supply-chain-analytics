# Interview Questions — Honest Answers

---

**Q: Walk me through this project.**
Analytics on the Northwind sample database — inventory turnover, slow-moving
stock, supplier lead times, and order fulfilment, using CTEs and window
functions. Loaded, validated with 10 data-quality checks, then 4 analysis
queries.

**Q: Why "turnover proxy" and not just "inventory turnover"?**
Because it isn't real turnover, and calling it that would be dishonest.
Textbook turnover is COGS divided by average inventory over a period.
Northwind only has a single current stock snapshot per product — there's no
historical stock level to average. What I computed instead — units sold
relative to current stock — is a genuinely useful proxy, but it's not the
same metric, so the column name says exactly what it is.

**Q: Why anchor "days since last sale" to the dataset's max date instead of
today?**
The data is from 1996-98. Using `CURRENT_DATE` would make every single
product look ~30 years stale, and the metric would stop differentiating
anything — everything would tie at "maximally old." Anchoring to the
dataset's own latest order date is what makes the metric mean anything.

**Q: This is a very well-known teaching dataset. Doesn't that undercut the
project?**
It's small — about 830 orders — and I say so directly in the README rather
than pretending otherwise. What it does demonstrate is real: I found and
fixed the "days since last sale" bug myself, ran 10 real data-quality checks
rather than assuming the data was clean, and made a defensible, disclosed
choice about the turnover proxy instead of faking a metric the data can't
support. If I extended this, Olist's e-commerce dataset (Kaggle) is the
obvious scale-up — messier, bigger, and with real historical order-status
tracking.

**Q: What did the data-quality validation actually check?**
Referential integrity across all 4 foreign-key relationships (no order line
pointing to a nonexistent product, etc.), a date-logic sanity check
(shipped_date can't be before order_date), and value sanity (no negative
prices, quantities, or stock). All 10 passed. I did this specifically because
"the data is already clean" is a claim, and I wanted to verify it rather than
assume it.

**Q: What's the ABC classification actually measuring?**
Cumulative revenue contribution — A products account for the top 80% of
revenue, B the next 15%, C the rest. It's a standard technique, applied here
using a window function (`SUM() OVER (ORDER BY revenue DESC ROWS BETWEEN
UNBOUNDED PRECEDING AND CURRENT ROW)`) to compute the running share before
bucketing.

**Q: What would you do differently?**
Scale this up on Olist or a similar dataset with real historical stock
snapshots, so "inventory turnover" could be the real metric instead of a
disclosed proxy. That's the single biggest thing this dataset can't give me.
