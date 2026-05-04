# seed_data.py
# Generates and inserts bulk sample data (≥ 5 rows per table as required)
# Run AFTER schema.sql has been executed.

import random
from datetime import date, timedelta
from db_connection import get_connection

# ── Helper ──────────────────────────────────────────────────

def rand_date(start_year=2023, end_year=2024):
    start = date(start_year, 1, 1)
    end   = date(end_year,   12, 31)
    return start + timedelta(days=random.randint(0, (end - start).days))


VIET_FIRST = ["Nguyen","Tran","Le","Pham","Hoang","Do","Vu","Bui","Dang","Ngo",
               "Duong","Ly","Ha","Dinh","Luu","Truong","Vo","Doan","Dam","Hua"]
VIET_MID   = ["Van","Thi","Duc","Minh","Quoc","Thanh","Tuan","Xuan","Kim","Ngoc"]
VIET_LAST  = ["An","Binh","Cuong","Dung","Em","Phong","Giang","Hoa","Ich","Kim",
               "Lam","Manh","Nam","Oanh","Phuc","Quang","Rong","Son","Thanh","Uyen"]
CITIES     = ["Hanoi","HCMC","Da Nang","Hue","Hai Phong","Can Tho","Vung Tau",
               "Nha Trang","Quy Nhon","Bien Hoa","Long Xuyen","Rach Gia"]
STREETS    = ["Le Loi","Nguyen Hue","Tran Phu","Bach Dang","Hung Vuong","Le Duan",
               "Tran Hung Dao","Nguyen Trai","Phan Chu Trinh","Ly Thuong Kiet"]
VEHICLE_TYPES    = ["Motorbike","Van","Truck","Pickup","Electric Bike"]
DRIVER_FIRST     = ["Nam","Hung","Minh","Tuan","Hai","Ba","Tu","Binh","Cuong","Duc"]
EXPENSE_TYPES    = ["Fuel","Toll","Handling","Maintenance","Other"]
ORDER_DESCS      = ["Electronics","Clothing","Food products","Medical supplies","Furniture",
                    "Books","Cosmetics","Auto parts","Kitchen equipment","Toys","Sporting goods",
                    "Office supplies","Industrial parts","Agricultural products","Chemicals"]

def rand_name():
    return f"{random.choice(VIET_FIRST)} {random.choice(VIET_MID)} {random.choice(VIET_LAST)}"

def rand_phone():
    return f"09{random.randint(10000000,99999999)}"

def rand_address():
    return f"{random.randint(1,200)} {random.choice(STREETS)}, {random.choice(CITIES)}"

def rand_plate():
    p1 = random.randint(10,99)
    l1 = random.choice("ABCDFGHJKLMNPQRSTUVWXY")
    l2 = random.randint(1,9)
    n  = random.randint(10000,99999)
    return f"{p1}{l1}{l2}-{n}"


