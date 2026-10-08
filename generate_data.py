"""
LQ Dining (synthetic) - restaurant group data generator for a Power BI portfolio project.
Clean, analysis-ready star schema. All figures are fictional. Amounts are GBP, ex-VAT.

Planted business stories:
  1. Seasonality: December peak, January dip, Fri/Sat busiest, lunch and dinner peaks.
  2. Salford Quays opens 2 Jun 2025 (ramps up over ~6 months) -> why like-for-like (LFL) matters.
  3. Menu price rises: +6% on 1 Mar 2025, +4% on 1 Feb 2026.
  4. Ingredient price shock: meat +22% from 1 Sep 2025, dairy +12% from 1 Oct 2025.
  5. Didsbury slowly declines from Apr 2025: higher wastage, labour overspend, worse reviews.
  6. Campaigns: January Blues & Christmas work; Influencer Takeover & Student Night flop.
  7. Delivery share grows each year.
"""
import os
import numpy as np
import pandas as pd

rng = np.random.default_rng(2024)
OUT = os.path.dirname(os.path.abspath(__file__))
START, END = pd.Timestamp("2024-01-01"), pd.Timestamp("2026-09-30")

# ----------------------------------------------------------------------------- dim_branch
dim_branch = pd.DataFrame([
    ("B01", "Northern Quarter", "City Centre", "M4 1HN", 90, "2019-04-12", "nq.manager@lqdining.example"),
    ("B02", "Deansgate", "City Centre", "M3 4LZ", 120, "2018-09-01", "deansgate.manager@lqdining.example"),
    ("B03", "Didsbury", "Suburban", "M20 6RE", 70, "2021-03-19", "didsbury.manager@lqdining.example"),
    ("B04", "Salford Quays", "Waterfront", "M50 3AZ", 100, "2025-06-02", "salfordquays.manager@lqdining.example"),
], columns=["branch_id", "branch_name", "area_type", "postcode", "seats", "opening_date", "manager_email"])
dim_branch["opening_date"] = pd.to_datetime(dim_branch["opening_date"])
dim_branch["trading_hours_per_day"] = 11
BR_VOL = {"B01": 1.0, "B02": 1.25, "B03": 0.9, "B04": 1.1}

# ----------------------------------------------------------------------------- dim_date
d = pd.date_range("2024-01-01", "2026-12-31")
dim_date = pd.DataFrame({"date": d})
dim_date["year"] = d.year
dim_date["quarter"] = "Q" + d.quarter.astype(str)
dim_date["year_quarter"] = d.year.astype(str) + "-Q" + d.quarter.astype(str)
dim_date["month_number"] = d.month
dim_date["month_name"] = d.strftime("%B")
dim_date["month_short"] = d.strftime("%b")
dim_date["year_month"] = d.strftime("%Y-%m")
dim_date["month_start"] = d.to_period("M").to_timestamp()
dim_date["week_start"] = d - pd.to_timedelta(d.dayofweek, unit="D")
dim_date["day_of_week_number"] = d.dayofweek + 1
dim_date["day_name"] = d.strftime("%A")
dim_date["day_short"] = d.strftime("%a")
dim_date["is_weekend"] = d.dayofweek >= 5
dim_date["is_trading_day"] = d.dayofweek != 1          # closed Tuesdays
dim_date["has_sales_data"] = d <= END

# ----------------------------------------------------------------------------- dim_time
hours = list(range(12, 23))
dim_time = pd.DataFrame({"hour": hours})
dim_time["time_label"] = dim_time["hour"].map(lambda h: f"{h:02d}:00")
dim_time["daypart"] = dim_time["hour"].map(lambda h: "Lunch" if h <= 14 else ("Afternoon" if h <= 16 else "Dinner"))

# ----------------------------------------------------------------------------- dim_channel
dim_channel = pd.DataFrame([
    ("CH1", "Dine-in", "In-house", 0.00),
    ("CH2", "Takeaway", "In-house", 0.00),
    ("CH3", "Deliveroo", "Delivery", 0.30),
    ("CH4", "Uber Eats", "Delivery", 0.30),
], columns=["channel_id", "channel_name", "channel_group", "commission_rate"])

# ----------------------------------------------------------------------------- dim_role
dim_role = pd.DataFrame([
    ("R01", "Head Chef", "Kitchen", 1.55, 0.14), ("R02", "Sous Chef", "Kitchen", 1.30, 0.10),
    ("R03", "Line Cook", "Kitchen", 1.08, 0.20), ("R04", "Kitchen Porter", "Kitchen", 1.00, 0.08),
    ("R05", "General Manager", "Front of House", 1.75, 0.12), ("R06", "Supervisor", "Front of House", 1.20, 0.08),
    ("R07", "Server", "Front of House", 1.00, 0.20), ("R08", "Bartender", "Front of House", 1.04, 0.08),
], columns=["role_id", "role_name", "department", "rate_mult", "cost_share"])


def min_wage(dt):  # UK National Living Wage (approx.)
    return 11.44 if dt < pd.Timestamp("2025-04-01") else (12.21 if dt < pd.Timestamp("2026-04-01") else 12.71)


# ----------------------------------------------------------------------------- dim_supplier
dim_supplier = pd.DataFrame([
    ("S01", "Manchester Meat Co", "Meat"), ("S02", "Fleetwood Fish Ltd", "Fish"),
    ("S03", "Pennine Dairies", "Dairy"), ("S04", "Smithfield Fresh Produce", "Produce"),
    ("S05", "North West Wholesale", "Dry Goods"), ("S06", "Mancunian Drinks Supply", "Beverages"),
], columns=["supplier_id", "supplier_name", "supplier_category"])
SUP = dict(zip(dim_supplier.supplier_category, dim_supplier.supplier_id))

