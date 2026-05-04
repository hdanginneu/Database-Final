# main.py
# Delivery Service Management System — Console Application
# Project 10 | DATCOM Lab | NEU College of Technology

import sys
from datetime import date
from db_connection import get_connection, test_connection

# ══════════════════════════════════════════════════════════════
#  DISPLAY HELPERS
# ══════════════════════════════════════════════════════════════

def clear():
    print("\n" + "=" * 60)

def print_table(headers, rows):
    """Pretty-print a list of tuples as a table."""
    if not rows:
        print("  (No records found)")
        return
    col_w = [len(str(h)) for h in headers]
    for row in rows:
        for i, val in enumerate(row):
            col_w[i] = max(col_w[i], len(str(val)))
    fmt = "  " + "  ".join(f"{{:<{w}}}" for w in col_w)
    sep = "  " + "  ".join("-" * w for w in col_w)
    print(sep)
    print(fmt.format(*headers))
    print(sep)
    for row in rows:
        print(fmt.format(*[str(v) if v is not None else "N/A" for v in row]))
    print(sep)
    print(f"  Total: {len(rows)} row(s)")

def input_int(prompt, min_val=None, max_val=None):
    while True:
        try:
            val = int(input(prompt))
            if min_val is not None and val < min_val:
                print(f"  ✗ Value must be ≥ {min_val}")
                continue
            if max_val is not None and val > max_val:
                print(f"  ✗ Value must be ≤ {max_val}")
                continue
            return val
        except ValueError:
            print("  ✗ Please enter a valid number.")

def input_float(prompt):
    while True:
        try:
            return float(input(prompt))
        except ValueError:
            print("  ✗ Please enter a valid number.")

def input_date(prompt):
    while True:
        s = input(prompt + " (YYYY-MM-DD): ").strip()
        try:
            return date.fromisoformat(s)
        except ValueError:
            print("  ✗ Invalid date format. Use YYYY-MM-DD.")

def pause():
    input("\n  Press Enter to continue…")

# ══════════════════════════════════════════════════════════════
#  CUSTOMER MANAGEMENT
# ══════════════════════════════════════════════════════════════

def menu_customers():
    while True:
        clear()
        print("  ┌─ CUSTOMER MANAGEMENT ─────────────────────────┐")
        print("  │  1. List all customers                         │")
        print("  │  2. Search customer                            │")
        print("  │  3. Add customer                               │")
        print("  │  4. Update customer                            │")
        print("  │  5. Delete customer                            │")
        print("  │  0. Back                                       │")
        print("  └────────────────────────────────────────────────┘")
        ch = input("  Choice: ").strip()
        if   ch == "1": list_customers()
        elif ch == "2": search_customer()
        elif ch == "3": add_customer()
        elif ch == "4": update_customer()
        elif ch == "5": delete_customer()
        elif ch == "0": break
        else: print("  ✗ Invalid option.")

def list_customers():
    clear()
    print("  ── ALL CUSTOMERS ──")
    conn = get_connection(); cur = conn.cursor()
    cur.execute("SELECT CustomerID, CustomerName, PhoneNumber, Address FROM Customers ORDER BY CustomerID")
    print_table(["ID","Name","Phone","Address"], cur.fetchall())
    cur.close(); conn.close(); pause()

def search_customer():
    clear()
    print("  ── SEARCH CUSTOMER ──")
    keyword = input("  Enter name or phone: ").strip()
    conn = get_connection(); cur = conn.cursor()
    cur.execute(
        "SELECT CustomerID, CustomerName, PhoneNumber, Address FROM Customers "
        "WHERE CustomerName LIKE %s OR PhoneNumber LIKE %s ORDER BY CustomerID",
        (f"%{keyword}%", f"%{keyword}%")
    )
    print_table(["ID","Name","Phone","Address"], cur.fetchall())
    cur.close(); conn.close(); pause()

def add_customer():
    clear()
    print("  ── ADD CUSTOMER ──")
    name  = input("  Full name  : ").strip()
    phone = input("  Phone      : ").strip()
    addr  = input("  Address    : ").strip()
    if not name or not phone or not addr:
        print("  ✗ All fields are required.")
        pause(); return
    conn = get_connection(); cur = conn.cursor()
    cur.execute(
        "INSERT INTO Customers (CustomerName, PhoneNumber, Address) VALUES (%s,%s,%s)",
        (name, phone, addr)
    )
    conn.commit()
    print(f"  ✓ Customer added with ID={cur.lastrowid}")
    cur.close(); conn.close(); pause()

