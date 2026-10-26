---
name: sql-style-review
version: 1.0.0
title: SQL style review
pack: snowflake
icon: ":material/database:"
description: Reviews a Snowflake SQL query for readability and common cost or performance pitfalls, and proposes a rewrite.
run_prompt: Review the SQL query I paste next.
---
# SQL style review

Review the query the user gives you. You only read and comment; you do not run it.

Check, in this order, and report only what you find:

1. **Correctness risks**: implicit casts, `NULL` handling in joins and `NOT IN`, a join that can multiply rows, `GROUP BY` on a different grain than the select list.
2. **Cost and speed (Snowflake)**: `SELECT *` on wide tables, a filter that cannot prune (a function on the clustering or date column), `ORDER BY` without `LIMIT` in a subquery, repeated scans of one table that a CTE could share, `DISTINCT` used to hide a duplicate join.
3. **Readability**: CTEs named for what they hold, one join condition per line, aliases that mean something, consistent keyword case.

Answer with a short list (most important first), each with the line or clause concerned and why it matters. Then give the rewritten query in one code block. If the query is fine, say so in one sentence.