# ----------------------------------------------------------------------------- dim_ingredient
ING = {
    "Meat": [("Beef Short Rib", "kg", 14), ("Sirloin Steak", "kg", 28), ("Ribeye Steak", "kg", 32), ("Beef Fillet", "kg", 48),
             ("Tomahawk Steak", "kg", 30), ("Beef Mince", "kg", 8.5), ("Chicken Breast", "kg", 7.5), ("Chicken Thigh", "kg", 5.5),
             ("Chicken Wings", "kg", 4.5), ("Whole Chicken", "each", 5.0), ("Lamb Rump", "kg", 18), ("Lamb Mince", "kg", 10),
             ("Duck Leg", "kg", 12), ("Bacon", "kg", 9), ("Pork Sausage", "kg", 7)],
    "Fish": [("Cod Fillet", "kg", 16), ("Seabass Fillet", "kg", 19), ("King Prawns", "kg", 18), ("Squid", "kg", 11), ("Lobster", "each", 14)],
    "Dairy": [("Butter", "kg", 7), ("Double Cream", "L", 4), ("Milk", "L", 1.1), ("Cheddar", "kg", 9), ("Parmesan", "kg", 18),
              ("Halloumi", "kg", 11), ("Burrata", "each", 3.2), ("Eggs", "each", 0.28), ("Ice Cream", "L", 5.5), ("Cream Cheese", "kg", 6)],
    "Produce": [("Potatoes", "kg", 0.9), ("Onions", "kg", 1.0), ("Garlic", "kg", 5), ("Tomatoes", "kg", 2.6), ("Lettuce", "each", 0.9),
                ("Mushrooms", "kg", 4.5), ("Tenderstem Broccoli", "kg", 7), ("Lemons", "each", 0.3), ("Limes", "each", 0.25),
                ("Mint", "bunch", 0.8), ("Fresh Herbs", "bunch", 1.0), ("Seasonal Veg", "kg", 2.5), ("Avocado", "each", 0.9),
                ("Strawberries", "kg", 6), ("Oranges", "each", 0.4)],
    "Dry Goods": [("Arborio Rice", "kg", 3.2), ("Basmati Rice", "kg", 2.2), ("Linguine", "kg", 2.4), ("Macaroni", "kg", 1.8),
                  ("Flour", "kg", 0.8), ("Panko Breadcrumbs", "kg", 3.5), ("Brioche Buns", "each", 0.45), ("Flatbread", "each", 0.35),
                  ("Bao Buns", "each", 0.3), ("Puff Pastry", "kg", 4), ("Sugar", "kg", 1.1), ("Dark Chocolate", "kg", 9),
                  ("Vegetable Oil", "L", 2.0), ("Olive Oil", "L", 7), ("Truffle Oil", "L", 40), ("Stock Base", "kg", 6),
                  ("Katsu Curry Sauce", "L", 4.5), ("Spices", "kg", 12), ("Plant Patty", "each", 1.4), ("Chickpeas", "kg", 2),
                  ("Quinoa", "kg", 5), ("Toffee Sauce", "L", 4.5), ("Biscuit Base", "kg", 3), ("Meringue", "kg", 6),
                  ("Pastry Case", "each", 0.6), ("Coffee Beans", "kg", 18)],
    "Beverages": [("Lager Keg", "L", 2.4), ("IPA Keg", "L", 3.0), ("Stout Keg", "L", 2.8), ("Cider Keg", "L", 2.3),
                  ("House Red Wine", "L", 6), ("House White Wine", "L", 6), ("Prosecco", "L", 8), ("Malbec Bottle", "each", 9.5),
                  ("Sauvignon Blanc Bottle", "each", 8.5), ("Vodka", "L", 16), ("Gin", "L", 18), ("Rum", "L", 17),
                  ("Bourbon", "L", 22), ("Aperol", "L", 14), ("Passion Fruit Puree", "L", 6), ("Coffee Liqueur", "L", 15),
                  ("Cola Syrup", "L", 6), ("Lemonade Syrup", "L", 5), ("Sparkling Water Bottle", "each", 0.4), ("Orange Juice", "L", 2.2)],
}
rows = []
for cat, items in ING.items():
    for name, unit, cost in items:
        rows.append((f"I{len(rows)+1:03d}", name, cat, unit, cost, SUP[cat]))
dim_ingredient = pd.DataFrame(rows, columns=["ingredient_id", "ingredient_name", "ingredient_category", "unit", "standard_cost_per_unit", "supplier_id"])
ING_ID = dict(zip(dim_ingredient.ingredient_name, dim_ingredient.ingredient_id))
ING_COST = dict(zip(dim_ingredient.ingredient_id, dim_ingredient.standard_cost_per_unit))
ING_CAT = dict(zip(dim_ingredient.ingredient_id, dim_ingredient.ingredient_category))
ING_SUP = dict(zip(dim_ingredient.ingredient_id, dim_ingredient.supplier_id))