def update_customer():
    clear()
    print("  ── UPDATE CUSTOMER ──")
    cid = input_int("  Customer ID: ", min_val=1)
    conn = get_connection(); cur = conn.cursor()
    cur.execute("SELECT CustomerName, PhoneNumber, Address FROM Customers WHERE CustomerID=%s", (cid,))
    row = cur.fetchone()
    if not row:
        print("  ✗ Customer not found."); cur.close(); conn.close(); pause(); return
    print(f"  Current: Name={row[0]}, Phone={row[1]}, Address={row[2]}")
    name  = input(f"  New name   [{row[0]}]: ").strip() or row[0]
    phone = input(f"  New phone  [{row[1]}]: ").strip() or row[1]
    addr  = input(f"  New address[{row[2]}]: ").strip() or row[2]
    cur.execute(
        "UPDATE Customers SET CustomerName=%s, PhoneNumber=%s, Address=%s WHERE CustomerID=%s",
        (name, phone, addr, cid)
    )
    conn.commit()
    print("  ✓ Customer updated.")
    cur.close(); conn.close(); pause()

def delete_customer():
    clear()
    print("  ── DELETE CUSTOMER ──")
    cid = input_int("  Customer ID: ", min_val=1)
    conn = get_connection(); cur = conn.cursor()
    cur.execute("SELECT CustomerName FROM Customers WHERE CustomerID=%s", (cid,))
    row = cur.fetchone()
    if not row:
        print("  ✗ Customer not found."); cur.close(); conn.close(); pause(); return
    confirm = input(f"  Delete '{row[0]}'? (yes/no): ").strip().lower()
    if confirm == "yes":
        cur.execute("DELETE FROM Customers WHERE CustomerID=%s", (cid,))
        conn.commit()
        print("  ✓ Customer deleted.")
    else:
        print("  Cancelled.")
    cur.close(); conn.close(); pause()

# ══════════════════════════════════════════════════════════════
#  ORDER MANAGEMENT
# ══════════════════════════════════════════════════════════════

def menu_orders():
    while True:
        clear()
        print("  ┌─ ORDER MANAGEMENT ────────────────────────────┐")
        print("  │  1. List all orders                            │")
        print("  │  2. View order details                         │")
        print("  │  3. Create new order                           │")
        print("  │  4. Update order status                        │")
        print("  │  5. Cancel order                               │")
        print("  │  6. List outstanding orders (view)             │")
        print("  │  0. Back                                       │")
        print("  └────────────────────────────────────────────────┘")
        ch = input("  Choice: ").strip()
        if   ch == "1": list_orders()
        elif ch == "2": view_order()
        elif ch == "3": create_order()
        elif ch == "4": update_order_status()
        elif ch == "5": cancel_order()
        elif ch == "6": list_outstanding_orders()
        elif ch == "0": break
        else: print("  ✗ Invalid option.")

def list_orders():
    clear()
    print("  ── ALL ORDERS ──")
    conn = get_connection(); cur = conn.cursor()
    cur.execute(
        "SELECT o.OrderID, c.CustomerName, o.OrderDate, o.Status, o.Description "
        "FROM Orders o JOIN Customers c ON o.CustomerID=c.CustomerID ORDER BY o.OrderID DESC LIMIT 100"
    )
    print_table(["OrderID","Customer","Date","Status","Description"], cur.fetchall())
    cur.close(); conn.close(); pause()

def view_order():
    clear()
    print("  ── ORDER DETAILS ──")
    oid = input_int("  Order ID: ", min_val=1)
    conn = get_connection(); cur = conn.cursor()
    cur.execute(
        "SELECT o.OrderID, c.CustomerName, c.PhoneNumber, c.Address, "
        "o.OrderDate, o.Status, o.Description "
        "FROM Orders o JOIN Customers c ON o.CustomerID=c.CustomerID WHERE o.OrderID=%s",
        (oid,)
    )
    row = cur.fetchone()
    if not row:
        print("  ✗ Order not found."); cur.close(); conn.close(); pause(); return
    labels = ["Order ID","Customer","Phone","Address","Date","Status","Description"]
    for lbl, val in zip(labels, row):
        print(f"  {lbl:<14}: {val}")

    # Show linked delivery
    cur.execute(
        "SELECT d.DeliveryID, v.VehicleType, v.LicensePlate, d.DriverName, "
        "d.DeliveryDate, d.Status FROM Deliveries d "
        "JOIN Vehicles v ON d.VehicleID=v.VehicleID WHERE d.OrderID=%s", (oid,)
    )
    d = cur.fetchone()
    if d:
        print(f"\n  {'--- Delivery ---':}")
        for lbl, val in zip(["DeliveryID","Vehicle","Plate","Driver","Date","Status"], d):
            print(f"  {lbl:<14}: {val}")

    # Show expenses via function
    cur.execute("SELECT fn_order_total_expense(%s)", (oid,))
    total = cur.fetchone()[0]
    print(f"\n  Total Expense  : {total:,.0f} VND")
    cur.close(); conn.close(); pause()

