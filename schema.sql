-- ============================================================
--  DELIVERY SERVICE MANAGEMENT SYSTEM - schema.sql
--  Project 10 | DATCOM Lab | NEU College of Technology
-- ============================================================

DROP DATABASE IF EXISTS delivery_system;
CREATE DATABASE delivery_system CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE delivery_system;

-- ============================================================
-- 1. TABLE STRUCTURES
-- ============================================================

CREATE TABLE Customers (
    CustomerID   INT AUTO_INCREMENT PRIMARY KEY,
    CustomerName VARCHAR(100) NOT NULL,
    PhoneNumber  VARCHAR(20)  NOT NULL,
    Address      VARCHAR(255) NOT NULL
);

CREATE TABLE Vehicles (
    VehicleID    INT AUTO_INCREMENT PRIMARY KEY,
    VehicleType  VARCHAR(50)  NOT NULL,
    LicensePlate VARCHAR(20)  NOT NULL UNIQUE,
    IsAvailable  TINYINT(1)   NOT NULL DEFAULT 1   -- 1=available, 0=in use
);

CREATE TABLE Orders (
    OrderID     INT AUTO_INCREMENT PRIMARY KEY,
    CustomerID  INT          NOT NULL,
    OrderDate   DATE         NOT NULL,
    Status      ENUM('Pending','In Transit','Delivered','Cancelled') NOT NULL DEFAULT 'Pending',
    Description VARCHAR(255),
    FOREIGN KEY (CustomerID) REFERENCES Customers(CustomerID) ON DELETE CASCADE
);

CREATE TABLE Deliveries (
    DeliveryID    INT AUTO_INCREMENT PRIMARY KEY,
    OrderID       INT  NOT NULL UNIQUE,
    VehicleID     INT  NOT NULL,
    DeliveryDate  DATE NOT NULL,
    DriverName    VARCHAR(100),
    Status        ENUM('Scheduled','In Transit','Completed','Failed') NOT NULL DEFAULT 'Scheduled',
    FOREIGN KEY (OrderID)   REFERENCES Orders(OrderID)   ON DELETE CASCADE,
    FOREIGN KEY (VehicleID) REFERENCES Vehicles(VehicleID)
);

CREATE TABLE Expenses (
    ExpenseID    INT AUTO_INCREMENT PRIMARY KEY,
    DeliveryID   INT            NOT NULL,
    ExpenseType  ENUM('Fuel','Toll','Handling','Maintenance','Other') NOT NULL,
    Amount       DECIMAL(10,2)  NOT NULL CHECK (Amount >= 0),
    Note         VARCHAR(255),
    FOREIGN KEY (DeliveryID) REFERENCES Deliveries(DeliveryID) ON DELETE CASCADE
);

-- ============================================================
-- 2. INDEXES
-- ============================================================

CREATE INDEX idx_orders_status      ON Orders(Status);
CREATE INDEX idx_orders_customer    ON Orders(CustomerID);
CREATE INDEX idx_orders_date        ON Orders(OrderDate);
CREATE INDEX idx_deliveries_vehicle ON Deliveries(VehicleID);
CREATE INDEX idx_deliveries_date    ON Deliveries(DeliveryDate);
CREATE INDEX idx_deliveries_status  ON Deliveries(Status);
CREATE INDEX idx_expenses_delivery  ON Expenses(DeliveryID);
CREATE INDEX idx_expenses_type      ON Expenses(ExpenseType);

-- ============================================================
-- 3. VIEWS
-- ============================================================

-- View: Current delivery schedule (not yet completed)
CREATE VIEW vw_current_delivery_schedule AS
SELECT
    d.DeliveryID,
    o.OrderID,
    c.CustomerName,
    c.PhoneNumber,
    c.Address          AS DeliveryAddress,
    v.VehicleType,
    v.LicensePlate,
    d.DriverName,
    d.DeliveryDate,
    d.Status           AS DeliveryStatus,
    o.Description      AS OrderDescription
FROM Deliveries d
JOIN Orders   o ON d.OrderID   = o.OrderID
JOIN Customers c ON o.CustomerID = c.CustomerID
JOIN Vehicles  v ON d.VehicleID  = v.VehicleID
WHERE d.Status IN ('Scheduled','In Transit');

-- View: Total cost per order
CREATE VIEW vw_cost_per_order AS
SELECT
    o.OrderID,
    c.CustomerName,
    o.OrderDate,
    o.Status          AS OrderStatus,
    d.DeliveryID,
    COALESCE(SUM(e.Amount), 0) AS TotalCost