# ----------------------------------------------------------------------------- dim_menu_item + recipes
# (name, category, price_2026, target_cost_pct, popularity, vegetarian, [ingredients, hero first])
MENU = [
    ("Soup of the Day", "Starters", 5.5, .22, 6, True, ["Seasonal Veg", "Onions", "Stock Base", "Double Cream", "Flatbread"]),
    ("Salt & Pepper Calamari", "Starters", 7.5, .30, 9, False, ["Squid", "Flour", "Spices", "Lemons", "Vegetable Oil"]),
    ("Halloumi Fries", "Starters", 6.5, .28, 10, True, ["Halloumi", "Flour", "Spices", "Vegetable Oil"]),
    ("Chicken Wings", "Starters", 7.0, .27, 11, False, ["Chicken Wings", "Spices", "Butter", "Vegetable Oil"]),
    ("Garlic Flatbread", "Starters", 5.0, .18, 8, True, ["Flatbread", "Garlic", "Butter", "Fresh Herbs"]),
    ("Burrata & Tomato", "Starters", 8.5, .34, 4, True, ["Burrata", "Tomatoes", "Olive Oil", "Fresh Herbs"]),
    ("Prawn Cocktail", "Starters", 8.0, .33, 3, False, ["King Prawns", "Lettuce", "Lemons", "Tomatoes"]),
    ("Crispy Duck Bao", "Starters", 8.0, .31, 6, False, ["Duck Leg", "Bao Buns", "Spices", "Onions"]),
    ("Fish & Chips", "Mains", 15.5, .28, 16, False, ["Cod Fillet", "Potatoes", "Flour", "Vegetable Oil", "Lemons"]),
    ("Chicken Supreme", "Mains", 17.5, .30, 7, False, ["Chicken Breast", "Seasonal Veg", "Potatoes", "Butter", "Double Cream"]),
    ("Beef Short Rib", "Mains", 22.0, .34, 6, False, ["Beef Short Rib", "Potatoes", "Stock Base", "Seasonal Veg"]),
    ("Lamb Rump", "Mains", 23.5, .35, 3, False, ["Lamb Rump", "Potatoes", "Seasonal Veg", "Fresh Herbs"]),
    ("Seabass Fillet", "Mains", 19.5, .33, 5, False, ["Seabass Fillet", "Potatoes", "Butter", "Lemons", "Seasonal Veg"]),
    ("Mushroom Risotto", "Mains", 14.5, .22, 6, True, ["Arborio Rice", "Mushrooms", "Parmesan", "Butter", "Stock Base"]),
    ("Chicken Caesar Salad", "Mains", 13.5, .27, 8, False, ["Chicken Breast", "Lettuce", "Parmesan", "Bacon", "Eggs"]),
    ("Steak Frites", "Mains", 21.0, .36, 12, False, ["Sirloin Steak", "Potatoes", "Butter", "Vegetable Oil"]),
    ("Pie of the Day", "Mains", 15.0, .26, 7, False, ["Beef Mince", "Puff Pastry", "Potatoes", "Seasonal Veg", "Stock Base"]),
    ("Vegan Buddha Bowl", "Mains", 13.0, .25, 4, True, ["Quinoa", "Chickpeas", "Avocado", "Seasonal Veg"]),
    ("Lobster Linguine", "Mains", 26.0, .38, 2, False, ["Lobster", "Linguine", "Tomatoes", "Garlic", "Double Cream"]),
    ("Chicken Katsu Curry", "Mains", 15.5, .26, 11, False, ["Chicken Thigh", "Katsu Curry Sauce", "Basmati Rice", "Panko Breadcrumbs"]),
    ("8oz Sirloin", "Grill", 26.0, .38, 6, False, ["Sirloin Steak", "Potatoes", "Tomatoes", "Mushrooms", "Butter"]),
    ("10oz Ribeye", "Grill", 30.0, .39, 5, False, ["Ribeye Steak", "Potatoes", "Tomatoes", "Mushrooms", "Butter"]),
    ("6oz Fillet", "Grill", 34.0, .40, 2, False, ["Beef Fillet", "Potatoes", "Tomatoes", "Mushrooms", "Butter"]),
    ("Half Rotisserie Chicken", "Grill", 16.5, .27, 8, False, ["Whole Chicken", "Potatoes", "Spices", "Lemons"]),
    ("Tomahawk to Share", "Grill", 65.0, .42, 1, False, ["Tomahawk Steak", "Potatoes", "Mushrooms", "Butter", "Seasonal Veg"]),
    ("Classic Beef Burger", "Burgers", 14.0, .29, 14, False, ["Beef Mince", "Brioche Buns", "Cheddar", "Lettuce", "Potatoes"]),
    ("Double Smash Burger", "Burgers", 16.0, .31, 10, False, ["Beef Mince", "Brioche Buns", "Cheddar", "Bacon", "Potatoes"]),
    ("Buttermilk Chicken Burger", "Burgers", 14.5, .27, 9, False, ["Chicken Thigh", "Brioche Buns", "Milk", "Flour", "Potatoes"]),
    ("Plant Burger", "Burgers", 13.5, .30, 3, True, ["Plant Patty", "Brioche Buns", "Lettuce", "Tomatoes", "Potatoes"]),
    ("Lamb Kofta Burger", "Burgers", 15.0, .30, 3, False, ["Lamb Mince", "Brioche Buns", "Spices", "Lettuce", "Potatoes"]),
    ("Fries", "Sides", 4.0, .15, 20, True, ["Potatoes", "Vegetable Oil"]),
    ("Truffle Parmesan Fries", "Sides", 5.5, .22, 8, True, ["Potatoes", "Truffle Oil", "Parmesan", "Vegetable Oil"]),
    ("Onion Rings", "Sides", 4.5, .18, 6, True, ["Onions", "Flour", "Vegetable Oil"]),
    ("House Salad", "Sides", 4.0, .22, 5, True, ["Lettuce", "Tomatoes", "Olive Oil"]),
    ("Mac & Cheese", "Sides", 5.5, .24, 7, True, ["Macaroni", "Cheddar", "Milk", "Butter"]),
    ("Tenderstem Broccoli", "Sides", 4.5, .30, 3, True, ["Tenderstem Broccoli", "Butter", "Garlic"]),
    ("Sticky Toffee Pudding", "Desserts", 7.0, .20, 12, True, ["Flour", "Toffee Sauce", "Butter", "Sugar", "Ice Cream"]),
    ("Chocolate Brownie", "Desserts", 6.5, .22, 10, True, ["Dark Chocolate", "Butter", "Sugar", "Eggs", "Ice Cream"]),
    ("Lemon Tart", "Desserts", 6.5, .24, 4, True, ["Pastry Case", "Lemons", "Eggs", "Sugar", "Double Cream"]),
    ("Eton Mess", "Desserts", 6.5, .26, 5, True, ["Strawberries", "Meringue", "Double Cream"]),
    ("Cheesecake", "Desserts", 7.0, .25, 7, True, ["Cream Cheese", "Biscuit Base", "Sugar", "Strawberries"]),
    ("Ice Cream Trio", "Desserts", 5.5, .20, 4, True, ["Ice Cream"]),
    ("Coca-Cola", "Soft Drinks", 3.2, .14, 18, True, ["Cola Syrup", "Sparkling Water Bottle"]),
    ("Lemonade", "Soft Drinks", 3.2, .14, 8, True, ["Lemonade Syrup", "Sparkling Water Bottle"]),
    ("Sparkling Water", "Soft Drinks", 2.8, .15, 7, True, ["Sparkling Water Bottle"]),
    ("Fresh Orange Juice", "Soft Drinks", 3.8, .25, 5, True, ["Orange Juice"]),
    ("Flat White", "Soft Drinks", 3.2, .14, 9, True, ["Coffee Beans", "Milk"]),
    ("Draught Lager", "Beer & Cider", 5.8, .30, 18, True, ["Lager Keg"]),
    ("Craft IPA", "Beer & Cider", 6.5, .32, 9, True, ["IPA Keg"]),
    ("Guinness", "Beer & Cider", 6.2, .31, 7, True, ["Stout Keg"]),
    ("Cider", "Beer & Cider", 5.8, .30, 6, True, ["Cider Keg"]),
    ("House Red (175ml)", "Wine", 6.5, .26, 9, True, ["House Red Wine"]),
    ("House White (175ml)", "Wine", 6.5, .26, 10, True, ["House White Wine"]),
    ("Prosecco (Glass)", "Wine", 7.5, .25, 8, True, ["Prosecco"]),
    ("Malbec (Bottle)", "Wine", 32.0, .31, 3, True, ["Malbec Bottle"]),
    ("Sauvignon Blanc (Bottle)", "Wine", 30.0, .30, 3, True, ["Sauvignon Blanc Bottle"]),
    ("Pornstar Martini", "Cocktails", 10.5, .20, 10, True, ["Vodka", "Passion Fruit Puree", "Prosecco", "Limes"]),
    ("Espresso Martini", "Cocktails", 10.5, .20, 9, True, ["Vodka", "Coffee Liqueur", "Coffee Beans", "Sugar"]),
    ("Aperol Spritz", "Cocktails", 9.5, .22, 8, True, ["Aperol", "Prosecco", "Sparkling Water Bottle", "Oranges"]),
    ("Mojito", "Cocktails", 9.5, .19, 6, True, ["Rum", "Limes", "Mint", "Sugar", "Sparkling Water Bottle"]),
    ("Old Fashioned", "Cocktails", 11.0, .21, 3, True, ["Bourbon", "Sugar", "Oranges"]),
]
DRINK_CATS = {"Soft Drinks", "Beer & Cider", "Wine", "Cocktails"}
menu_rows, recipe_rows = [], []
for i, (name, cat, price, tgt, pop, veg, ings) in enumerate(MENU, start=1):
    item_id = f"M{i:03d}"
    menu_rows.append((item_id, name, cat, "Drinks" if cat in DRINK_CATS else "Food", price, veg, pop))
    target_cost = price * tgt * 0.92
    hero_share = 0.9 if cat in DRINK_CATS else 0.6
    if len(ings) == 1:
        shares = [1.0]
    else:
        rest = rng.dirichlet(np.ones(len(ings) - 1)) * (1 - hero_share)
        shares = [hero_share] + list(rest)
    for ing, sh in zip(ings, shares):
        iid = ING_ID[ing]
        qty = round(target_cost * sh / ING_COST[iid], 4)
        recipe_rows.append((item_id, iid, max(qty, 0.001)))