def create_order():
    clear()
    print("  ── CREATE NEW ORDER ──")
    cid  = input_int("  Customer ID : ", min_val=1)
    conn = get_connection(); cur = conn.cursor()
    cur.execute("SELECT CustomerName FROM Customers WHERE CustomerID=%s", (cid,))
    row = cur.fetchone()
    if not row:
        print("  ✗ Customer not found."); cur.close(); conn.close(); pause(); return
    print(f"  Customer: {row[0]}")
    odate = input_date("  Order date  ")
    desc  = input("  Description: ").strip()
    cur.execute(
        "INSERT INTO Orders (CustomerID, OrderDate, Status, Description) VALUES (%s,%s,'Pending',%s)",
        (cid, odate, desc)
    )
    conn.commit()
    print(f"  ✓ Order created with ID={cur.lastrowid}")
    cur.close(); conn.close(); pause()

def update_order_status():
    clear()
    print("  ── UPDATE ORDER STATUS ──")
    oid = input_int("  Order ID: ", min_val=1)
    conn = get_connection(); cur = conn.cursor()
    cur.execute("SELECT Status FROM Orders WHERE OrderID=%s", (oid,))
    row = cur.fetchone()
    if not row:
        print("  ✗ Order not found."); cur.close(); conn.close(); pause(); return
    print(f"  Current status: {row[0]}")
    print("  Statuses: 1=Pending  2=In Transit  3=Delivered  4=Cancelled")
    s_map = {"1":"Pending","2":"In Transit","3":"Delivered","4":"Cancelled"}
    ch = input("  New status: ").strip()
    if ch not in s_map:
        print("  ✗ Invalid choice."); cur.close(); conn.close(); pause(); return
    cur.execute("UPDATE Orders SET Status=%s WHERE OrderID=%s", (s_map[ch], oid))
    conn.commit()
    print(f"  ✓ Status updated to '{s_map[ch]}'.")
    cur.close(); conn.close(); pause()

def cancel_order():
    clear()
    print("  ── CANCEL ORDER ──")
    oid = input_int("  Order ID: ", min_val=1)
    conn = get_connection(); cur = conn.cursor()
    cur.execute("SELECT Status FROM Orders WHERE OrderID=%s", (oid,))
    row = cur.fetchone()
    if not row:
        print("  ✗ Order not found."); cur.close(); conn.close(); pause(); return
    if row[0] == "Delivered":
        print("  ✗ Cannot cancel a delivered order."); cur.close(); conn.close(); pause(); return
    cur.execute("UPDATE Orders SET Status='Cancelled' WHERE OrderID=%s", (oid,))
    conn.commit()
    print("  ✓ Order cancelled.")
    cur.close(); conn.close(); pause()

def list_outstanding_orders():
    clear()
    print("  ── OUTSTANDING ORDERS (View) ──")
    conn = get_connection(); cur = conn.cursor()
    cur.execute("SELECT * FROM vw_outstanding_orders ORDER BY OrderID DESC LIMIT 50")
    print_table(["OrderID","Customer","Phone","Date","Status","Description"], cur.fetchall())
    cur.close(); conn.close(); pause()

# ══════════════════════════════════════════════════════════════
#  DELIVERY MANAGEMENT
# ══════════════════════════════════════════════════════════════

def menu_deliveries():
    while True:
        clear()
        print("  ┌─ DELIVERY MANAGEMENT ─────────────────────────┐")
        print("  │  1. View current schedule (view)               │")
        print("  │  2. Assign delivery to order (procedure)       │")
        print("  │  3. Update delivery status                     │")
        print("  │  4. View delivery expenses                     │")
        print("  │  5. List all deliveries                        │")
        print("  │  0. Back                                       │")
        print("  └────────────────────────────────────────────────┘")
        ch = input("  Choice: ").strip()
        if   ch == "1": view_delivery_schedule()
        elif ch == "2": assign_delivery()
        elif ch == "3": update_delivery_status()
        elif ch == "4": view_delivery_expenses()
        elif ch == "5": list_deliveries()
        elif ch == "0": break
        else: print("  ✗ Invalid option.")

