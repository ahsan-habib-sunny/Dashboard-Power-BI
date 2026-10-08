# LQ Dining – Restaurant Performance Dashboard (Power BI)

An end-to-end Power BI report for a fictional four-branch restaurant group in Manchester. It turns raw sales, kitchen, labour, booking and marketing data into decision-ready pages for the owner, operations, marketing, head chefs and finance, and it shows the business is not as healthy as its headline growth suggests.

> All data is synthetic, generated in Python to behave like a real UK casual-dining business. No real company data is used.

![Executive Overview](screenshots/01_executive_overview.png)

---

## The business question

Total sales are up **21% year on year**. The owner wants to know:

- Is the business really growing, or is a new branch hiding problems?
- Where is money being lost: food, labour, waste or marketing?
- Which branch needs attention, and why?

## Key findings (Jan–Sep 2026)

| Finding | Evidence |
|---|---|
| **Growth comes from the new site, not the existing estate** | Net sales +21.2% YoY, but **like-for-like sales −4.1%**. Salford Quays (opened Jun 2025) is now the #1 branch. |
| **The group is behind plan** | Net sales **3.4% below budget**. |
| **Food cost is above target** | Actual food cost **32.9%** vs a 30% target (about £11.7k of lost margin) and vs **26.5% theoretical** from recipes. Meat is the largest spend, so the late-2025 meat price rise hit hardest. |
| **Didsbury is the problem branch** | LFL **−6.7%**, prime cost **69.2%** (group 61.7%), labour **34.2%** (group 28.8%), waste **0.92%** of sales (group 0.38%), rating **3.46** (group 4.10), no-shows **11.3%** (group 7.6%). Complaints are mainly about speed and service. |
| **The best marketing was cheap and targeted** | Summer Cocktail Hour returned **+412% ROI**; the £8.7k Influencer Takeover lost **−77%**. The best-performing campaign was not repeated in 2026. |
| **Loyalty is improving** | **43.9%** of active members in 2026 were returning customers, up from 32.6% in 2025. |

### Recommendations

1. Treat Didsbury as an operational turnaround: realign the rota to its lower sales, and tackle kitchen waste and service speed.
2. Review prices on popular, low-margin dishes ("Plowhorses" such as Fish & Chips and the Classic Burger).
3. Bring back proven low-cost campaigns and stop high-spend influencer activity.

---

## Report pages

| Page | Audience | Answers |
|---|---|---|
| **Executive Overview** | Owner / directors | Are we growing, profitable and on plan? |
| **Sales & Operations** | Ops / general managers | When are we busy, what do guests spend, which channels? |
| **Marketing & Customers** | Marketing | Which campaigns paid off, are guests returning, what do reviews say? |
| **Kitchen & Menu** | Head chefs | Are we cooking to recipe, what is wasted, which dishes earn their place? |
| **Finance & Labour** | Finance / ops directors | Are wages under control, and what is left after food and labour? |
| **Branch Detail** (drill-through) | Anyone | Right-click any branch to see its full story against the group. |

| | |
|---|---|
| ![Sales & Operations](screenshots/02_sales_operations.png) | ![Marketing & Customers](screenshots/03_marketing_customers.png) |
| ![Kitchen & Menu](screenshots/04_kitchen_menu.png) | ![Finance & Labour](screenshots/05_finance_labour.png) |
| ![Branch Detail – Didsbury](screenshots/06_branch_detail_didsbury.png) | ![Drill-through](screenshots/07_drill_through.png) |

---

## Data model

A star schema with **9 fact tables, 10 dimensions and 1 bridge table**: 36 one-to-many, single-direction relationships around a shared date table.

| Fact table | Grain (one row = …) | Rows |
|---|---|---|
| fact_sales_lines | one dish/drink on an order | ~115k |
| fact_orders | one order (holds covers) | ~16k |
| fact_labour_shifts | one role's hours at a branch on a day | ~23k |
| fact_purchases | one ingredient delivery line | ~20k |
| fact_bookings | one table booking | ~7k |
| fact_wastage | one waste log entry | ~4k |
| fact_reviews | one online review | ~1.1k |
| fact_budget | branch × month target | 127 |
| fact_marketing_spend | campaign × week spend | 58 |

**Dimensions:** date, time, branch, channel, menu item, ingredient, supplier, campaign, customer, role. **Bridge:** recipe (dish → ingredient → quantity per portion).

