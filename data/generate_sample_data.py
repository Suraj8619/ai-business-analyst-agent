"""
Generates a synthetic sales dataset so the agent has something real to query.
Swap this out for your own CSV later -- just point db_setup.py at it.
"""

import numpy as np
import pandas as pd

np.random.seed(42)

REGIONS = ["North", "South", "East", "West"]
CATEGORIES = ["Electronics", "Furniture", "Apparel", "Office Supplies", "Toys"]
SEGMENTS = ["Enterprise", "SMB", "Mid-Market"]

n_rows = 2000
dates = pd.date_range("2025-01-01", "2025-09-30", freq="D")

df = pd.DataFrame({
    "order_id": range(1, n_rows + 1),
    "order_date": np.random.choice(dates, n_rows),
    "region": np.random.choice(REGIONS, n_rows, p=[0.3, 0.25, 0.25, 0.2]),
    "category": np.random.choice(CATEGORIES, n_rows),
    "customer_segment": np.random.choice(SEGMENTS, n_rows, p=[0.3, 0.5, 0.2]),
    "is_returning_customer": np.random.choice([True, False], n_rows, p=[0.4, 0.6]),
    "quantity": np.random.randint(1, 10, n_rows),
    "unit_price": np.round(np.random.uniform(10, 500, n_rows), 2),
})

df["revenue"] = np.round(df["quantity"] * df["unit_price"], 2)

# Bake in a deliberate Q3 dip in Enterprise revenue so there's something
# interesting for the agent to find and explain.
q3_mask = (df["order_date"] >= "2025-07-01") & (df["order_date"] <= "2025-09-30")
enterprise_mask = df["customer_segment"] == "Enterprise"
df.loc[q3_mask & enterprise_mask, "revenue"] *= 0.55
df.loc[q3_mask & enterprise_mask, "quantity"] = (
    df.loc[q3_mask & enterprise_mask, "quantity"] * 0.6
).round().astype(int)

# Also add a return_rate-relevant flag: mark some orders as returned,
# weighted higher for Apparel (useful for "return rate by category" questions).
return_prob = df["category"].map({
    "Apparel": 0.18,
    "Electronics": 0.09,
    "Furniture": 0.05,
    "Office Supplies": 0.03,
    "Toys": 0.07,
})
df["is_returned"] = np.random.binomial(1, return_prob).astype(bool)

df = df.sort_values("order_date").reset_index(drop=True)
df.to_csv("data/sales_data.csv", index=False)

print(f"Generated {len(df)} rows -> data/sales_data.csv")
print(df.head())