def view_delivery_schedule():
    clear()
    print("  ── CURRENT DELIVERY SCHEDULE ──")
    conn = get_connection(); cur = conn.cursor()
    cur.execute("SELECT DeliveryID, CustomerName, PhoneNumber, DeliveryAddress, "
                "VehicleType, LicensePlate, DriverName, DeliveryDate, DeliveryStatus "
                "FROM vw_current_delivery_schedule ORDER BY DeliveryDate")
    print_table(
        ["DelID","Customer","Phone","Address","VehicleType","Plate","Driver","Date","Status"],
        cur.fetchall()
    )
    cur.close(); conn.close(); pause()

def assign_delivery():
    clear()
    print("  ── ASSIGN DELIVERY (Stored Procedure) ──")
    oid  = input_int("  Order ID   : ", min_val=1)
    # Show available vehicles
    conn = get_connection(); cur = conn.cursor()
    cur.execute("SELECT VehicleID, VehicleType, LicensePlate FROM Vehicles WHERE IsAvailable=1")
    rows = cur.fetchall()
    if not rows:
        print("  ✗ No vehicles available."); cur.close(); conn.close(); pause(); return
    print_table(["VehicleID","Type","Plate"], rows)
    vid    = input_int("  Vehicle ID : ", min_val=1)
    driver = input("  Driver name: ").strip()
    ddate  = input_date("  Delivery date")
    try:
        cur.callproc("sp_assign_delivery", (oid, vid, driver, str(ddate)))
        conn.commit()
        for result in cur.stored_results():
            row = result.fetchone()
            if row:
                print(f"  ✓ {row[0]}  →  Delivery ID={row[1]}")
    except Exception as e:
        print(f"  ✗ Error: {e}")
    cur.close(); conn.close(); pause()

def update_delivery_status():
    clear()
    print("  ── UPDATE DELIVERY STATUS ──")
    did = input_int("  Delivery ID: ", min_val=1)
    conn = get_connection(); cur = conn.cursor()
    cur.execute("SELECT Status FROM Deliveries WHERE DeliveryID=%s", (did,))
    row = cur.fetchone()
    if not row:
        print("  ✗ Delivery not found."); cur.close(); conn.close(); pause(); return
    print(f"  Current status: {row[0]}")
    print("  1=Scheduled  2=In Transit  3=Completed  4=Failed")
    s_map = {"1":"Scheduled","2":"In Transit","3":"Completed","4":"Failed"}
    ch = input("  New status: ").strip()
    if ch not in s_map:
        print("  ✗ Invalid choice."); cur.close(); conn.close(); pause(); return
    cur.execute("UPDATE Deliveries SET Status=%s WHERE DeliveryID=%s", (s_map[ch], did))
    conn.commit()
    print(f"  ✓ Delivery status updated to '{s_map[ch]}'.")
    print("    (Trigger will auto-update Order status and Vehicle availability)")
    cur.close(); conn.close(); pause()

def view_delivery_expenses():
    clear()
    print("  ── DELIVERY EXPENSES (Stored Procedure) ──")
    did = input_int("  Delivery ID: ", min_val=1)
    conn = get_connection(); cur = conn.cursor()
    try:
        cur.callproc("sp_calculate_delivery_expenses", (did,))
        for result in cur.stored_results():
            row = result.fetchone()
            if row:
                labels = ["DeliveryID","OrderID","Customer","Total","Fuel","Toll","Handling","Maintenance","Other"]
                for lbl, val in zip(labels, row):
                    print(f"  {lbl:<14}: {float(val):,.0f} VND" if isinstance(val, (int,float)) and lbl!="Customer" else f"  {lbl:<14}: {val}")
            else:
                print("  ✗ Delivery not found.")
    except Exception as e:
        print(f"  ✗ Error: {e}")
    cur.close(); conn.close(); pause()

def list_deliveries():
    clear()
    print("  ── ALL DELIVERIES ──")
    conn = get_connection(); cur = conn.cursor()
    cur.execute(
        "SELECT d.DeliveryID, o.OrderID, v.LicensePlate, d.DriverName, d.DeliveryDate, d.Status "
        "FROM Deliveries d "
        "JOIN Orders o ON d.OrderID=o.OrderID "
        "JOIN Vehicles v ON d.VehicleID=v.VehicleID ORDER BY d.DeliveryID DESC LIMIT 100"
    )
    print_table(["DelID","OrderID","Plate","Driver","Date","Status"], cur.fetchall())
    cur.close(); conn.close(); pause()