dim_menu_item = pd.DataFrame(menu_rows, columns=["menu_item_id", "menu_item_name", "category", "menu_section", "current_price", "is_vegetarian", "_pop"])
bridge_recipe = pd.DataFrame(recipe_rows, columns=["menu_item_id", "ingredient_id", "quantity_per_portion"])
bridge_recipe.insert(0, "recipe_line_id", [f"RL{i:04d}" for i in range(1, len(bridge_recipe) + 1)])
PRICE = dict(zip(dim_menu_item.menu_item_id, dim_menu_item.current_price))
CAT = dict(zip(dim_menu_item.menu_item_id, dim_menu_item.category))
SECTION = dict(zip(dim_menu_item.menu_item_id, dim_menu_item.menu_section))
POOLS = {}
for cat, grp in dim_menu_item.groupby("category"):
    POOLS[cat] = (grp.menu_item_id.values, grp._pop.values / grp._pop.sum())
mains = dim_menu_item[dim_menu_item.category.isin(["Mains", "Grill", "Burgers"])]
POOLS["MAIN"] = (mains.menu_item_id.values, mains._pop.values / mains._pop.sum())
RECIPE = {k: list(zip(g.ingredient_id, g.quantity_per_portion)) for k, g in bridge_recipe.groupby("menu_item_id")}


def price_on(item_id, dt):
    factor = 1.06 * 1.04 if dt < pd.Timestamp("2025-03-01") else (1.04 if dt < pd.Timestamp("2026-02-01") else 1.0)
    return round(round(PRICE[item_id] / factor / 0.05) * 0.05, 2)


def ingredient_cost_on(iid, dt):
    months = (dt.year - 2024) * 12 + dt.month - 1
    c = ING_COST[iid] * (1.003 ** months)
    if ING_CAT[iid] == "Meat" and dt >= pd.Timestamp("2025-09-01"):
        c *= 1.22
    if ING_CAT[iid] == "Dairy" and dt >= pd.Timestamp("2025-10-01"):
        c *= 1.12
    return round(c, 4)