FROM Orders o
JOIN Customers  c ON o.CustomerID  = c.CustomerID
LEFT JOIN Deliveries d ON o.OrderID    = d.OrderID
LEFT JOIN Expenses   e ON d.DeliveryID = e.DeliveryID
GROUP BY o.OrderID, c.CustomerName, o.OrderDate, o.Status, d.DeliveryID;

-- View: Outstanding (pending / in-transit) orders
CREATE VIEW vw_outstanding_orders AS
SELECT
    o.OrderID,
    c.CustomerName,
    c.PhoneNumber,
    o.OrderDate,
    o.Status,
    o.Description
FROM Orders o
JOIN Customers c ON o.CustomerID = c.CustomerID
WHERE o.Status IN ('Pending','In Transit');

-- View: Vehicle utilization
CREATE VIEW vw_vehicle_utilization AS
SELECT
    v.VehicleID,
    v.VehicleType,
    v.LicensePlate,
    v.IsAvailable,
    COUNT(d.DeliveryID)        AS TotalDeliveries,
    COALESCE(SUM(e.Amount), 0) AS TotalExpenses
FROM Vehicles v
LEFT JOIN Deliveries d ON v.VehicleID  = d.VehicleID
LEFT JOIN Expenses   e ON d.DeliveryID = e.DeliveryID
GROUP BY v.VehicleID, v.VehicleType, v.LicensePlate, v.IsAvailable;

-- ============================================================
-- 4. STORED PROCEDURES
-- ============================================================

DELIMITER $$

-- Procedure: Assign a vehicle to an order (creates a Delivery record)
CREATE PROCEDURE sp_assign_delivery(
    IN p_order_id    INT,
    IN p_vehicle_id  INT,
    IN p_driver_name VARCHAR(100),
    IN p_delivery_date DATE
)
BEGIN
    DECLARE v_order_status  VARCHAR(20);
    DECLARE v_is_available  TINYINT(1);

    SELECT Status INTO v_order_status FROM Orders  WHERE OrderID   = p_order_id;
    SELECT IsAvailable INTO v_is_available FROM Vehicles WHERE VehicleID = p_vehicle_id;

    IF v_order_status IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Order not found';
    ELSEIF v_order_status != 'Pending' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Order is not in Pending status';
    ELSEIF v_is_available = 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Vehicle is not available';
    ELSE
        INSERT INTO Deliveries (OrderID, VehicleID, DriverName, DeliveryDate, Status)
        VALUES (p_order_id, p_vehicle_id, p_driver_name, p_delivery_date, 'Scheduled');

        UPDATE Orders   SET Status      = 'In Transit' WHERE OrderID   = p_order_id;
        UPDATE Vehicles SET IsAvailable = 0            WHERE VehicleID = p_vehicle_id;

        SELECT 'Delivery assigned successfully' AS message, LAST_INSERT_ID() AS DeliveryID;
    END IF;
END$$

-- Procedure: Calculate total expenses for a delivery
CREATE PROCEDURE sp_calculate_delivery_expenses(IN p_delivery_id INT)
BEGIN
    SELECT
        d.DeliveryID,
        o.OrderID,
        c.CustomerName,
        SUM(e.Amount)                                           AS TotalExpenses,
        SUM(CASE WHEN e.ExpenseType='Fuel'       THEN e.Amount ELSE 0 END) AS FuelCost,
        SUM(CASE WHEN e.ExpenseType='Toll'       THEN e.Amount ELSE 0 END) AS TollCost,
        SUM(CASE WHEN e.ExpenseType='Handling'   THEN e.Amount ELSE 0 END) AS HandlingCost,
        SUM(CASE WHEN e.ExpenseType='Maintenance'THEN e.Amount ELSE 0 END) AS MaintenanceCost,
        SUM(CASE WHEN e.ExpenseType='Other'      THEN e.Amount ELSE 0 END) AS OtherCost
    FROM Deliveries d
    JOIN Orders    o ON d.OrderID   = o.OrderID
    JOIN Customers c ON o.CustomerID= c.CustomerID
    LEFT JOIN Expenses e ON d.DeliveryID = e.DeliveryID
    WHERE d.DeliveryID = p_delivery_id
    GROUP BY d.DeliveryID, o.OrderID, c.CustomerName;
END$$