# ══════════════════════════════════════════════════════════════
#  VEHICLE MANAGEMENT
# ══════════════════════════════════════════════════════════════

def menu_vehicles():
    while True:
        clear()
        print("  ┌─ VEHICLE MANAGEMENT ──────────────────────────┐")
        print("  │  1. List all vehicles                          │")
        print("  │  2. Add vehicle                                │")
        print("  │  3. Update vehicle                             │")
        print("  │  4. Vehicle utilization (view)                 │")
        print("  │  5. Deliveries per vehicle (function)          │")
        print("  │  6. Avg delivery cost per vehicle (function)   │")
        print("  │  0. Back                                       │")
        print("  └────────────────────────────────────────────────┘")
        ch = input("  Choice: ").strip()
        if   ch == "1": list_vehicles()
        elif ch == "2": add_vehicle()
        elif ch == "3": update_vehicle()
        elif ch == "4": vehicle_utilization()
        elif ch == "5": deliveries_per_vehicle()
        elif ch == "6": avg_cost_per_vehicle()
        elif ch == "0": break
        else: print("  ✗ Invalid option.")

def list_vehicles():
    clear()
    print("  ── ALL VEHICLES ──")
    conn = get_connection(); cur = conn.cursor()
    cur.execute("SELECT VehicleID, VehicleType, LicensePlate, "
                "CASE IsAvailable WHEN 1 THEN 'Available' ELSE 'In Use' END AS Status "
                "FROM Vehicles ORDER BY VehicleID")
    print_table(["VehicleID","Type","Plate","Status"], cur.fetchall())
    cur.close(); conn.close(); pause()

def add_vehicle():
    clear()
    print("  ── ADD VEHICLE ──")
    print("  Types: Motorbike / Van / Truck / Pickup / Electric Bike")
    vtype = input("  Vehicle type : ").strip()
    plate = input("  License plate: ").strip()
    conn = get_connection(); cur = conn.cursor()
    try:
        cur.execute("INSERT INTO Vehicles (VehicleType, LicensePlate) VALUES (%s,%s)", (vtype, plate))
        conn.commit()
        print(f"  ✓ Vehicle added with ID={cur.lastrowid}")
    except Exception as e:
        print(f"  ✗ Error: {e}")
    cur.close(); conn.close(); pause()

def update_vehicle():
    clear()
    print("  ── UPDATE VEHICLE ──")
    vid = input_int("  Vehicle ID: ", min_val=1)
    conn = get_connection(); cur = conn.cursor()
    cur.execute("SELECT VehicleType, LicensePlate, IsAvailable FROM Vehicles WHERE VehicleID=%s", (vid,))
    row = cur.fetchone()
    if not row:
        print("  ✗ Vehicle not found."); cur.close(); conn.close(); pause(); return
    vtype = input(f"  Type    [{row[0]}]: ").strip() or row[0]
    plate = input(f"  Plate   [{row[1]}]: ").strip() or row[1]
    cur.execute("UPDATE Vehicles SET VehicleType=%s, LicensePlate=%s WHERE VehicleID=%s", (vtype, plate, vid))
    conn.commit()
    print("  ✓ Vehicle updated.")
    cur.close(); conn.close(); pause()

def vehicle_utilization():
    clear()
    print("  ── VEHICLE UTILIZATION (View) ──")
    conn = get_connection(); cur = conn.cursor()
    cur.execute("SELECT VehicleID, VehicleType, LicensePlate, "
                "CASE IsAvailable WHEN 1 THEN 'Available' ELSE 'In Use' END, "
                "TotalDeliveries, TotalExpenses FROM vw_vehicle_utilization ORDER BY TotalDeliveries DESC")
    print_table(["ID","Type","Plate","Status","Deliveries","TotalExpenses"], cur.fetchall())
    cur.close(); conn.close(); pause()

def deliveries_per_vehicle():
    clear()
    print("  ── DELIVERIES PER VEHICLE (UDF) ──")
    vid = input_int("  Vehicle ID: ", min_val=1)
    conn = get_connection(); cur = conn.cursor()
    cur.execute("SELECT fn_deliveries_per_vehicle(%s)", (vid,))
    cnt = cur.fetchone()[0]
    print(f"  Vehicle {vid} has completed {cnt} delivery(ies).")
    cur.close(); conn.close(); pause()