# ----------------------------------------------------------------------------- dim_campaign
dim_campaign = pd.DataFrame([
    ("CMP000", "No Campaign", None, None, "None", 0.00, "All", "All", "All", 0.0, 0),
    ("CMP001", "Christmas Party Season 2024", "2024-11-18", "2024-12-22", "Email", 0.10, "Food", "Dine-in", "All", 0.35, 3000),
    ("CMP002", "January Blues 2025", "2025-01-06", "2025-01-31", "Instagram", 0.25, "Food", "Dine-in", "All", 0.45, 4500),
    ("CMP003", "Uber Eats Launch Offer", "2025-04-01", "2025-04-30", "Uber Eats Ads", 0.20, "All", "Uber Eats", "All", 0.50, 2500),
    ("CMP004", "Summer Cocktail Hour", "2025-07-01", "2025-08-31", "Instagram", 0.50, "Cocktails", "Dine-in", "All", 0.30, 3500),
    ("CMP005", "Influencer Takeover", "2025-10-06", "2025-11-02", "TikTok", 0.15, "All", "Dine-in", "All", 0.12, 9000),
    ("CMP006", "Christmas Party Season 2025", "2025-11-17", "2025-12-21", "Email", 0.10, "Food", "Dine-in", "All", 0.35, 3500),
    ("CMP007", "January Blues 2026", "2026-01-05", "2026-01-31", "Instagram", 0.25, "Food", "Dine-in", "All", 0.45, 5000),
    ("CMP008", "Student Night Wednesdays", "2026-02-04", "2026-04-29", "Instagram", 0.30, "All", "Dine-in", "All", 0.25, 3000),
    ("CMP009", "Salford Summer Terrace", "2026-06-01", "2026-07-31", "Google Ads", 0.00, "All", "Dine-in", "B04", 0.20, 4000),
], columns=["campaign_id", "campaign_name", "start_date", "end_date", "marketing_channel", "discount_pct",
            "discount_applies_to", "order_channel", "branch_scope", "redeem", "planned_budget"])
UPLIFT = {"CMP001": 1.10, "CMP002": 1.35, "CMP003": 1.30, "CMP004": 1.15, "CMP005": 1.02,
          "CMP006": 1.12, "CMP007": 1.30, "CMP008": 1.03, "CMP009": 1.20}
camps = dim_campaign[dim_campaign.campaign_id != "CMP000"].copy()
camps["start_date"] = pd.to_datetime(camps.start_date)
camps["end_date"] = pd.to_datetime(camps.end_date)


def active_campaigns(dt, branch):
    out = []
    for c in camps.itertuples():
        if c.start_date <= dt <= c.end_date and c.branch_scope in ("All", branch):
            if c.campaign_id == "CMP008" and dt.dayofweek != 2:   # Wednesdays only
                continue
            out.append(c)
    return out


# ----------------------------------------------------------------------------- dim_customer
N_CUST = 5000
cust_branch = rng.choice(["B01", "B02", "B03", "B04"], N_CUST, p=[.28, .34, .22, .16])
join = []
for b in cust_branch:
    lo = max(pd.Timestamp("2023-01-01"), dim_branch.set_index("branch_id").opening_date[b])
    span = (END - lo).days
    join.append(lo + pd.Timedelta(days=int(rng.integers(0, span))))
dim_customer = pd.DataFrame({
    "customer_id": [f"C{i:05d}" for i in range(1, N_CUST + 1)],
    "join_date": join,
    "home_branch_id": cust_branch,
    "age_band": rng.choice(["18-24", "25-34", "35-44", "45-54", "55+"], N_CUST, p=[.18, .32, .24, .15, .11]),
    "acquisition_source": rng.choice(["In-store sign-up", "Website", "Instagram", "Google", "Referral"], N_CUST, p=[.40, .20, .18, .12, .10]),
})
dim_customer["_w"] = rng.pareto(1.3, N_CUST) + 0.2
non_member = pd.DataFrame([{"customer_id": "C00000", "join_date": pd.Timestamp("2018-01-01"), "home_branch_id": "B00",
                            "age_band": "Unknown", "acquisition_source": "Non-member", "_w": 0}])
cust_by_branch = {b: g.sort_values("join_date") for b, g in dim_customer.groupby("home_branch_id")}

# ----------------------------------------------------------------------------- sales generation
MONTH_SEAS = {1: .75, 2: .85, 3: .95, 4: 1.0, 5: 1.05, 6: 1.05, 7: 1.10, 8: 1.05, 9: .95, 10: 1.0, 11: 1.05, 12: 1.35}
DOW = {0: .70, 2: .80, 3: .95, 4: 1.35, 5: 1.50, 6: 1.10}
YEAR = {2024: 1.0, 2025: 1.05, 2026: 1.08}
HOUR_W = {"dine": np.array([.08, .11, .07, .03, .03, .06, .12, .16, .15, .11, .08]),
          "away": np.array([.05, .07, .05, .03, .04, .09, .15, .18, .15, .11, .08])}
COVERS_P = np.array([.12, .38, .14, .20, .06, .06, .02, .02])
BASE_ORDERS = 4.6
open_dt = dim_branch.set_index("branch_id").opening_date


def branch_trend(b, dt):
    if b == "B03" and dt >= pd.Timestamp("2025-04-01"):
        m = (dt.year - 2025) * 12 + dt.month - 4
        return max(0.80, 1 - 0.008 * m)
    if b == "B04":
        return 0.55 + 0.45 * min(1.0, (dt - open_dt[b]).days / 180)
    return 1.0


def channel_probs(dt):
    delivery = {2024: .17, 2025: .21, 2026: .25}[dt.year]
    takeaway = .09
    return np.array([1 - delivery - takeaway, takeaway, delivery * .55, delivery * .45])