![Data model](screenshots/00_data_model.png)

### Modelling decisions

- **Covers stored at order grain**, not on sales lines, to avoid double-counting guests (a table of 4 ordering 8 items is 4 covers, not 32).
- **Two date relationships to bookings:** visit date (active) and booking-created date (inactive, switched on with `USERELATIONSHIP`).
- **Monthly budget joined to a daily date table** at month start, and reported at month level or above.
- **Recipe bridge table** resolves the many-to-many between dishes and ingredients and drives theoretical food cost.
- **Placeholder dimension rows** (non-member customer, no campaign) so every fact row always matches a dimension row.

---

## DAX highlights

88 measures, organised into display folders (Sales, Time Intelligence, Kitchen, Labour, Marketing, Budget, Menu Engineering, Benchmarks).

| Technique | Where it is used |
|---|---|
| `CALCULATE` with `KEEPFILTERS` vs plain filters | Dine-in sales, campaign sales per campaign row |
| Time intelligence limited to dates with data | Net Sales LY / YoY / YTD, so a partial year is compared fairly |
| **Like-for-like sales** with `FILTER` over branches by opening date | LFL Net Sales and LFL YoY % |
| `ALL` vs `ALLSELECTED` vs `REMOVEFILTERS` | % of total vs % of selected, group benchmarks |
| `RANKX` with `HASONEVALUE` | Branch and dish rankings |
| Iterators (`SUMX`, `AVERAGEX`, `MINX`) with `RELATED` / `RELATEDTABLE` | Recipe cost, theoretical food cost, delivery commission, booking lead time |
| Context transition in a calculated column | Customer first order date, new vs returning customers |
| `USERELATIONSHIP` | Bookings by created date vs visit date |
| Menu engineering with `SWITCH(TRUE())` | Star / Plowhorse / Puzzle / Dog classification, coloured by a measure |
| Measure-driven formatting and titles | Dynamic drill-through title, conditional colours, constant lines bound to measures |

Example, like-for-like sales:

```dax
LFL Net Sales =
VAR DatesWithData =
    CALCULATETABLE ( VALUES ( dim_date[date] ), dim_date[has_sales_data] = TRUE () )
VAR FirstDateLY = MINX ( SAMEPERIODLASTYEAR ( DatesWithData ), dim_date[date] )
VAR LFLBranches = FILTER ( dim_branch, dim_branch[opening_date] <= FirstDateLY )
RETURN
    CALCULATE ( [Net Sales], LFLBranches )
```

---

## Report features

- **Drill-through** to a Branch Detail page that compares any branch with the group, while keeping the year slicer editable.
- **Row-level security:** a Branch Manager role filtered by `USERPRINCIPALNAME()`, so each manager sees only their own branch, plus a Head Office role with full access.
- **Synced slicers**, **edit interactions** (e.g. trend charts that ignore the year slicer) and page-specific filters.
- **Conditional formatting** driven by rules and by measures (colour by field value).

---

## Repository structure

```
├── LQ_Dining_Report.pbix        Power BI report
├── LQ_Dining_Report.pdf         PDF export of all pages
├── data/                        20 CSV files (star schema)
├── generate_data.py             Python script that creates the synthetic data
├── screenshots/                 Page images used in this README
└── README.md
```

## How to run it

1. Download or clone this repository.
2. Open `LQ_Dining_Report.pbix` in Power BI Desktop.
3. If prompted, point the data source to the `data/` folder (Transform data → Data source settings → Change source).
4. To regenerate the data: `python generate_data.py` (requires pandas and numpy).

## Tools

Power BI Desktop · DAX · Power Query · Python (pandas, NumPy)

## Limitations

- The data is a **sample**, at roughly 10–15 orders per branch per day, so absolute metrics such as RevPASH are lower than in a real restaurant. Ratios and trends are what matter.
- Theoretical food cost uses fixed 2024 ingredient prices, so part of the actual-vs-theoretical variance reflects supplier inflation rather than kitchen waste. Branches are therefore compared with each other.
- History starts in January 2024, so 2024 shows no returning customers.

---

**Author:** Ahsan · Business Intelligence / Data Analyst · Manchester, UK · [LinkedIn](https://www.linkedin.com/) · [GitHub](https://github.com/)