def avg_cost_per_vehicle():
    clear()
    print("  ── AVERAGE DELIVERY COST (UDF) ──")
    vid = input_int("  Vehicle ID: ", min_val=1)
    conn = get_connection(); cur = conn.cursor()
    cur.execute("SELECT fn_avg_delivery_cost(%s)", (vid,))
    avg = cur.fetchone()[0]
    print(f"  Average delivery cost for Vehicle {vid}: {float(avg):,.2f} VND")
    cur.close(); conn.close(); pause()

# ══════════════════════════════════════════════════════════════
#  EXPENSE MANAGEMENT
# ══════════════════════════════════════════════════════════════

def menu_expenses():
    while True:
        clear()
        print("  ┌─ EXPENSE MANAGEMENT ──────────────────────────┐")
        print("  │  1. List expenses for a delivery               │")
        print("  │  2. Add expense                                │")
        print("  │  3. Update expense                             │")
        print("  │  4. Delete expense                             │")
        print("  │  5. Cost per order (view)                      │")
        print("  │  0. Back                                       │")
        print("  └────────────────────────────────────────────────┘")
        ch = input("  Choice: ").strip()
        if   ch == "1": list_expenses()
        elif ch == "2": add_expense()
        elif ch == "3": update_expense()
        elif ch == "4": delete_expense()
        elif ch == "5": cost_per_order()
        elif ch == "0": break
        else: print("  ✗ Invalid option.")

def list_expenses():
    clear()
    print("  ── EXPENSES FOR DELIVERY ──")
    did = input_int("  Delivery ID (0=all): ", min_val=0)
    conn = get_connection(); cur = conn.cursor()
    if did == 0:
        cur.execute("SELECT ExpenseID, DeliveryID, ExpenseType, Amount, Note FROM Expenses ORDER BY DeliveryID LIMIT 100")
    else:
        cur.execute("SELECT ExpenseID, DeliveryID, ExpenseType, Amount, Note FROM Expenses WHERE DeliveryID=%s", (did,))
    print_table(["ExpID","DelID","Type","Amount (VND)","Note"], cur.fetchall())
    cur.close(); conn.close(); pause()

def add_expense():
    clear()
    print("  ── ADD EXPENSE ──")
    did    = input_int("  Delivery ID: ", min_val=1)
    print("  Types: Fuel / Toll / Handling / Maintenance / Other")
    etype  = input("  Expense type: ").strip()
    amount = input_float("  Amount (VND): ")
    note   = input("  Note        : ").strip()
    conn = get_connection(); cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO Expenses (DeliveryID, ExpenseType, Amount, Note) VALUES (%s,%s,%s,%s)",
            (did, etype, amount, note)
        )
        conn.commit()
        print(f"  ✓ Expense added with ID={cur.lastrowid}")
    except Exception as e:
        print(f"  ✗ Error: {e}")
    cur.close(); conn.close(); pause()

def update_expense():
    clear()
    print("  ── UPDATE EXPENSE ──")
    eid = input_int("  Expense ID: ", min_val=1)
    conn = get_connection(); cur = conn.cursor()
    cur.execute("SELECT ExpenseType, Amount, Note FROM Expenses WHERE ExpenseID=%s", (eid,))
    row = cur.fetchone()
    if not row:
        print("  ✗ Expense not found."); cur.close(); conn.close(); pause(); return
    etype  = input(f"  Type   [{row[0]}]: ").strip() or row[0]
    amt_in = input(f"  Amount [{row[1]}]: ").strip()
    amount = float(amt_in) if amt_in else row[1]
    note   = input(f"  Note   [{row[2]}]: ").strip() or row[2]
    cur.execute("UPDATE Expenses SET ExpenseType=%s, Amount=%s, Note=%s WHERE ExpenseID=%s",
                (etype, amount, note, eid))
    conn.commit()
    print("  ✓ Expense updated.")
    cur.close(); conn.close(); pause()

def delete_expense():
    clear()
    print("  ── DELETE EXPENSE ──")
    eid = input_int("  Expense ID: ", min_val=1)
    conn = get_connection(); cur = conn.cursor()
    cur.execute("SELECT Amount, ExpenseType FROM Expenses WHERE ExpenseID=%s", (eid,))
    row = cur.fetchone()
    if not row:
        print("  ✗ Expense not found."); cur.close(); conn.close(); pause(); return
    confirm = input(f"  Delete {row[1]} ({row[0]} VND)? (yes/no): ").strip().lower()
    if confirm == "yes":
        cur.execute("DELETE FROM Expenses WHERE ExpenseID=%s", (eid,))
        conn.commit()
        print("  ✓ Expense deleted.")
    else:
        print("  Cancelled.")
    cur.close(); conn.close(); pause()