def seed(num_customers=50, num_vehicles=20):
    conn = get_connection()
    cur  = conn.cursor()

    print("=" * 55)
    print("  DELIVERY SYSTEM — Bulk Sample Data Seeder")
    print("=" * 55)

    # ── Customers ──────────────────────────────────────────
    print(f"\n[1/5] Inserting {num_customers} customers …")
    cust_data = [(rand_name(), rand_phone(), rand_address()) for _ in range(num_customers)]
    cur.executemany(
        "INSERT INTO Customers (CustomerName, PhoneNumber, Address) VALUES (%s,%s,%s)",
        cust_data
    )
    conn.commit()
    print(f"      ✓ {cur.rowcount} customers inserted.")

    # ── Vehicles ───────────────────────────────────────────
    print(f"\n[2/5] Inserting {num_vehicles} vehicles …")
    plates = set()
    veh_data = []
    while len(veh_data) < num_vehicles:
        p = rand_plate()
        if p not in plates:
            plates.add(p)
            veh_data.append((random.choice(VEHICLE_TYPES), p, 1))
    cur.executemany(
        "INSERT INTO Vehicles (VehicleType, LicensePlate, IsAvailable) VALUES (%s,%s,%s)",
        veh_data
    )
    conn.commit()
    print(f"      ✓ {cur.rowcount} vehicles inserted.")

    # ── Get IDs ────────────────────────────────────────────
    cur.execute("SELECT CustomerID FROM Customers")
    customer_ids = [r[0] for r in cur.fetchall()]
    cur.execute("SELECT VehicleID FROM Vehicles")
    vehicle_ids  = [r[0] for r in cur.fetchall()]

    # ── Orders ─────────────────────────────────────────────
    num_orders = max(num_customers * 2, 100)
    print(f"\n[3/5] Inserting {num_orders} orders …")
    statuses = ["Pending","In Transit","Delivered","Cancelled"]
    weights  = [0.20, 0.15, 0.55, 0.10]
    ord_data = []
    for _ in range(num_orders):
        cid  = random.choice(customer_ids)
        odt  = rand_date()
        stat = random.choices(statuses, weights=weights, k=1)[0]
        desc = random.choice(ORDER_DESCS)
        ord_data.append((cid, odt, stat, desc))
    cur.executemany(
        "INSERT INTO Orders (CustomerID, OrderDate, Status, Description) VALUES (%s,%s,%s,%s)",
        ord_data
    )
    conn.commit()
    print(f"      ✓ {cur.rowcount} orders inserted.")

    # ── Deliveries (only for Delivered / In Transit orders) ─
    cur.execute("SELECT OrderID FROM Orders WHERE Status IN ('Delivered','In Transit')")
    eligible_order_ids = [r[0] for r in cur.fetchall()]

    # Check which orders already have a delivery
    cur.execute("SELECT OrderID FROM Deliveries")
    already_assigned = {r[0] for r in cur.fetchall()}
    to_assign = [oid for oid in eligible_order_ids if oid not in already_assigned]

    print(f"\n[4/5] Inserting deliveries for {len(to_assign)} orders …")
    del_data = []
    for oid in to_assign:
        vid      = random.choice(vehicle_ids)
        driver   = f"Driver {rand_name()}"
        del_date = rand_date()
        # status matches order status
        cur.execute("SELECT Status FROM Orders WHERE OrderID=%s", (oid,))
        row = cur.fetchone()
        if row is None:
            continue
        ostatus  = row[0]
        dstatus  = "Completed" if ostatus == "Delivered" else "In Transit"
        del_data.append((oid, vid, driver, del_date, dstatus))

    if del_data:
        cur.executemany(
            "INSERT INTO Deliveries (OrderID, VehicleID, DriverName, DeliveryDate, Status) "
            "VALUES (%s,%s,%s,%s,%s)",
            del_data
        )
        conn.commit()
        print(f"      ✓ {cur.rowcount} deliveries inserted.")

    # ── Expenses ───────────────────────────────────────────
    cur.execute("SELECT DeliveryID FROM Deliveries")
    delivery_ids = [r[0] for r in cur.fetchall()]

    print(f"\n[5/5] Inserting expenses …")
    exp_data = []
    for did in delivery_ids:
        num_exp = random.randint(1, 4)
        for _ in range(num_exp):
            etype  = random.choice(EXPENSE_TYPES)
            amount = round(random.uniform(20000, 500000), 2)
            note   = f"{etype} cost for delivery {did}"
            exp_data.append((did, etype, amount, note))

    cur.executemany(
        "INSERT INTO Expenses (DeliveryID, ExpenseType, Amount, Note) VALUES (%s,%s,%s,%s)",
        exp_data
    )
    conn.commit()
    print(f"      ✓ {cur.rowcount} expense records inserted.")

    # ── Summary ────────────────────────────────────────────
    print("\n" + "=" * 55)
    for tbl in ("Customers","Vehicles","Orders","Deliveries","Expenses"):
        cur.execute(f"SELECT COUNT(*) FROM {tbl}")
        cnt = cur.fetchone()[0]
        print(f"  {tbl:<14}: {cnt:>5} rows")
    print("=" * 55)
    print("  Seeding complete!\n")

    cur.close()
    conn.close()


if __name__ == "__main__":
    seed(num_customers=50, num_vehicles=20)