-- Procedure: Monthly performance report
CREATE PROCEDURE sp_monthly_report(IN p_year INT, IN p_month INT)
BEGIN
    SELECT
        COUNT(DISTINCT o.OrderID)                                         AS TotalOrders,
        COUNT(DISTINCT CASE WHEN o.Status='Delivered' THEN o.OrderID END) AS DeliveredOrders,
        COUNT(DISTINCT CASE WHEN o.Status='Cancelled' THEN o.OrderID END) AS CancelledOrders,
        COUNT(DISTINCT d.DeliveryID)                                      AS TotalDeliveries,
        COALESCE(SUM(e.Amount), 0)                                        AS TotalExpenses,
        COALESCE(AVG(e.Amount), 0)                                        AS AvgExpensePerDelivery
    FROM Orders o
    LEFT JOIN Deliveries d ON o.OrderID    = d.OrderID
    LEFT JOIN Expenses   e ON d.DeliveryID = e.DeliveryID
    WHERE YEAR(o.OrderDate) = p_year AND MONTH(o.OrderDate) = p_month;
END$$

DELIMITER ;

-- ============================================================
-- 5. USER-DEFINED FUNCTIONS
-- ============================================================

DELIMITER $$

-- Function: Average delivery cost for a vehicle
CREATE FUNCTION fn_avg_delivery_cost(p_vehicle_id INT)
RETURNS DECIMAL(10,2)
DETERMINISTIC
READS SQL DATA
BEGIN
    DECLARE avg_cost DECIMAL(10,2);
    SELECT COALESCE(AVG(total_exp), 0) INTO avg_cost
    FROM (
        SELECT d.DeliveryID, SUM(e.Amount) AS total_exp
        FROM Deliveries d
        LEFT JOIN Expenses e ON d.DeliveryID = e.DeliveryID
        WHERE d.VehicleID = p_vehicle_id
        GROUP BY d.DeliveryID
    ) sub;
    RETURN avg_cost;
END$$

-- Function: Count deliveries per vehicle
CREATE FUNCTION fn_deliveries_per_vehicle(p_vehicle_id INT)
RETURNS INT
DETERMINISTIC
READS SQL DATA
BEGIN
    DECLARE cnt INT;
    SELECT COUNT(*) INTO cnt FROM Deliveries WHERE VehicleID = p_vehicle_id;
    RETURN cnt;
END$$

-- Function: Total expenses for an order
CREATE FUNCTION fn_order_total_expense(p_order_id INT)
RETURNS DECIMAL(10,2)
DETERMINISTIC
READS SQL DATA
BEGIN
    DECLARE total DECIMAL(10,2);
    SELECT COALESCE(SUM(e.Amount), 0) INTO total
    FROM Deliveries d
    JOIN Expenses e ON d.DeliveryID = e.DeliveryID
    WHERE d.OrderID = p_order_id;
    RETURN total;
END$$

DELIMITER ;

-- ============================================================
-- 6. TRIGGERS
-- ============================================================

DELIMITER $$

-- Trigger: When delivery status -> 'Completed', update Order to 'Delivered' and free vehicle
CREATE TRIGGER trg_delivery_completed
AFTER UPDATE ON Deliveries
FOR EACH ROW
BEGIN
    IF NEW.Status = 'Completed' AND OLD.Status != 'Completed' THEN
        UPDATE Orders   SET Status      = 'Delivered' WHERE OrderID   = NEW.OrderID;
        UPDATE Vehicles SET IsAvailable = 1           WHERE VehicleID = NEW.VehicleID;
    END IF;
    IF NEW.Status = 'Failed' AND OLD.Status != 'Failed' THEN
        UPDATE Orders   SET Status      = 'Pending'   WHERE OrderID   = NEW.OrderID;
        UPDATE Vehicles SET IsAvailable = 1           WHERE VehicleID = NEW.VehicleID;
    END IF;
END$$

-- Trigger: Prevent negative expense amounts
CREATE TRIGGER trg_validate_expense
BEFORE INSERT ON Expenses
FOR EACH ROW
BEGIN
    IF NEW.Amount < 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Expense amount cannot be negative';
    END IF;
END$$

DELIMITER ;

-- ============================================================
-- 7. DATABASE SECURITY – ROLES & USERS
-- ============================================================

-- Delivery Manager: full access
CREATE USER IF NOT EXISTS 'delivery_manager'@'localhost' IDENTIFIED BY 'Manager@123';
GRANT ALL PRIVILEGES ON delivery_system.* TO 'delivery_manager'@'localhost';

-- Dispatcher: can manage orders/deliveries/vehicles, NO expenses or user admin
CREATE USER IF NOT EXISTS 'dispatcher'@'localhost' IDENTIFIED BY 'Dispatch@123';
GRANT SELECT, INSERT, UPDATE ON delivery_system.Customers   TO 'dispatcher'@'localhost';
GRANT SELECT, INSERT, UPDATE ON delivery_system.Orders      TO 'dispatcher'@'localhost';
GRANT SELECT, INSERT, UPDATE ON delivery_system.Deliveries  TO 'dispatcher'@'localhost';
GRANT SELECT                  ON delivery_system.Vehicles    TO 'dispatcher'@'localhost';

