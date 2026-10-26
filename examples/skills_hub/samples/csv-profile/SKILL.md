---
name: csv-profile
version: 1.0.0
title: CSV profile
pack: data
icon: ":material/table_chart:"
description: Profiles a CSV file the user points to (rows, columns, missing values, distinct counts) with a small script, then explains what stands out.
run_prompt: Profile the CSV file I name next.
---
# CSV profile

When the user names a CSV file that is available in the sandbox:

1. Run `python3 scripts/profile.py <path-to-the-csv>` (the script sits next to this SKILL.md) and read its JSON output.
2. Explain in a few lines what stands out: columns that are mostly empty, columns with a single value, a column that looks like an id (all distinct), a column whose values look mixed (numbers and text).
3. Suggest at most three checks worth doing before using the file.

If the file is not there, say so and ask where it is. Do not guess the content.
