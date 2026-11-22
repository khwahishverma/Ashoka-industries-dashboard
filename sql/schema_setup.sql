-- ============================================================
-- Ashoka Industries schema only.
-- This creates empty tables. Import authorized transaction data
-- separately; business records are not included in this repository.
-- ============================================================

DROP DATABASE IF EXISTS ashoka_industries;

CREATE DATABASE ashoka_industries;

USE ashoka_industries;

CREATE TABLE sales (
    sale_id INT AUTO_INCREMENT PRIMARY KEY,
    sale_date DATE NOT NULL,
    bill_no VARCHAR(50),
    customer_name VARCHAR(150),
    quantity DECIMAL(10,2),
    amount DECIMAL(15,2),
    transaction_type VARCHAR(30),
    period VARCHAR(30)
);

CREATE TABLE purchases (
    purchase_id INT AUTO_INCREMENT PRIMARY KEY,
    purchase_date DATE NOT NULL,
    bill_no VARCHAR(50),
    item_name VARCHAR(100),
    hsn_code VARCHAR(30),
    gst_amount DECIMAL(15,2),
    purchase_amount DECIMAL(15,2),
    period VARCHAR(30)
);

CREATE TABLE consumables (
    consumable_id INT AUTO_INCREMENT PRIMARY KEY,
    consumable_date DATE NOT NULL,
    bill_no VARCHAR(50),
    item_name VARCHAR(150),
    quantity DECIMAL(10,2),
    amount DECIMAL(15,2),
    period VARCHAR(30)
);

CREATE TABLE sales_adjustments (
    adjustment_id INT AUTO_INCREMENT PRIMARY KEY,
    adjustment_date DATE NOT NULL,
    reference VARCHAR(100),
    description VARCHAR(200),
    amount DECIMAL(15,2),
    adjustment_type VARCHAR(50)
);