-- Accountant: read-only on most tables, full access to Expenses
CREATE USER IF NOT EXISTS 'accountant'@'localhost' IDENTIFIED BY 'Account@123';
GRANT SELECT ON delivery_system.Orders      TO 'accountant'@'localhost';
GRANT SELECT ON delivery_system.Deliveries  TO 'accountant'@'localhost';
GRANT SELECT ON delivery_system.Customers   TO 'accountant'@'localhost';
GRANT SELECT, INSERT, UPDATE, DELETE ON delivery_system.Expenses TO 'accountant'@'localhost';

FLUSH PRIVILEGES;

-- ============================================================
-- 8. SAMPLE DATA  (5–10 rows per table as demo; bulk via Python)
-- ============================================================

INSERT INTO Customers (CustomerName, PhoneNumber, Address) VALUES
('Nguyen Van An',    '0901234561', '12 Le Loi, Hanoi'),
('Tran Thi Bich',   '0912345672', '34 Nguyen Hue, HCMC'),
('Le Van Cuong',    '0923456783', '56 Tran Phu, Da Nang'),
('Pham Thi Dung',   '0934567894', '78 Ly Thuong Kiet, Hue'),
('Hoang Van Em',    '0945678905', '90 Bach Dang, Hai Phong'),
('Do Thi Phuong',   '0956789016', '23 Phan Chu Trinh, Can Tho'),
('Vu Van Giang',    '0967890127', '45 Hung Vuong, Vung Tau'),
('Nguyen Thi Hoa',  '0978901238', '67 Le Duan, Nha Trang'),
('Bui Van Ich',     '0989012349', '89 Tran Hung Dao, Quy Nhon'),
('Dang Thi Kim',    '0990123450', '11 Nguyen Trai, Bien Hoa');

INSERT INTO Vehicles (VehicleType, LicensePlate, IsAvailable) VALUES
('Motorbike',  '29B1-11111', 1),
('Motorbike',  '29B2-22222', 1),
('Van',        '51C1-33333', 1),
('Van',        '51C2-44444', 1),
('Truck',      '43A1-55555', 1),
('Truck',      '43A2-66666', 1),
('Motorbike',  '92C1-77777', 1),
('Van',        '75A1-88888', 1),
('Truck',      '60B1-99999', 1),
('Motorbike',  '30A1-00001', 1);

INSERT INTO Orders (CustomerID, OrderDate, Status, Description) VALUES
(1,  '2024-01-05', 'Delivered',   'Electronics package'),
(2,  '2024-01-07', 'Delivered',   'Clothing items'),
(3,  '2024-01-10', 'Delivered',   'Food products'),
(4,  '2024-01-12', 'Delivered',   'Medical supplies'),
(5,  '2024-01-15', 'In Transit',  'Furniture parts'),
(6,  '2024-01-18', 'Pending',     'Books and stationery'),
(7,  '2024-01-20', 'Pending',     'Cosmetics'),
(8,  '2024-01-22', 'Cancelled',   'Cancelled order'),
(9,  '2024-01-25', 'Delivered',   'Auto parts'),
(10, '2024-01-28', 'Pending',     'Kitchen equipment');

INSERT INTO Deliveries (OrderID, VehicleID, DriverName, DeliveryDate, Status) VALUES
(1, 1, 'Tran Van Nam',   '2024-01-06', 'Completed'),
(2, 2, 'Le Van Hai',     '2024-01-08', 'Completed'),
(3, 3, 'Pham Van Ba',    '2024-01-11', 'Completed'),
(4, 4, 'Hoang Van Tu',   '2024-01-13', 'Completed'),
(5, 5, 'Do Van Nam',     '2024-01-16', 'In Transit'),
(9, 6, 'Vu Van Sau',     '2024-01-26', 'Completed');

INSERT INTO Expenses (DeliveryID, ExpenseType, Amount, Note) VALUES
(1, 'Fuel',        50000,  'Hanoi city route'),
(1, 'Toll',        20000,  'Highway toll'),
(2, 'Fuel',        75000,  'HCMC route'),
(2, 'Handling',    30000,  'Fragile items handling'),
(3, 'Fuel',        120000, 'Da Nang long route'),
(3, 'Toll',        45000,  'Bridge toll'),
(4, 'Fuel',        60000,  'Hue city'),
(4, 'Handling',    50000,  'Medical equipment handling'),
(5, 'Fuel',        200000, 'Truck fuel'),
(6, 'Fuel',        90000,  'Return route fuel');