def cost_per_order():
    clear()
    print("  ── COST PER ORDER (View) ──")
    conn = get_connection(); cur = conn.cursor()
    cur.execute(
        "SELECT OrderID, CustomerName, OrderDate, OrderStatus, DeliveryID, TotalCost "
        "FROM vw_cost_per_order ORDER BY OrderID DESC LIMIT 50"
    )
    print_table(["OrderID","Customer","Date","Status","DelID","TotalCost"], cur.fetchall())
    cur.close(); conn.close(); pause()

# ══════════════════════════════════════════════════════════════
#  REPORTS
# ══════════════════════════════════════════════════════════════

def menu_reports():
    while True:
        clear()
        print("  ┌─ REPORTS ─────────────────────────────────────┐")
        print("  │  1. Monthly performance report (procedure)     │")
        print("  │  2. Delivery performance summary               │")
        print("  │  3. Cost breakdown by expense type             │")
        print("  │  4. Top 10 customers by order count            │")
        print("  │  5. Order status distribution                  │")
        print("  │  6. Export summary report to file              │")
        print("  │  0. Back                                       │")
        print("  └────────────────────────────────────────────────┘")
        ch = input("  Choice: ").strip()
        if   ch == "1": monthly_report()
        elif ch == "2": delivery_performance()
        elif ch == "3": cost_breakdown()
        elif ch == "4": top_customers()
        elif ch == "5": order_status_dist()
        elif ch == "6": export_report()
        elif ch == "0": break
        else: print("  ✗ Invalid option.")

def monthly_report():
    clear()
    print("  ── MONTHLY PERFORMANCE REPORT (Stored Procedure) ──")
    year  = input_int("  Year  (e.g. 2024): ", min_val=2000, max_val=2100)
    month = input_int("  Month (1-12)      : ", min_val=1, max_val=12)
    conn = get_connection(); cur = conn.cursor()
    cur.callproc("sp_monthly_report", (year, month))
    for result in cur.stored_results():
        row = result.fetchone()
        if row:
            labels = ["Total Orders","Delivered","Cancelled","Total Deliveries",
                      "Total Expenses (VND)","Avg Expense/Delivery (VND)"]
            print(f"\n  Report for {year}/{month:02d}:")
            print("  " + "-"*40)
            for lbl, val in zip(labels, row):
                print(f"  {lbl:<30}: {float(val):>12,.2f}" if isinstance(val, (int,float)) else f"  {lbl:<30}: {val}")
    cur.close(); conn.close(); pause()

def delivery_performance():
    clear()
    print("  ── DELIVERY PERFORMANCE ──")
    conn = get_connection(); cur = conn.cursor()
    cur.execute(
        "SELECT d.Status, COUNT(*) AS Count, "
        "COALESCE(AVG(total_exp.total), 0) AS AvgCost "
        "FROM Deliveries d "
        "LEFT JOIN (SELECT DeliveryID, SUM(Amount) AS total FROM Expenses GROUP BY DeliveryID) total_exp "
        "ON d.DeliveryID = total_exp.DeliveryID "
        "GROUP BY d.Status"
    )
    print_table(["Status","Count","AvgCost (VND)"], cur.fetchall())
    cur.close(); conn.close(); pause()

def cost_breakdown():
    clear()
    print("  ── COST BREAKDOWN BY EXPENSE TYPE ──")
    conn = get_connection(); cur = conn.cursor()
    cur.execute(
        "SELECT ExpenseType, COUNT(*) AS Records, SUM(Amount) AS Total, AVG(Amount) AS Average "
        "FROM Expenses GROUP BY ExpenseType ORDER BY Total DESC"
    )
    print_table(["Type","Records","Total (VND)","Average (VND)"], cur.fetchall())
    cur.close(); conn.close(); pause()