order_rows, line_rows = [], []
oid = lid = 0
for b in dim_branch.branch_id:
    days = pd.date_range(max(START, open_dt[b]), END)
    for dt in days:
        if dt.dayofweek == 1:
            continue
        acts = active_campaigns(dt, b)
        uplift_dine = np.prod([UPLIFT[c.campaign_id] for c in acts if c.order_channel == "Dine-in"]) if acts else 1.0
        lam = BASE_ORDERS * BR_VOL[b] * MONTH_SEAS[dt.month] * DOW[dt.dayofweek] * YEAR[dt.year] * branch_trend(b, dt) * uplift_dine
        if dt.month == 12 and dt.day >= 24:
            lam *= 0.5 if dt.day != 25 else 0
        n = rng.poisson(lam)
        cp = channel_probs(dt)
        if any(c.campaign_id == "CMP003" for c in acts):
            cp[3] *= 1.3
            cp = cp / cp.sum()
        elig = cust_by_branch[b]
        elig = elig[elig.join_date <= dt]
        for _ in range(n):
            oid += 1
            order_id = f"O{oid:06d}"
            ch = rng.choice(["CH1", "CH2", "CH3", "CH4"], p=cp)
            dine = ch == "CH1"
            hour = int(rng.choice(hours, p=HOUR_W["dine" if dine else "away"]))
            covers = int(rng.choice(range(1, 9), p=COVERS_P)) if dine else 0
            people = covers if dine else int(rng.choice([1, 2, 3, 4], p=[.45, .35, .13, .07]))
            member_p = 0.35 if dine else 0.22
            cust = "C00000"
            if len(elig) and rng.random() < member_p:
                w = elig._w.values
                cust = elig.customer_id.values[rng.choice(len(elig), p=w / w.sum())]
            # campaign tagging
            camp = None
            for c in acts:
                ch_ok = (c.order_channel == "Dine-in" and dine) or (c.order_channel == "Uber Eats" and ch == "CH4")
                if ch_ok and rng.random() < c.redeem:
                    camp = c
                    break
            # basket
            basket = {}
            lunch = hour <= 14

            def add(pool):
                ids, p = POOLS[pool]
                it = ids[rng.choice(len(ids), p=p)]
                basket[it] = basket.get(it, 0) + 1
            for _p in range(people):
                add("MAIN")
                if rng.random() < (.30 if dine else .25): add("Starters")
                if rng.random() < (.35 if dine else .50): add("Sides")
                if rng.random() < (.25 if dine else .12): add("Desserts")
                if dine:
                    if rng.random() < .88:
                        cocktail_boost = 1.6 if (camp is not None and camp.campaign_id == "CMP004") else 1.0
                        dp = np.array([.50, .22, .17, .11 * cocktail_boost]) if lunch else np.array([.24, .30, .26, .20 * cocktail_boost])
                        add(rng.choice(["Soft Drinks", "Beer & Cider", "Wine", "Cocktails"], p=dp / dp.sum()))
                    if not lunch and rng.random() < .40:
                        add(rng.choice(["Beer & Cider", "Wine", "Cocktails"], p=[.40, .35, .25]))
                elif rng.random() < .40:
                    add("Soft Drinks")
            for it, q in basket.items():
                lid += 1
                up = price_on(it, dt)
                gross = round(up * q, 2)
                disc = 0.0
                if camp is not None and camp.discount_pct > 0:
                    applies = camp.discount_applies_to
                    if applies == "All" or applies == SECTION[it] or applies == CAT[it]:
                        disc = round(gross * camp.discount_pct, 2)
                line_rows.append((f"L{lid:07d}", order_id, dt, hour, b, ch, it, cust,
                                  camp.campaign_id if camp is not None else "CMP000", q, up, gross, disc, round(gross - disc, 2)))
            order_rows.append((order_id, dt, hour, b, ch, cust, camp.campaign_id if camp is not None else "CMP000", covers))

fact_sales_lines = pd.DataFrame(line_rows, columns=["sales_line_id", "order_id", "date", "hour", "branch_id", "channel_id", "menu_item_id",
                                                    "customer_id", "campaign_id", "quantity", "unit_price", "gross_amount",
                                                    "discount_amount", "net_amount"])
fact_orders = pd.DataFrame(order_rows, columns=["order_id", "date", "hour", "branch_id", "channel_id", "customer_id", "campaign_id", "covers"])
order_tot = fact_sales_lines.groupby("order_id").agg(items=("quantity", "sum"), order_net_amount=("net_amount", "sum")).reset_index()
fact_orders = fact_orders.merge(order_tot, on="order_id", how="left")
fact_orders = fact_orders[fact_orders["items"].notna()].copy()
fact_orders["items"] = fact_orders["items"].astype(int)
fact_orders["order_net_amount"] = fact_orders["order_net_amount"].round(2)

# ----------------------------------------------------------------------------- daily theoretical ingredient usage
rec = bridge_recipe[["menu_item_id", "ingredient_id", "quantity_per_portion"]]
use = fact_sales_lines[["date", "branch_id", "menu_item_id", "quantity"]].merge(rec, on="menu_item_id")
use["qty_used"] = use.quantity * use.quantity_per_portion
daily_use = use.groupby(["date", "branch_id", "ingredient_id"], as_index=False).qty_used.sum()

