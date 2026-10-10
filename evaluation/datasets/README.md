# Evaluation datasets

Versioned reference cases cover text retrieval, SQL, combined evidence,
conversation, missing evidence and source conflicts. A frozen dataset is pending.

Each case records question/history, expected route, reference facts, supporting
pages or database IDs, and snapshot identity. Generated references require human
review. System comparisons use the same dataset version. RAGAS context inputs,
if used, contain passage text rather than chunk IDs.
