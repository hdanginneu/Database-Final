


## ⚙️ Setup Instructions

### Step 1 — Install Python dependency
```bash
pip install mysql-connector-python
```
Or using the requirements file:
```bash
pip install -r requirements.txt
```

### Step 2 — Configure Database Password
Open `db_connection.py` and edit the `DB_CONFIG` block:
```python
DB_CONFIG = {
    "host":     "localhost",
    "user":     "root",
    "password": "YOUR_MYSQL_PASSWORD_HERE",   # ← change this
    "database": "delivery_system",
}
```

### Step 3 — Create the Database
Open **MySQL Workbench** (or any MySQL client) and run:
```sql
source /path/to/schema.sql
```
Or paste the contents of `schema.sql` directly into MySQL Workbench and execute.

### Step 4 — Seed Sample Data (optional but recommended)
```bash
python seed_data.py
```
This inserts 50 customers, 20 vehicles, ~100 orders, deliveries, and expenses.

### Step 5 — Run the Application
```bash
python main.py
```

---

## 📁 File Structure

```
delivery_system/
├── schema.sql          ← DB schema, views, procedures, triggers, sample data
├── db_connection.py    ← MySQL connection config
├── seed_data.py        ← Bulk sample data generator
├── main.py             ← Main console application
├── requirements.txt    ← Python dependencies
└── README.md           ← This file
```

---

## 🗃️ Database Objects

### Tables
| Table | Description |
|-------|-------------|
| Customers | Customer profiles |
| Orders | Delivery orders |
| Deliveries | Delivery assignments |
| Vehicles | Transport vehicles |
| Expenses | Delivery-related costs |

### Views
| View | Description |
|------|-------------|
| vw_current_delivery_schedule | Active (non-completed) deliveries |
| vw_cost_per_order | Total cost aggregated per order |
| vw_outstanding_orders | Pending / In Transit orders |
| vw_vehicle_utilization | Per-vehicle delivery count & expenses |

### Stored Procedures
| Procedure | Description |
|-----------|-------------|
| sp_assign_delivery | Assign a vehicle to an order |
| sp_calculate_delivery_expenses | Full expense breakdown for a delivery |
| sp_monthly_report | Monthly KPI report |

### User-Defined Functions
| Function | Description |
|----------|-------------|
| fn_avg_delivery_cost(vehicle_id) | Average cost per delivery for a vehicle |
| fn_deliveries_per_vehicle(vehicle_id) | Total deliveries for a vehicle |
| fn_order_total_expense(order_id) | Total expenses for an order |

### Triggers
| Trigger | Description |
|---------|-------------|
| trg_delivery_completed | Auto-updates Order status & Vehicle availability on delivery completion |
| trg_validate_expense | Prevents negative expense amounts |

### DB Users / Roles
| User | Permissions |
|------|-------------|
| delivery_manager | Full access |
| dispatcher | Manage orders/deliveries/vehicles |
| accountant | Read orders/deliveries + full expense access |

---

##  Application Features

-  Customer CRUD (add, view, search, update, delete)
-  Order management (create, update status, cancel)
-  Delivery assignment via Stored Procedure
-  Real-time delivery schedule via View
-  Expense tracking (CRUD)
-  Vehicle utilization dashboard
-  Monthly performance report via Stored Procedure
-  UDF calls for vehicle stats
-  Export summary report to `.txt` file