# ----------------------------------------------------------------------------- fact_wastage
REASONS = ["Spoilage / Expired", "Over-production", "Prep Error", "Customer Return", "Dropped / Damaged"]
REASON_P = np.array([.34, .28, .18, .10, .10])
waste_rows = []
wid = 0
for (dt, b), g in daily_use.groupby(["date", "branch_id"]):
    rate = 2.4 if (b == "B03" and dt >= pd.Timestamp("2025-04-01")) else (1.6 if b == "B04" and (dt - open_dt[b]).days < 120 else 1.1)
    for _ in range(rng.poisson(rate)):
        r = g.iloc[rng.choice(len(g), p=(g.qty_used / g.qty_used.sum()).values)]
        reason = rng.choice(REASONS, p=REASON_P)
        frac = rng.uniform(0.08, 0.35) * (1.4 if b == "B03" and dt >= pd.Timestamp("2025-04-01") else 1)
        qty = round(max(r.qty_used * frac, 0.01), 3)
        wid += 1
        uc = ingredient_cost_on(r.ingredient_id, dt)
        waste_rows.append((f"W{wid:05d}", dt, b, r.ingredient_id, reason, qty, uc, round(qty * uc, 2)))
fact_wastage = pd.DataFrame(waste_rows, columns=["waste_id", "date", "branch_id", "ingredient_id", "waste_reason", "quantity", "unit_cost", "waste_cost"])

# ----------------------------------------------------------------------------- fact_purchases (deliveries on 1st and 16th, covering each half-month)
def variance_factor(b, dt):  # unexplained over-usage (portioning, theft, unrecorded waste)
    if b == "B03":
        return 1.05 if dt < pd.Timestamp("2025-04-01") else 1.09
    return {"B01": 1.02, "B02": 1.025, "B04": 1.04}[b]


du = daily_use.copy()
du["period_start"] = du.date.map(lambda x: x.replace(day=1) if x.day < 16 else x.replace(day=16))
wq = fact_wastage.assign(period_start=fact_wastage.date.map(lambda x: x.replace(day=1) if x.day < 16 else x.replace(day=16)))
wq = wq.groupby(["period_start", "branch_id", "ingredient_id"], as_index=False).quantity.sum().rename(columns={"quantity": "waste_qty"})
pu = du.groupby(["period_start", "branch_id", "ingredient_id"], as_index=False).qty_used.sum().merge(wq, how="left", on=["period_start", "branch_id", "ingredient_id"])
pu["waste_qty"] = pu.waste_qty.fillna(0)
pu["quantity"] = [round((u * variance_factor(b, dt) + w) * rng.uniform(0.98, 1.02), 3) for u, w, b, dt in zip(pu.qty_used, pu.waste_qty, pu.branch_id, pu.period_start)]
pu["unit_cost"] = [ingredient_cost_on(i, dt) for i, dt in zip(pu.ingredient_id, pu.period_start)]
pu["line_cost"] = (pu.quantity * pu.unit_cost).round(2)
pu["supplier_id"] = pu.ingredient_id.map(ING_SUP)
pu = pu.sort_values(["period_start", "branch_id", "ingredient_id"]).reset_index(drop=True)
pu.insert(0, "purchase_line_id", [f"P{i:06d}" for i in range(1, len(pu) + 1)])
fact_purchases = pu.rename(columns={"period_start": "delivery_date"})[["purchase_line_id", "delivery_date", "branch_id", "supplier_id", "ingredient_id", "quantity", "unit_cost", "line_cost"]]

# ----------------------------------------------------------------------------- fact_labour_shifts
daily_sales = fact_sales_lines.groupby(["date", "branch_id"], as_index=False).net_amount.sum()
lab_rows = []
sid = 0
for r in daily_sales.itertuples():
    b, dt = r.branch_id, r.date
    if b == "B03":
        target = 0.29 if dt < pd.Timestamp("2025-04-01") else 0.29 + min(0.07, 0.004 * ((dt.year - 2025) * 12 + dt.month - 4))
        # staffing stays flat as sales fall -> labour % creeps up
    elif b == "B04":
        target = 0.36 if (dt - open_dt[b]).days < 90 else 0.29
    else:
        target = {"B01": 0.28, "B02": 0.26}[b]
    day_cost = r.net_amount * target * rng.uniform(0.95, 1.05)
    for role in dim_role.itertuples():
        rate = round(min_wage(dt) * role.rate_mult, 2)
        cost = day_cost * role.cost_share
        actual = round(cost / rate * 4) / 4
        if actual <= 0:
            continue
        sched = round(actual * rng.uniform(0.92, 1.02) * 4) / 4
        sid += 1
        lab_rows.append((f"SH{sid:06d}", dt, b, role.role_id, sched, actual, rate, round(actual * rate, 2)))
fact_labour_shifts = pd.DataFrame(lab_rows, columns=["shift_id", "date", "branch_id", "role_id", "scheduled_hours", "actual_hours", "hourly_rate", "labour_cost"])

# ----------------------------------------------------------------------------- fact_bookings
SOURCES = ["Website", "OpenTable", "Phone", "Instagram"]
bk_rows = []
bid = 0
dine = fact_orders[fact_orders.channel_id == "CH1"]
for o in dine.itertuples():
    p_book = 0.55 if o.hour >= 17 else 0.30
    if o.date.dayofweek >= 4:
        p_book += 0.1
    if rng.random() >= p_book:
        continue
    lead = int(min(rng.geometric(0.15) - 1, 45))
    created = o.date - pd.Timedelta(days=lead)
    bid += 1
    bk_rows.append((f"BK{bid:06d}", created, o.date, o.hour, o.branch_id, o.customer_id,
                    rng.choice(SOURCES, p=[.45, .30, .20, .05]), o.covers, "Completed"))
    noshow_p = 0.12 if (o.branch_id == "B03" and o.date >= pd.Timestamp("2025-04-01")) else 0.07
    for status, p in (("No-show", noshow_p), ("Cancelled", 0.10)):
        if rng.random() < p:
            lead2 = int(min(rng.geometric(0.15) - 1, 45))
            bid += 1
            bk_rows.append((f"BK{bid:06d}", o.date - pd.Timedelta(days=lead2), o.date, o.hour, o.branch_id, "C00000",
                            rng.choice(SOURCES, p=[.45, .30, .20, .05]), int(rng.choice(range(1, 9), p=COVERS_P)), status))