def top_customers():
    clear()
    print("  ── TOP 10 CUSTOMERS BY ORDER COUNT ──")
    conn = get_connection(); cur = conn.cursor()
    cur.execute(
        "SELECT c.CustomerID, c.CustomerName, COUNT(o.OrderID) AS Orders, "
        "SUM(CASE WHEN o.Status='Delivered' THEN 1 ELSE 0 END) AS Delivered "
        "FROM Customers c LEFT JOIN Orders o ON c.CustomerID=o.CustomerID "
        "GROUP BY c.CustomerID, c.CustomerName ORDER BY Orders DESC LIMIT 10"
    )
    print_table(["ID","Name","Total Orders","Delivered"], cur.fetchall())
    cur.close(); conn.close(); pause()

def order_status_dist():
    clear()
    print("  ── ORDER STATUS DISTRIBUTION ──")
    conn = get_connection(); cur = conn.cursor()
    cur.execute("SELECT Status, COUNT(*) AS Count FROM Orders GROUP BY Status ORDER BY Count DESC")
    rows = cur.fetchall()
    print_table(["Status","Count"], rows)
    total = sum(r[1] for r in rows)
    print(f"\n  Total orders: {total}")
    for r in rows:
        pct = (r[1] / total * 100) if total else 0
        bar = "█" * int(pct // 2)
        print(f"  {r[0]:<12}  {bar} {pct:.1f}%")
    cur.close(); conn.close(); pause()

def export_report():
    clear()
    print("  ── EXPORT SUMMARY REPORT ──")
    filename = f"delivery_report_{date.today()}.txt"
    conn = get_connection(); cur = conn.cursor()

    lines = []
    lines.append("=" * 60)
    lines.append("  DELIVERY SERVICE MANAGEMENT SYSTEM — Summary Report")
    lines.append(f"  Generated: {date.today()}")
    lines.append("=" * 60)

    # Orders summary
    cur.execute("SELECT Status, COUNT(*) FROM Orders GROUP BY Status")
    lines.append("\n  ORDER STATUS SUMMARY")
    lines.append("  " + "-"*40)
    for row in cur.fetchall():
        lines.append(f"  {row[0]:<15}: {row[1]}")

    # Expense summary
    cur.execute("SELECT ExpenseType, SUM(Amount) FROM Expenses GROUP BY ExpenseType")
    lines.append("\n  EXPENSE BREAKDOWN")
    lines.append("  " + "-"*40)
    for row in cur.fetchall():
        lines.append(f"  {row[0]:<15}: {float(row[1]):>12,.2f} VND")

    # Top vehicles
    cur.execute(
        "SELECT v.LicensePlate, COUNT(d.DeliveryID) FROM Vehicles v "
        "LEFT JOIN Deliveries d ON v.VehicleID=d.VehicleID GROUP BY v.VehicleID ORDER BY 2 DESC LIMIT 5"
    )
    lines.append("\n  TOP 5 VEHICLES BY DELIVERIES")
    lines.append("  " + "-"*40)
    for row in cur.fetchall():
        lines.append(f"  {row[0]:<20}: {row[1]} deliveries")

    lines.append("\n" + "=" * 60)

    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"  ✓ Report exported to '{filename}'")
    cur.close(); conn.close(); pause()

# ══════════════════════════════════════════════════════════════
#  MAIN MENU
# ══════════════════════════════════════════════════════════════

def main():
    print("\n" + "═" * 60)
    print("  DELIVERY SERVICE MANAGEMENT SYSTEM")
    print("  Project 10 | DATCOM Lab | NEU College of Technology")
    print("═" * 60)

    if not test_connection():
        print("\n  [!] Cannot connect to database.")
        print("      1. Make sure MySQL is running.")
        print("      2. Run 'schema.sql' to create the database.")
        print("      3. Update DB_CONFIG in db_connection.py if needed.")
        sys.exit(1)

    while True:
        clear()
        print("  ┌─ MAIN MENU ────────────────────────────────────┐")
        print("  │  1. Customer Management                         │")
        print("  │  2. Order Management                            │")
        print("  │  3. Delivery Management                         │")
        print("  │  4. Vehicle Management                          │")
        print("  │  5. Expense Management                          │")
        print("  │  6. Reports                                     │")
        print("  │  0. Exit                                        │")
        print("  └─────────────────────────────────────────────────┘")
        ch = input("  Choice: ").strip()
        if   ch == "1": menu_customers()
        elif ch == "2": menu_orders()
        elif ch == "3": menu_deliveries()
        elif ch == "4": menu_vehicles()
        elif ch == "5": menu_expenses()
        elif ch == "6": menu_reports()
        elif ch == "0":
            print("\n  Goodbye! 👋\n")
            break
        else:
            print("  ✗ Invalid option.")


if __name__ == "__main__":
    main()