-- Create schema for inventory app
-- This script creates the schema and all necessary tables for the inventory ordering system

-- Create the schema
CREATE SCHEMA IF NOT EXISTS {schema_name};

-- Products table
CREATE TABLE IF NOT EXISTS {schema_name}.products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    category VARCHAR(50) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    stock_quantity INTEGER NOT NULL DEFAULT 0,
    reserved_quantity INTEGER NOT NULL DEFAULT 0,
    image_url VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Customers table
CREATE TABLE IF NOT EXISTS {schema_name}.customers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Orders table
CREATE TABLE IF NOT EXISTS {schema_name}.orders (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES {schema_name}.customers(id),
    order_number VARCHAR(50) UNIQUE NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    total_amount DECIMAL(10,2) NOT NULL,
    pickup_time TIMESTAMP,
    pickup_slot_id INTEGER,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Order items table
CREATE TABLE IF NOT EXISTS {schema_name}.order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES {schema_name}.orders(id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES {schema_name}.products(id),
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    subtotal DECIMAL(10,2) NOT NULL
);

-- Pickup slots table
CREATE TABLE IF NOT EXISTS {schema_name}.pickup_slots (
    id SERIAL PRIMARY KEY,
    slot_time TIMESTAMP NOT NULL,
    max_orders INTEGER DEFAULT 10,
    current_orders INTEGER DEFAULT 0,
    is_available BOOLEAN DEFAULT TRUE
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_products_category ON {schema_name}.products(category);
CREATE INDEX IF NOT EXISTS idx_products_active ON {schema_name}.products(is_active);
CREATE INDEX IF NOT EXISTS idx_orders_customer ON {schema_name}.orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON {schema_name}.orders(status);
CREATE INDEX IF NOT EXISTS idx_order_items_order ON {schema_name}.order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_order_items_product ON {schema_name}.order_items(product_id);
CREATE INDEX IF NOT EXISTS idx_pickup_slots_time ON {schema_name}.pickup_slots(slot_time);