fact_bookings = pd.DataFrame(bk_rows, columns=["booking_id", "booking_created_date", "visit_date", "visit_hour", "branch_id", "customer_id",
                                               "booking_source", "party_size", "booking_status"])
fact_bookings["booking_created_date"] = fact_bookings[["booking_created_date"]].max(axis=1).clip(lower=pd.Timestamp("2024-01-01"))

# ----------------------------------------------------------------------------- fact_reviews
TOPICS = ["Food", "Service", "Value", "Ambience", "Speed"]
rv_rows = []
rid = 0
for o in dine.itertuples():
    if rng.random() >= 0.10:
        continue
    bad = o.branch_id == "B03" and o.date >= pd.Timestamp("2025-04-01")
    mean = {"B01": 4.3, "B02": 4.4, "B03": 4.2, "B04": 4.2}[o.branch_id] - (0.6 if bad else 0)
    rating = int(np.clip(round(rng.normal(mean, 0.9)), 1, 5))
    tp = np.array([.35, .25, .15, .15, .10]) if rating >= 4 else (np.array([.15, .35, .15, .05, .30]) if bad else np.array([.30, .25, .25, .10, .10]))
    rid += 1
    rv_rows.append((f"RV{rid:05d}", o.date + pd.Timedelta(days=int(rng.integers(0, 3))), o.branch_id,
                    rng.choice(["Google", "TripAdvisor", "OpenTable"], p=[.6, .25, .15]), rating, rng.choice(TOPICS, p=tp)))
fact_reviews = pd.DataFrame(rv_rows, columns=["review_id", "review_date", "branch_id", "platform", "rating", "main_topic"])
fact_reviews = fact_reviews[fact_reviews.review_date <= END]

# ----------------------------------------------------------------------------- fact_marketing_spend
ms_rows = []
msid = 0
for c in camps.itertuples():
    weeks = pd.date_range(c.start_date - pd.Timedelta(days=c.start_date.dayofweek), c.end_date, freq="W-MON")
    per_week = c.planned_budget / len(weeks)
    for w in weeks:
        spend = round(per_week * rng.uniform(0.85, 1.15), 2)
        cpm = {"Instagram": 6, "TikTok": 4, "Email": 1, "Google Ads": 9, "Uber Eats Ads": 7}[c.marketing_channel]
        impressions = int(spend / cpm * 1000)
        ctr = {"CMP005": 0.004, "CMP008": 0.006}.get(c.campaign_id, 0.012)
        msid += 1
        ms_rows.append((f"MS{msid:04d}", w, c.campaign_id, c.marketing_channel, spend, impressions, int(impressions * ctr * rng.uniform(.8, 1.2))))
fact_marketing_spend = pd.DataFrame(ms_rows, columns=["spend_id", "week_start_date", "campaign_id", "marketing_channel", "spend", "impressions", "clicks"])

# ----------------------------------------------------------------------------- fact_budget (monthly, per branch)
ms = fact_sales_lines.assign(month_start=fact_sales_lines.date.dt.to_period("M").dt.to_timestamp()).groupby(["branch_id", "month_start"]).net_amount.sum()
bud_rows = []
for b in dim_branch.branch_id:
    for m in pd.date_range("2024-01-01", "2026-12-01", freq="MS"):
        if m < open_dt[b].to_period("M").to_timestamp():
            continue
        ly = m - pd.DateOffset(years=1)
        if (b, ly) in ms.index and ms[(b, ly)] > 0 and not (b == "B04" and ly < pd.Timestamp("2025-07-01")):
            base = ms[(b, ly)] * 1.06
        elif b == "B04":
            ref = ms.get(("B01", m), ms.get(("B01", ly), 0) * 1.05)
            base = ref * 1.15  # optimistic new-site plan
        elif (b, m) in ms.index:
            base = ms[(b, m)] * rng.uniform(0.98, 1.06)
        else:
            base = ms.get((b, ly), 0) * 1.06
        sales = round(base, -1)
        bud_rows.append((b, m, sales, round(sales * 0.30, 2), round(sales * 0.28, 2)))
fact_budget = pd.DataFrame(bud_rows, columns=["branch_id", "month_start", "budget_net_sales", "budget_food_cost", "budget_labour_cost"])
fact_budget.insert(0, "budget_id", [f"BG{i:04d}" for i in range(1, len(fact_budget) + 1)])

# ----------------------------------------------------------------------------- write
dim_customer = pd.concat([non_member, dim_customer], ignore_index=True)
tables = {
    "dim_date": dim_date, "dim_time": dim_time, "dim_branch": dim_branch, "dim_channel": dim_channel,
    "dim_menu_item": dim_menu_item.drop(columns="_pop"), "dim_ingredient": dim_ingredient, "dim_supplier": dim_supplier,
    "bridge_recipe": bridge_recipe, "dim_campaign": dim_campaign.drop(columns="redeem"),
    "dim_customer": dim_customer.drop(columns="_w"), "dim_role": dim_role.drop(columns=["rate_mult", "cost_share"]),
    "fact_orders": fact_orders, "fact_sales_lines": fact_sales_lines, "fact_bookings": fact_bookings,
    "fact_labour_shifts": fact_labour_shifts, "fact_purchases": fact_purchases, "fact_wastage": fact_wastage,
    "fact_budget": fact_budget, "fact_marketing_spend": fact_marketing_spend, "fact_reviews": fact_reviews,
}
os.makedirs(os.path.join(OUT, "data"), exist_ok=True)
for name, df in tables.items():
    df.to_csv(os.path.join(OUT, "data", f"{name}.csv"), index=False, date_format="%Y-%m-%d")
    print(f"{name:22s} {len(df):>8,} rows")
