from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import psycopg
import os
import time
import csv
import io
from datetime import datetime
from databricks import sdk
from psycopg import sql
from psycopg_pool import ConnectionPool
from werkzeug.utils import secure_filename
from config import config

# Database connection setup
workspace_client = sdk.WorkspaceClient()
postgres_password = None
last_password_refresh = 0
connection_pool = None


# Print configuration summary on startup
config.print_config_summary()

# CSV upload configuration
ALLOWED_EXTENSIONS = {'csv'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB max file size

def allowed_file(filename):
    """Check if uploaded file is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def refresh_oauth_token():
    """Refresh OAuth token if expired."""
    global postgres_password, last_password_refresh
    if postgres_password is None or time.time() - last_password_refresh > 900:
        print("Refreshing PostgreSQL OAuth token")
        try:
            postgres_password = workspace_client.config.oauth_token().access_token
            last_password_refresh = time.time()
        except Exception as e:
            print(f"❌ Failed to refresh OAuth token: {str(e)}")
            return False
    return True

def get_connection_pool():
    """Get or create the connection pool."""
    global connection_pool
    if connection_pool is None:
        refresh_oauth_token()
        conn_string = (
            f"dbname={os.getenv('PGDATABASE')} "
            f"user={os.getenv('PGUSER')} "
            f"password={postgres_password} "
            f"host={os.getenv('PGHOST')} "
            f"port={os.getenv('PGPORT')} "
            f"sslmode={os.getenv('PGSSLMODE', 'require')} "
            f"application_name={os.getenv('PGAPPNAME')}"
        )
        connection_pool = ConnectionPool(conn_string, min_size=2, max_size=10)
    return connection_pool

def get_connection():
    """Get a connection from the pool."""
    global connection_pool
    
    # Recreate pool if token expired
    if postgres_password is None or time.time() - last_password_refresh > 900:
        if connection_pool:
            connection_pool.close()
            connection_pool = None
    
    return get_connection_pool().connection()

def get_schema_name():
    return os.getenv("POSTGRES_SCHEMA", "inventory_app")

def get_category_table_name():
    return os.getenv("POSTGRES_CATEGORY_TABLE", "inventory_category")

def get_warehouse_table_name():
    return os.getenv("POSTGRES_WAREHOUSE_TABLE", "inventory_warehouse")

def get_supplier_table_name():
    return os.getenv("POSTGRES_SUPPLIER_TABLE", "inventory_supplier")

def init_database():
    """Initialize database schema and tables."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                schema_name = get_schema_name()
                table_name = os.getenv("POSTGRES_TABLE", "inventory_items")
                category_table_name = get_category_table_name()
                warehouse_table_name = get_warehouse_table_name()
                supplier_table_name = get_supplier_table_name()
                
                print(f"🔧 Creating schema '{schema_name}' if it doesn't exist...")
                cur.execute(sql.SQL("CREATE SCHEMA IF NOT EXISTS {}").format(sql.Identifier(schema_name)))
                print(f"✅ Schema '{schema_name}' ready")
                
                # Create category table first
                print(f"🔧 Creating table '{schema_name}.{category_table_name}' if it doesn't exist...")
                create_category_table_sql = sql.SQL("""
                    CREATE TABLE IF NOT EXISTS {}.{} (
                        category_id serial4 NOT NULL,
                        category_name varchar(50) NOT NULL UNIQUE,
                        description text NULL,
                        date_created timestamp DEFAULT CURRENT_TIMESTAMP,
                        last_updated timestamp DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (category_id)
                    );
                """).format(
                    sql.Identifier(schema_name), 
                    sql.Identifier(category_table_name)
                )
                cur.execute(create_category_table_sql)
                print(f"✅ Table '{schema_name}.{category_table_name}' ready")
                
                # Create warehouse table
                print(f"🔧 Creating table '{schema_name}.{warehouse_table_name}' if it doesn't exist...")
                create_warehouse_table_sql = sql.SQL("""
                    CREATE TABLE IF NOT EXISTS {}.{} (
                        warehouse_id serial4 NOT NULL,
                        warehouse_name varchar(100) NOT NULL,
                        address varchar(255) NULL,
                        city varchar(100) NULL,
                        state varchar(100) NULL,
                        country varchar(100) NULL,
                        county varchar(100) NULL,
                        zipcode varchar(20) NULL,
                        latitude decimal(10, 8) NULL,
                        longitude decimal(11, 8) NULL,
                        contact_person varchar(100) NULL,
                        phone varchar(20) NULL,
                        email varchar(100) NULL,
                        date_created timestamp DEFAULT CURRENT_TIMESTAMP,
                        last_updated timestamp DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (warehouse_id)
                    );
                """).format(
                    sql.Identifier(schema_name), 
                    sql.Identifier(warehouse_table_name)
                )
                cur.execute(create_warehouse_table_sql)
                print(f"✅ Table '{schema_name}.{warehouse_table_name}' ready")
                
                # Create supplier table
                print(f"🔧 Creating table '{schema_name}.{supplier_table_name}' if it doesn't exist...")
                create_supplier_table_sql = sql.SQL("""
                    CREATE TABLE IF NOT EXISTS {}.{} (
                        supplier_id serial4 NOT NULL,
                        supplier_name varchar(100) NOT NULL,
                        contact_person varchar(100) NULL,
                        email varchar(100) NULL,
                        phone varchar(20) NULL,
                        address varchar(255) NULL,
                        city varchar(100) NULL,
                        state varchar(100) NULL,
                        country varchar(100) NULL,
                        county varchar(100) NULL,
                        zipcode varchar(20) NULL,
                        latitude decimal(10, 8) NULL,
                        longitude decimal(11, 8) NULL,
                        website varchar(255) NULL,
                        tax_id varchar(50) NULL,
                        payment_terms varchar(100) NULL,
                        date_created timestamp DEFAULT CURRENT_TIMESTAMP,
                        last_updated timestamp DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (supplier_id)
                    );
                """).format(
                    sql.Identifier(schema_name), 
                    sql.Identifier(supplier_table_name)
                )
                cur.execute(create_supplier_table_sql)
                print(f"✅ Table '{schema_name}.{supplier_table_name}' ready")
                
                # Check if old inventory_items table exists and migrate data
                print("🔧 Checking for existing inventory_items table...")
                cur.execute(sql.SQL("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = %s AND table_name = %s
                    );
                """), (schema_name, table_name))
                
                table_exists = cur.fetchone()[0]
                
                if table_exists:
                    # Check if table has old schema (with category column instead of category_id)
                    cur.execute(sql.SQL("""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_schema = %s AND table_name = %s AND column_name = 'category'
                    """), (schema_name, table_name))
                    
                    has_old_schema = cur.fetchone() is not None
                    
                    if has_old_schema:
                        print("🔧 Migrating existing data to new schema...")
                        migrate_existing_data(conn, cur, schema_name, table_name, category_table_name, warehouse_table_name, supplier_table_name)
                    else:
                        print("✅ Table already has new schema")
                    
                    # Check if supplier_id column exists, if not add it
                    cur.execute(sql.SQL("""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_schema = %s AND table_name = %s AND column_name = 'supplier_id'
                    """), (schema_name, table_name))
                    
                    has_supplier_id = cur.fetchone() is not None
                    
                    if not has_supplier_id:
                        print("🔧 Adding missing supplier_id column...")
                        cur.execute(sql.SQL("""
                            ALTER TABLE {}.{} 
                            ADD COLUMN supplier_id int4 NULL,
                            ADD CONSTRAINT fk_supplier 
                            FOREIGN KEY (supplier_id) REFERENCES {}.{}(supplier_id) ON DELETE SET NULL
                        """).format(
                            sql.Identifier(schema_name), 
                            sql.Identifier(table_name),
                            sql.Identifier(schema_name),
                            sql.Identifier(supplier_table_name)
                        ))
                        print("✅ Added supplier_id column")
                else:
                    # Create new inventory_items table with foreign keys
                    print(f"🔧 Creating new table '{schema_name}.{table_name}'...")
                    create_table_sql = sql.SQL("""
                        CREATE TABLE {}.{} (
                            id serial4 NOT NULL,
                            item_name varchar(100) NOT NULL,
                            description text NULL,
                            category_id int4 NOT NULL,
                            warehouse_id int4 NULL,
                            supplier_id int4 NULL,
                            quantity int4 NOT NULL,
                            unit_price float8 NOT NULL,
                            "location" varchar(100) NULL,
                            minimum_stock int4 NULL,
                            date_added timestamp DEFAULT CURRENT_TIMESTAMP,
                            last_updated timestamp DEFAULT CURRENT_TIMESTAMP,
                            PRIMARY KEY (id),
                            FOREIGN KEY (category_id) REFERENCES {}.{}(category_id) ON DELETE RESTRICT,
                            FOREIGN KEY (warehouse_id) REFERENCES {}.{}(warehouse_id) ON DELETE SET NULL,
                            FOREIGN KEY (supplier_id) REFERENCES {}.{}(supplier_id) ON DELETE SET NULL
                        );
                    """).format(
                        sql.Identifier(schema_name), 
                        sql.Identifier(table_name),
                        sql.Identifier(schema_name),
                        sql.Identifier(category_table_name),
                        sql.Identifier(schema_name),
                        sql.Identifier(warehouse_table_name),
                        sql.Identifier(schema_name),
                        sql.Identifier(supplier_table_name)
                    )
                    
                    cur.execute(create_table_sql)
                    print(f"✅ Table '{schema_name}.{table_name}' ready")
                
                # Insert default categories if they don't exist
                print("🔧 Inserting default categories...")
                default_categories = [
                    "Home", "Shoes", "Sports", "Children", "Men",
                    "Music", "Books", "Jewelry", "Women", "Electronics"
                ]
                
                for category in default_categories:
                    cur.execute(sql.SQL("""
                        INSERT INTO {}.{} (category_name) 
                        VALUES (%s) 
                        ON CONFLICT (category_name) DO NOTHING
                    """).format(sql.Identifier(schema_name), sql.Identifier(category_table_name)), (category,))
                
                print("✅ Default categories inserted")
                
                # Insert default warehouse if none exists
                print("🔧 Inserting default warehouse...")
                cur.execute(sql.SQL("""
                    INSERT INTO {}.{} (warehouse_name, city, state, country) 
                    SELECT 'Main Warehouse', 'Unknown', 'Unknown', 'Unknown'
                    WHERE NOT EXISTS (SELECT 1 FROM {}.{})
                """).format(
                    sql.Identifier(schema_name), 
                    sql.Identifier(warehouse_table_name),
                    sql.Identifier(schema_name),
                    sql.Identifier(warehouse_table_name)
                ))
                
                print("✅ Default warehouse inserted")
                
                # Insert default suppliers if they don't exist
                print("🔧 Inserting default suppliers...")
                default_suppliers = [
                    "Tech Supply Co.", "Office Solutions Inc.", "Industrial Equipment Ltd.", 
                    "Safety First Supplies", "Global Logistics Corp.", "Quality Materials Inc."
                ]
                
                for supplier in default_suppliers:
                    cur.execute(sql.SQL("""
                        INSERT INTO {}.{} (supplier_name) 
                        VALUES (%s) 
                        ON CONFLICT (supplier_name) DO NOTHING
                    """).format(sql.Identifier(schema_name), sql.Identifier(supplier_table_name)), (supplier,))
                
                print("✅ Default suppliers inserted")
                
                conn.commit()
                print("✅ Schema and tables creation committed")
                return True
                
    except Exception as e:
        print(f"❌ Database initialization error: {e}")
        return False

def migrate_existing_data(conn, cur, schema_name, table_name, category_table_name, warehouse_table_name, supplier_table_name):
    """Migrate existing inventory_items data to new schema."""
    try:
        # Get all unique categories from existing data
        cur.execute(sql.SQL("""
            SELECT DISTINCT category FROM {}.{} WHERE category IS NOT NULL
        """).format(sql.Identifier(schema_name), sql.Identifier(table_name)))
        
        existing_categories = [row[0] for row in cur.fetchall()]
        
        # Insert categories that don't exist
        for category in existing_categories:
            cur.execute(sql.SQL("""
                INSERT INTO {}.{} (category_name) 
                VALUES (%s) 
                ON CONFLICT (category_name) DO NOTHING
            """).format(sql.Identifier(schema_name), sql.Identifier(category_table_name)), (category,))
        
        # Get all unique suppliers from existing data
        cur.execute(sql.SQL("""
            SELECT DISTINCT supplier FROM {}.{} WHERE supplier IS NOT NULL
        """).format(sql.Identifier(schema_name), sql.Identifier(table_name)))
        
        existing_suppliers = [row[0] for row in cur.fetchall()]
        
        # Insert suppliers that don't exist
        for supplier in existing_suppliers:
            cur.execute(sql.SQL("""
                INSERT INTO {}.{} (supplier_name) 
                VALUES (%s) 
                ON CONFLICT (supplier_name) DO NOTHING
            """).format(sql.Identifier(schema_name), sql.Identifier(supplier_table_name)), (supplier,))
        
        # Get category mappings
        cur.execute(sql.SQL("""
            SELECT category_id, category_name FROM {}.{}
        """).format(sql.Identifier(schema_name), sql.Identifier(category_table_name)))
        
        category_mapping = {name: cat_id for cat_id, name in cur.fetchall()}
        
        # Get supplier mappings
        cur.execute(sql.SQL("""
            SELECT supplier_id, supplier_name FROM {}.{}
        """).format(sql.Identifier(schema_name), sql.Identifier(supplier_table_name)))
        
        supplier_mapping = {name: sup_id for sup_id, name in cur.fetchall()}
        
        # Get default warehouse ID
        cur.execute(sql.SQL("""
            SELECT warehouse_id FROM {}.{} WHERE warehouse_name = 'Main Warehouse' LIMIT 1
        """).format(sql.Identifier(schema_name), sql.Identifier(warehouse_table_name)))
        
        default_warehouse_id = cur.fetchone()
        default_warehouse_id = default_warehouse_id[0] if default_warehouse_id else None
        
        # Create new table with migrated data
        cur.execute(sql.SQL("""
            CREATE TABLE {}.{}_new (
                id serial4 NOT NULL,
                item_name varchar(100) NOT NULL,
                description text NULL,
                category_id int4 NOT NULL,
                warehouse_id int4 NULL,
                supplier_id int4 NULL,
                quantity int4 NOT NULL,
                unit_price float8 NOT NULL,
                "location" varchar(100) NULL,
                minimum_stock int4 NULL,
                date_added timestamp DEFAULT CURRENT_TIMESTAMP,
                last_updated timestamp DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (id),
                FOREIGN KEY (category_id) REFERENCES {}.{}(category_id) ON DELETE RESTRICT,
                FOREIGN KEY (warehouse_id) REFERENCES {}.{}(warehouse_id) ON DELETE SET NULL,
                FOREIGN KEY (supplier_id) REFERENCES {}.{}(supplier_id) ON DELETE SET NULL
            );
        """).format(
            sql.Identifier(schema_name), 
            sql.Identifier(table_name),
            sql.Identifier(schema_name),
            sql.Identifier(category_table_name),
            sql.Identifier(schema_name),
            sql.Identifier(warehouse_table_name),
            sql.Identifier(schema_name),
            sql.Identifier(supplier_table_name)
        ))
        
        # Migrate data with proper category and supplier mapping
        cur.execute(sql.SQL("""
            INSERT INTO {}.{}_new 
            (item_name, description, category_id, warehouse_id, supplier_id, quantity, unit_price, location, minimum_stock, date_added, last_updated)
            SELECT 
                i.item_name, 
                i.description, 
                COALESCE(c.category_id, 1), 
                %s, 
                COALESCE(s.supplier_id, NULL), 
                i.quantity, 
                i.unit_price, 
                i.location, 
                i.minimum_stock, 
                i.date_added, 
                i.last_updated
            FROM {}.{} i
            LEFT JOIN {}.{} c ON i.category = c.category_name
            LEFT JOIN {}.{} s ON i.supplier = s.supplier_name
        """).format(
            sql.Identifier(schema_name), 
            sql.Identifier(table_name),
            sql.Identifier(schema_name), 
            sql.Identifier(table_name),
            sql.Identifier(schema_name),
            sql.Identifier(category_table_name),
            sql.Identifier(schema_name),
            sql.Identifier(supplier_table_name)
        ), (default_warehouse_id,))
        
        # Drop old table and rename new one
        cur.execute(sql.SQL("DROP TABLE {}.{}").format(sql.Identifier(schema_name), sql.Identifier(table_name)))
        cur.execute(sql.SQL("ALTER TABLE {}.{}_new RENAME TO {}").format(
            sql.Identifier(schema_name), 
            sql.Identifier(table_name),
            sql.Identifier(table_name)
        ))
        
        print("✅ Data migration completed")
        
    except Exception as e:
        print(f"❌ Data migration error: {e}")
        raise

# Category management functions
def get_categories():
    """Get all categories."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                schema = get_schema_name()
                category_table = get_category_table_name()
                cur.execute(sql.SQL("""
                    SELECT category_id, category_name, description, date_created, last_updated 
                    FROM {}.{} ORDER BY category_name ASC
                """).format(sql.Identifier(schema), sql.Identifier(category_table)))
                return cur.fetchall()
    except Exception as e:
        print(f"Get categories error: {e}")
        return []

def get_category(category_id):
    """Get a specific category by ID."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                schema = get_schema_name()
                category_table = get_category_table_name()
                cur.execute(sql.SQL("""
                    SELECT category_id, category_name, description, date_created, last_updated 
                    FROM {}.{} WHERE category_id = %s
                """).format(sql.Identifier(schema), sql.Identifier(category_table)), (category_id,))
                return cur.fetchone()
    except Exception as e:
        print(f"Get category error: {e}")
        return None

def add_category(category_name, description=None):
    """Add a new category."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                schema = get_schema_name()
                category_table = get_category_table_name()
                cur.execute(sql.SQL("""
                    INSERT INTO {}.{} (category_name, description, date_created, last_updated) 
                    VALUES (%s, %s, %s, %s)
                """).format(sql.Identifier(schema), sql.Identifier(category_table)), 
                (category_name, description, datetime.now(), datetime.now()))
                conn.commit()
                return True
    except Exception as e:
        print(f"Add category error: {e}")
        return False

def update_category(category_id, category_name, description=None):
    """Update an existing category."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                schema = get_schema_name()
                category_table = get_category_table_name()
                cur.execute(sql.SQL("""
                    UPDATE {}.{} 
                    SET category_name = %s, description = %s, last_updated = %s
                    WHERE category_id = %s
                """).format(sql.Identifier(schema), sql.Identifier(category_table)), 
                (category_name, description, datetime.now(), category_id))
                conn.commit()
                return True
    except Exception as e:
        print(f"Update category error: {e}")
        return False

def delete_category(category_id):
    """Delete a category if no items are using it."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                schema = get_schema_name()
                category_table = get_category_table_name()
                table_name = os.getenv("POSTGRES_TABLE", "inventory_items")
                
                # First, check if any items are using this category
                cur.execute(sql.SQL("""
                    SELECT COUNT(*) 
                    FROM {}.{} 
                    WHERE category_id = %s
                """).format(sql.Identifier(schema), sql.Identifier(table_name)), (category_id,))
                
                item_count = cur.fetchone()[0]
                
                if item_count > 0:
                    print(f"Cannot delete category {category_id}: {item_count} items are using this category")
                    return False, f"Cannot delete category. {item_count} items are currently using this category. Please reassign or delete those items first."
                
                # If no items are using this category, proceed with deletion
                cur.execute(sql.SQL("DELETE FROM {}.{} WHERE category_id = %s").format(sql.Identifier(schema), sql.Identifier(category_table)), (category_id,))
                conn.commit()
                return True, "Category deleted successfully!"
                
    except Exception as e:
        print(f"Delete category error: {e}")
        return False, f"Error deleting category: {str(e)}"

# Warehouse management functions
def get_warehouses():
    """Get all warehouses."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                schema = get_schema_name()
                warehouse_table = get_warehouse_table_name()
                cur.execute(sql.SQL("""
                    SELECT warehouse_id, warehouse_name, address, city, state, country, county, zipcode, 
                           latitude, longitude, contact_person, phone, email, date_created, last_updated 
                    FROM {}.{} ORDER BY warehouse_name ASC
                """).format(sql.Identifier(schema), sql.Identifier(warehouse_table)))
                return cur.fetchall()
    except Exception as e:
        print(f"Get warehouses error: {e}")
        return []

def get_warehouse(warehouse_id):
    """Get a specific warehouse by ID."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                schema = get_schema_name()
                warehouse_table = get_warehouse_table_name()
                cur.execute(sql.SQL("""
                    SELECT warehouse_id, warehouse_name, address, city, state, country, county, zipcode, 
                           latitude, longitude, contact_person, phone, email, date_created, last_updated 
                    FROM {}.{} WHERE warehouse_id = %s
                """).format(sql.Identifier(schema), sql.Identifier(warehouse_table)), (warehouse_id,))
                return cur.fetchone()
    except Exception as e:
        print(f"Get warehouse error: {e}")
        return None

def add_warehouse(warehouse_name, address=None, city=None, state=None, country=None, county=None, 
                 zipcode=None, latitude=None, longitude=None, contact_person=None, phone=None, email=None):
    """Add a new warehouse."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                schema = get_schema_name()
                warehouse_table = get_warehouse_table_name()
                cur.execute(sql.SQL("""
                    INSERT INTO {}.{} (warehouse_name, address, city, state, country, county, zipcode, 
                                     latitude, longitude, contact_person, phone, email, date_created, last_updated) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """).format(sql.Identifier(schema), sql.Identifier(warehouse_table)), 
                (warehouse_name, address, city, state, country, county, zipcode, 
                 latitude, longitude, contact_person, phone, email, datetime.now(), datetime.now()))
                conn.commit()
                return True
    except Exception as e:
        print(f"Add warehouse error: {e}")
        return False

def update_warehouse(warehouse_id, warehouse_name, address=None, city=None, state=None, country=None, county=None, 
                    zipcode=None, latitude=None, longitude=None, contact_person=None, phone=None, email=None):
    """Update an existing warehouse."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                schema = get_schema_name()
                warehouse_table = get_warehouse_table_name()
                cur.execute(sql.SQL("""
                    UPDATE {}.{} 
                    SET warehouse_name = %s, address = %s, city = %s, state = %s, country = %s, county = %s, 
                        zipcode = %s, latitude = %s, longitude = %s, contact_person = %s, phone = %s, 
                        email = %s, last_updated = %s
                    WHERE warehouse_id = %s
                """).format(sql.Identifier(schema), sql.Identifier(warehouse_table)), 
                (warehouse_name, address, city, state, country, county, zipcode, 
                 latitude, longitude, contact_person, phone, email, datetime.now(), warehouse_id))
                conn.commit()
                return True
    except Exception as e:
        print(f"Update warehouse error: {e}")
        return False

def delete_warehouse(warehouse_id):
    """Delete a warehouse."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                schema = get_schema_name()
                warehouse_table = get_warehouse_table_name()
                cur.execute(sql.SQL("DELETE FROM {}.{} WHERE warehouse_id = %s").format(sql.Identifier(schema), sql.Identifier(warehouse_table)), (warehouse_id,))
                conn.commit()
                return True
    except Exception as e:
        print(f"Delete warehouse error: {e}")
        return False

# Supplier management functions
def get_suppliers():
    """Get all suppliers."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                schema = get_schema_name()
                supplier_table = get_supplier_table_name()
                cur.execute(sql.SQL("""
                    SELECT supplier_id, supplier_name, contact_person, email, phone, address, city, state, country, 
                           county, zipcode, latitude, longitude, website, tax_id, payment_terms, date_created, last_updated 
                    FROM {}.{} ORDER BY supplier_name ASC
                """).format(sql.Identifier(schema), sql.Identifier(supplier_table)))
                return cur.fetchall()
    except Exception as e:
        print(f"Get suppliers error: {e}")
        return []

def get_supplier(supplier_id):
    """Get a specific supplier by ID."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                schema = get_schema_name()
                supplier_table = get_supplier_table_name()
                cur.execute(sql.SQL("""
                    SELECT supplier_id, supplier_name, contact_person, email, phone, address, city, state, country, 
                           county, zipcode, latitude, longitude, website, tax_id, payment_terms, date_created, last_updated 
                    FROM {}.{} WHERE supplier_id = %s
                """).format(sql.Identifier(schema), sql.Identifier(supplier_table)), (supplier_id,))
                return cur.fetchone()
    except Exception as e:
        print(f"Get supplier error: {e}")
        return None

def add_supplier(supplier_name, contact_person=None, email=None, phone=None, address=None, city=None, state=None, 
                country=None, county=None, zipcode=None, latitude=None, longitude=None, website=None, 
                tax_id=None, payment_terms=None):
    """Add a new supplier."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                schema = get_schema_name()
                supplier_table = get_supplier_table_name()
                cur.execute(sql.SQL("""
                    INSERT INTO {}.{} (supplier_name, contact_person, email, phone, address, city, state, country, 
                                     county, zipcode, latitude, longitude, website, tax_id, payment_terms, date_created, last_updated) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """).format(sql.Identifier(schema), sql.Identifier(supplier_table)), 
                (supplier_name, contact_person, email, phone, address, city, state, country, county, zipcode, 
                 latitude, longitude, website, tax_id, payment_terms, datetime.now(), datetime.now()))
                conn.commit()
                return True
    except Exception as e:
        print(f"Add supplier error: {e}")
        return False

def update_supplier(supplier_id, supplier_name, contact_person=None, email=None, phone=None, address=None, city=None, 
                   state=None, country=None, county=None, zipcode=None, latitude=None, longitude=None, website=None, 
                   tax_id=None, payment_terms=None):
    """Update an existing supplier."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                schema = get_schema_name()
                supplier_table = get_supplier_table_name()
                cur.execute(sql.SQL("""
                    UPDATE {}.{} 
                    SET supplier_name = %s, contact_person = %s, email = %s, phone = %s, address = %s, city = %s, 
                        state = %s, country = %s, county = %s, zipcode = %s, latitude = %s, longitude = %s, 
                        website = %s, tax_id = %s, payment_terms = %s, last_updated = %s
                    WHERE supplier_id = %s
                """).format(sql.Identifier(schema), sql.Identifier(supplier_table)), 
                (supplier_name, contact_person, email, phone, address, city, state, country, county, zipcode, 
                 latitude, longitude, website, tax_id, payment_terms, datetime.now(), supplier_id))
                conn.commit()
                return True
    except Exception as e:
        print(f"Update supplier error: {e}")
        return False

def delete_supplier(supplier_id):
    """Delete a supplier."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                schema = get_schema_name()
                supplier_table = get_supplier_table_name()
                cur.execute(sql.SQL("DELETE FROM {}.{} WHERE supplier_id = %s").format(sql.Identifier(schema), sql.Identifier(supplier_table)), (supplier_id,))
                conn.commit()
                return True
    except Exception as e:
        print(f"Delete supplier error: {e}")
        return False

def add_inventory_item(item_name, description, category_id, quantity, unit_price, supplier_id=None, location=None, minimum_stock=None, warehouse_id=None):
    """Add a new inventory item."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                schema = get_schema_name()
                table_name = os.getenv("POSTGRES_TABLE", "inventory_items")
                cur.execute(sql.SQL("""
                    INSERT INTO {}.{} 
                    (item_name, description, category_id, warehouse_id, supplier_id, quantity, unit_price, location, minimum_stock, date_added, last_updated) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """).format(sql.Identifier(schema), sql.Identifier(table_name)), 
                (item_name, description, category_id, warehouse_id, supplier_id, quantity, unit_price, location, minimum_stock, datetime.now(), datetime.now()))
                conn.commit()
                return True
    except Exception as e:
        print(f"Add inventory item error: {e}")
        return False

def add_inventory_items_bulk(items_data):
    """Add multiple inventory items in bulk."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                schema = get_schema_name()
                table_name = os.getenv("POSTGRES_TABLE", "inventory_items")
                
                # Prepare the bulk insert
                insert_query = sql.SQL("""
                    INSERT INTO {}.{} 
                    (item_name, description, category_id, warehouse_id, supplier_id, quantity, unit_price, location, minimum_stock, date_added, last_updated) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """).format(sql.Identifier(schema), sql.Identifier(table_name))
                
                # Execute bulk insert
                cur.executemany(insert_query, items_data)
                conn.commit()
                return True, cur.rowcount
    except Exception as e:
        print(f"Bulk add inventory items error: {e}")
        return False, 0

def validate_csv_row(row, row_num):
    """Validate a single CSV row and return processed data or error."""
    errors = []
    
    # Required fields
    item_name = row.get('item_name', '').strip()
    category_name = row.get('category', '').strip()
    
    # Validate required fields
    if not item_name:
        errors.append(f"Row {row_num}: item_name is required")
    elif len(item_name) > 100:
        errors.append(f"Row {row_num}: item_name must be 100 characters or less")
        
    if not category_name:
        errors.append(f"Row {row_num}: category is required")
    elif len(category_name) > 50:
        errors.append(f"Row {row_num}: category must be 50 characters or less")
    
    # Get category_id from category name
    category_id = None
    if category_name:
        categories = get_categories()
        for cat in categories:
            if cat[1].lower() == category_name.lower():  # cat[1] is category_name
                category_id = cat[0]  # cat[0] is category_id
                break
        if not category_id:
            errors.append(f"Row {row_num}: category '{category_name}' not found. Please add it first.")
    
    # Validate warehouse_id (now required)
    warehouse_id = None
    try:
        warehouse_id = int(row.get('warehouse_id', 0))
        if warehouse_id <= 0:
            errors.append(f"Row {row_num}: warehouse_id is required and must be a positive integer")
        else:
            # Verify warehouse exists
            warehouses = get_warehouses()
            warehouse_exists = any(wh[0] == warehouse_id for wh in warehouses)
            if not warehouse_exists:
                errors.append(f"Row {row_num}: warehouse_id {warehouse_id} not found. Please check warehouse ID.")
    except (ValueError, TypeError):
        errors.append(f"Row {row_num}: warehouse_id must be a valid integer")
    
    # Validate quantity
    try:
        quantity = int(row.get('quantity', 0))
        if quantity < 0:
            errors.append(f"Row {row_num}: quantity must be 0 or greater")
    except (ValueError, TypeError):
        errors.append(f"Row {row_num}: quantity must be a valid number")
        quantity = 0
    
    # Validate unit_price
    try:
        unit_price = float(row.get('unit_price', 0.0))
        if unit_price < 0:
            errors.append(f"Row {row_num}: unit_price must be 0 or greater")
    except (ValueError, TypeError):
        errors.append(f"Row {row_num}: unit_price must be a valid number")
        unit_price = 0.0
    
    # Optional fields with length validation
    description = row.get('description', '').strip()
    supplier = row.get('supplier', '').strip() or None
    
    if supplier and len(supplier) > 100:
        errors.append(f"Row {row_num}: supplier must be 100 characters or less")
    
    # Validate minimum_stock
    minimum_stock = None
    if row.get('minimum_stock', '').strip():
        try:
            minimum_stock = int(row.get('minimum_stock'))
            if minimum_stock < 0:
                errors.append(f"Row {row_num}: minimum_stock must be 0 or greater")
        except (ValueError, TypeError):
            errors.append(f"Row {row_num}: minimum_stock must be a valid number or empty")
    
    # Get supplier_id from supplier name if provided
    supplier_id = None
    supplier_name = row.get('supplier', '').strip()
    if supplier_name:
        suppliers = get_suppliers()
        for sup in suppliers:
            if sup[1].lower() == supplier_name.lower():  # sup[1] is supplier_name
                supplier_id = sup[0]  # sup[0] is supplier_id
                break
        if not supplier_id:
            errors.append(f"Row {row_num}: supplier '{supplier_name}' not found. Please add it first.")
    
    if errors:
        return None, errors
    
    return (item_name, description, category_id, warehouse_id, supplier_id, quantity, unit_price, None, minimum_stock, datetime.now(), datetime.now()), []

def process_csv_file(file_content):
    """Process uploaded CSV file and return results."""
    try:
        # Parse CSV content
        csv_reader = csv.DictReader(io.StringIO(file_content))
        
        # Expected columns
        required_columns = {'item_name', 'category', 'warehouse_id', 'quantity', 'unit_price'}
        optional_columns = {'description', 'supplier', 'minimum_stock'}
        all_columns = required_columns.union(optional_columns)
        
        # Check if required columns exist
        csv_columns = set(csv_reader.fieldnames or [])
        missing_required = required_columns - csv_columns
        
        if missing_required:
            return {
                'success': False,
                'error': f"Missing required columns: {', '.join(missing_required)}",
                'valid_items': 0,
                'total_rows': 0,
                'errors': []
            }
        
        # Unknown columns warning
        unknown_columns = csv_columns - all_columns
        warnings = []
        if unknown_columns:
            warnings.append(f"Unknown columns will be ignored: {', '.join(unknown_columns)}")
        
        # Process rows
        valid_items = []
        all_errors = []
        row_num = 1  # Start from 1 (header is row 0)
        
        for row in csv_reader:
            row_num += 1
            
            # Skip empty rows
            if not any(value.strip() for value in row.values() if value):
                continue
                
            item_data, row_errors = validate_csv_row(row, row_num)
            
            if item_data:
                valid_items.append(item_data)
            else:
                all_errors.extend(row_errors)
        
        return {
            'success': len(valid_items) > 0,
            'valid_items': len(valid_items),
            'total_rows': row_num - 1,  # Exclude header row
            'errors': all_errors,
            'warnings': warnings,
            'data': valid_items if len(valid_items) > 0 else []
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': f"Error processing CSV file: {str(e)}",
            'valid_items': 0,
            'total_rows': 0,
            'errors': []
        }

def get_inventory_items():
    """Get all inventory items with category, warehouse, and supplier information."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                schema = get_schema_name()
                table_name = os.getenv("POSTGRES_TABLE", "inventory_items")
                category_table = get_category_table_name()
                warehouse_table = get_warehouse_table_name()
                supplier_table = get_supplier_table_name()
                cur.execute(sql.SQL("""
                    SELECT i.id, i.item_name, i.description, c.category_name, w.warehouse_name, s.supplier_name,
                           i.quantity, i.unit_price, i.location, i.minimum_stock, 
                           i.date_added, i.last_updated, i.category_id, i.warehouse_id, i.supplier_id
                    FROM {}.{} i
                    LEFT JOIN {}.{} c ON i.category_id = c.category_id
                    LEFT JOIN {}.{} w ON i.warehouse_id = w.warehouse_id
                    LEFT JOIN {}.{} s ON i.supplier_id = s.supplier_id
                    ORDER BY i.item_name ASC
                """).format(
                    sql.Identifier(schema), sql.Identifier(table_name),
                    sql.Identifier(schema), sql.Identifier(category_table),
                    sql.Identifier(schema), sql.Identifier(warehouse_table),
                    sql.Identifier(schema), sql.Identifier(supplier_table)
                ))
                return cur.fetchall()
    except Exception as e:
        print(f"Get inventory items error: {e}")
        return []

def get_inventory_item(item_id):
    """Get a specific inventory item by ID with category, warehouse, and supplier information."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                schema = get_schema_name()
                table_name = os.getenv("POSTGRES_TABLE", "inventory_items")
                category_table = get_category_table_name()
                warehouse_table = get_warehouse_table_name()
                supplier_table = get_supplier_table_name()
                cur.execute(sql.SQL("""
                    SELECT i.id, i.item_name, i.description, c.category_name, w.warehouse_name, s.supplier_name,
                           i.quantity, i.unit_price, i.location, i.minimum_stock, 
                           i.date_added, i.last_updated, i.category_id, i.warehouse_id, i.supplier_id
                    FROM {}.{} i
                    LEFT JOIN {}.{} c ON i.category_id = c.category_id
                    LEFT JOIN {}.{} w ON i.warehouse_id = w.warehouse_id
                    LEFT JOIN {}.{} s ON i.supplier_id = s.supplier_id
                    WHERE i.id = %s
                """).format(
                    sql.Identifier(schema), sql.Identifier(table_name),
                    sql.Identifier(schema), sql.Identifier(category_table),
                    sql.Identifier(schema), sql.Identifier(warehouse_table),
                    sql.Identifier(schema), sql.Identifier(supplier_table)
                ), (item_id,))
                return cur.fetchone()
    except Exception as e:
        print(f"Get inventory item error: {e}")
        return None

def update_inventory_item(item_id, item_name, description, category_id, quantity, unit_price, supplier_id=None, location=None, minimum_stock=None, warehouse_id=None):
    """Update an existing inventory item."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                schema = get_schema_name()
                table_name = os.getenv("POSTGRES_TABLE", "inventory_items")
                cur.execute(sql.SQL("""
                    UPDATE {}.{} 
                    SET item_name = %s, description = %s, category_id = %s, warehouse_id = %s, supplier_id = %s, 
                        quantity = %s, unit_price = %s, location = %s, minimum_stock = %s, last_updated = %s
                    WHERE id = %s
                """).format(sql.Identifier(schema), sql.Identifier(table_name)), 
                (item_name, description, category_id, warehouse_id, supplier_id, quantity, unit_price, location, minimum_stock, datetime.now(), item_id))
                conn.commit()
                return True
    except Exception as e:
        print(f"Update inventory item error: {e}")
        return False

def delete_inventory_item(item_id):
    """Delete an inventory item."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                schema = get_schema_name()
                table_name = os.getenv("POSTGRES_TABLE", "inventory_items")
                cur.execute(sql.SQL("DELETE FROM {}.{} WHERE id = %s").format(sql.Identifier(schema), sql.Identifier(table_name)), (item_id,))
                conn.commit()
                return True
    except Exception as e:
        print(f"Delete inventory item error: {e}")
        return False

def get_low_stock_items():
    """Get items with quantity at or below minimum stock level."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                schema = get_schema_name()
                table_name = os.getenv("POSTGRES_TABLE", "inventory_items")
                category_table = get_category_table_name()
                warehouse_table = get_warehouse_table_name()
                supplier_table = get_supplier_table_name()
                cur.execute(sql.SQL("""
                    SELECT i.id, i.item_name, i.description, c.category_name, w.warehouse_name, s.supplier_name,
                           i.quantity, i.unit_price, i.location, i.minimum_stock, 
                           i.date_added, i.last_updated, i.category_id, i.warehouse_id, i.supplier_id
                    FROM {}.{} i
                    LEFT JOIN {}.{} c ON i.category_id = c.category_id
                    LEFT JOIN {}.{} w ON i.warehouse_id = w.warehouse_id
                    LEFT JOIN {}.{} s ON i.supplier_id = s.supplier_id
                    WHERE i.minimum_stock IS NOT NULL AND i.quantity <= i.minimum_stock
                    ORDER BY (i.quantity - i.minimum_stock) ASC
                """).format(
                    sql.Identifier(schema), sql.Identifier(table_name),
                    sql.Identifier(schema), sql.Identifier(category_table),
                    sql.Identifier(schema), sql.Identifier(warehouse_table),
                    sql.Identifier(schema), sql.Identifier(supplier_table)
                ))
                return cur.fetchall()
    except Exception as e:
        print(f"Get low stock items error: {e}")
        return []

def get_demand_forecast_suggestion(warehouse_id, category_id, current_quantity, minimum_stock, new_quantity=0):
    """Get suggested quantity based on demand forecast with smart inventory analysis."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                schema = get_schema_name()
                
                # Get detailed forecast data for the next 30 days (daily granularity)
                cur.execute(sql.SQL("""
                    SELECT forecast_date, forecasted_items
                    FROM {}.inventory_demand_forecast 
                    WHERE warehouse_id = %s AND category_id = %s 
                    AND forecast_date >= CURRENT_DATE 
                    AND forecast_date <= CURRENT_DATE + INTERVAL '30 days'
                    ORDER BY forecast_date
                """).format(sql.Identifier(schema)), (warehouse_id, category_id))
                
                forecast_data = cur.fetchall()
                
                if forecast_data:
                    # Calculate total forecast and analyze daily requirements
                    total_forecast = sum(float(row[1]) for row in forecast_data)
                    daily_forecasts = [(row[0], float(row[1])) for row in forecast_data]
                    
                    # Calculate total available inventory (current + new quantity being added)
                    total_available = current_quantity + new_quantity
                    
                    # Calculate safety stock (minimum_stock or 10% of total forecast, whichever is higher)
                    safety_stock = max(
                        minimum_stock if minimum_stock else 0,
                        max(1, int(total_forecast * 0.1))
                    )
                    
                    # Calculate recommended total inventory (forecast + safety stock)
                    recommended_total = int(total_forecast) + safety_stock
                    
                    # Check if current inventory + new quantity meets demand
                    if total_available >= recommended_total:
                        # Current inventory is sufficient, suggest minimal increase or no change
                        if total_available >= recommended_total + safety_stock:
                            # Very well stocked, suggest no increase
                            suggested_quantity = new_quantity
                            reasoning = f"Current inventory ({current_quantity}) + new quantity ({new_quantity}) = {total_available} is sufficient for 30-day forecast ({int(total_forecast)}) + safety stock ({safety_stock}). No additional increase needed."
                        else:
                            # Adequate but could use small buffer
                            suggested_quantity = new_quantity + max(1, int(safety_stock * 0.2))
                            reasoning = f"Current inventory ({current_quantity}) + new quantity ({new_quantity}) = {total_available} meets forecast ({int(total_forecast)}) but adding small buffer for safety."
                    else:
                        # Insufficient inventory, calculate needed increase
                        needed_increase = recommended_total - total_available
                        suggested_quantity = new_quantity + needed_increase
                        reasoning = f"Current inventory ({current_quantity}) + new quantity ({new_quantity}) = {total_available} insufficient for 30-day forecast ({int(total_forecast)}) + safety stock ({safety_stock}). Suggest adding {needed_increase} more items."
                    
                    return {
                        'suggested_quantity': suggested_quantity,
                        'forecast_30_days': int(total_forecast),
                        'safety_stock': safety_stock,
                        'current_total_available': total_available,
                        'recommended_total': recommended_total,
                        'reasoning': reasoning
                    }
                else:
                    # No forecast data available, use minimum stock logic
                    if minimum_stock and current_quantity + new_quantity < minimum_stock:
                        needed_increase = minimum_stock - (current_quantity + new_quantity)
                        suggested_quantity = new_quantity + needed_increase
                        reasoning = f"No forecast data available. Current inventory ({current_quantity}) + new quantity ({new_quantity}) = {current_quantity + new_quantity} below minimum stock ({minimum_stock}). Suggest adding {needed_increase} more items."
                    else:
                        suggested_quantity = new_quantity
                        reasoning = f"No forecast data available. Current inventory ({current_quantity}) + new quantity ({new_quantity}) = {current_quantity + new_quantity} meets minimum stock requirement ({minimum_stock if minimum_stock else 'not set'})."
                    
                    return {
                        'suggested_quantity': suggested_quantity,
                        'forecast_30_days': 0,
                        'safety_stock': minimum_stock if minimum_stock else 1,
                        'current_total_available': current_quantity + new_quantity,
                        'recommended_total': minimum_stock if minimum_stock else current_quantity + new_quantity,
                        'reasoning': reasoning
                    }
    except Exception as e:
        print(f"Get demand forecast error: {e}")
        return {
            'suggested_quantity': new_quantity + 1,
            'forecast_30_days': 0,
            'safety_stock': minimum_stock if minimum_stock else 1,
            'current_total_available': current_quantity + new_quantity,
            'recommended_total': current_quantity + new_quantity + 1,
            'reasoning': "Error retrieving forecast data. Suggesting small increase."
        }

def get_dashboard_embed_url():
    """Generate dashboard embed URL with proper authentication."""
    try:
        # Get URL from configuration
        embed_url = config.get_dashboard_embed_url()
        
        if not embed_url:
            return None
        
        # Add authentication parameters if available
        if refresh_oauth_token() and postgres_password:
            embed_url += f"?access_token={postgres_password}"
        
        return embed_url
    except Exception as e:
        print(f"Dashboard URL generation error: {e}")
        return None

def get_dashboard_public_url():
    """Get the public dashboard URL for opening in new tab."""
    try:
        return config.get_dashboard_public_url()
    except Exception as e:
        print(f"Dashboard public URL error: {e}")
        return None

def is_token_expired():
    """Check if OAuth token is expired or will expire soon."""
    if not postgres_password or not last_password_refresh:
        return True
    
    # Consider token expired if it's been 13+ minutes (15 min expiry with 2 min buffer)
    return time.time() - last_password_refresh > 780

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key')
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Initialize database
if not init_database():
    print("Failed to initialize database")

@app.route('/')
def index():
    """Main page showing all inventory items."""
    items = get_inventory_items()
    low_stock_items = get_low_stock_items()
    warehouses = get_warehouses()
    return render_template('index.html', items=items, low_stock_count=len(low_stock_items), warehouses=warehouses)

@app.route('/add', methods=['GET', 'POST'])
def add_item_route():
    """Add a new inventory item."""
    if request.method == 'POST':
        item_name = request.form.get('item_name', '').strip()
        description = request.form.get('description', '').strip()
        category_id = request.form.get('category_id', type=int)
        warehouse_id = request.form.get('warehouse_id', type=int) or None
        supplier_id = request.form.get('supplier_id', type=int) or None
        quantity = request.form.get('quantity', type=int)
        unit_price = request.form.get('unit_price', type=float)
        minimum_stock = request.form.get('minimum_stock', type=int) or None
        
        if item_name and category_id and quantity is not None and unit_price is not None:
            if add_inventory_item(item_name, description, category_id, quantity, unit_price, supplier_id, None, minimum_stock, warehouse_id):
                flash('Item added successfully!', 'success')
            else:
                flash('Failed to add item.', 'error')
        else:
            flash('Please fill in all required fields.', 'error')
        return redirect(url_for('index'))
    
    categories = get_categories()
    warehouses = get_warehouses()
    suppliers = get_suppliers()
    low_stock_items = get_low_stock_items()
    return render_template('add_item.html', categories=categories, warehouses=warehouses, suppliers=suppliers, low_stock_count=len(low_stock_items))

@app.route('/upload-csv', methods=['GET', 'POST'])
def upload_csv_route():
    """Upload CSV file to add multiple inventory items."""
    if request.method == 'POST':
        # Check if file was uploaded
        if 'csv_file' not in request.files:
            flash('No file selected.', 'error')
            return redirect(request.url)
        
        file = request.files['csv_file']
        
        # Check if file is selected
        if file.filename == '':
            flash('No file selected.', 'error')
            return redirect(request.url)
        
        # Check file type
        if not allowed_file(file.filename):
            flash('Please upload a CSV file.', 'error')
            return redirect(request.url)
        
        try:
            # Read file content
            file_content = file.read().decode('utf-8')
            
            # Process CSV
            result = process_csv_file(file_content)
            
            if result['success'] and result['data']:
                # Insert valid items
                success, inserted_count = add_inventory_items_bulk(result['data'])
                
                if success:
                    flash(f'Successfully added {inserted_count} items from CSV!', 'success')
                    
                    # Show warnings if any
                    if result['warnings']:
                        for warning in result['warnings']:
                            flash(warning, 'warning')
                    
                    # Show errors for invalid rows if any
                    if result['errors']:
                        flash(f'Note: {len(result["errors"])} rows had errors and were skipped.', 'warning')
                        
                else:
                    flash('Failed to save items to database.', 'error')
            else:
                # Show error or validation issues
                if result.get('error'):
                    flash(result['error'], 'error')
                
                if result['errors']:
                    flash(f'Found {len(result["errors"])} validation errors:', 'error')
                    for error in result['errors'][:10]:  # Show first 10 errors
                        flash(error, 'error')
                    if len(result['errors']) > 10:
                        flash(f'... and {len(result["errors"]) - 10} more errors.', 'error')
        
        except Exception as e:
            flash(f'Error processing file: {str(e)}', 'error')
        
        return redirect(url_for('upload_csv_route'))
    
    low_stock_items = get_low_stock_items()
    return render_template('upload_csv.html', low_stock_count=len(low_stock_items))

@app.route('/download-template')
def download_template():
    """Download CSV template file."""
    from flask import Response
    
    # Create CSV template content
    template_content = """item_name,description,category,warehouse_id,quantity,unit_price,supplier,minimum_stock
"Laptop - Example Model","High-performance laptop for office use","Electronics",1,5,1299.99,"Tech Supplier Co.",2
"Office Desk","Adjustable height standing desk","Furniture",2,10,399.50,"Office Furniture Ltd.",3
"Safety Helmet","OSHA approved construction helmet","Safety Equipment",1,25,29.99,"Safety First Inc.",10"""
    
    return Response(
        template_content,
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=inventory_template.csv'}
    )

@app.route('/edit/<int:item_id>', methods=['GET', 'POST'])
def edit_item_route(item_id):
    """Edit an existing inventory item."""
    item = get_inventory_item(item_id)
    if not item:
        flash('Item not found.', 'error')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        item_name = request.form.get('item_name', '').strip()
        description = request.form.get('description', '').strip()
        category_id = request.form.get('category_id', type=int)
        warehouse_id = request.form.get('warehouse_id', type=int) or None
        supplier_id = request.form.get('supplier_id', type=int) or None
        quantity = request.form.get('quantity', type=int)
        unit_price = request.form.get('unit_price', type=float)
        minimum_stock = request.form.get('minimum_stock', type=int) or None
        
        if item_name and category_id and quantity is not None and unit_price is not None:
            if update_inventory_item(item_id, item_name, description, category_id, quantity, unit_price, supplier_id, None, minimum_stock, warehouse_id):
                flash('Item updated successfully!', 'success')
            else:
                flash('Failed to update item.', 'error')
        else:
            flash('Please fill in all required fields.', 'error')
        return redirect(url_for('index'))
    
    categories = get_categories()
    warehouses = get_warehouses()
    suppliers = get_suppliers()
    low_stock_items = get_low_stock_items()
    return render_template('edit_item.html', item=item, categories=categories, warehouses=warehouses, suppliers=suppliers, low_stock_count=len(low_stock_items))

@app.route('/delete/<int:item_id>')
def delete_item_route(item_id):
    """Delete an inventory item."""
    if delete_inventory_item(item_id):
        flash('Item deleted successfully!', 'success')
    else:
        flash('Failed to delete item.', 'error')
    return redirect(url_for('index'))

@app.route('/low-stock')
def low_stock_route():
    """Show items with low stock."""
    low_stock_items = get_low_stock_items()
    return render_template('low_stock.html', items=low_stock_items, low_stock_count=len(low_stock_items))

@app.route('/dashboard')
def dashboard_route():
    """Display embedded Databricks AI/BI dashboard."""
    dashboard_embed_url = get_dashboard_embed_url()
    dashboard_url = get_dashboard_public_url()
    low_stock_items = get_low_stock_items()
    
    # Debug information
    print(f"Dashboard Debug Info:")
    print(f"  DASHBOARD_ID: {os.getenv('DASHBOARD_ID')}")
    print(f"  DATABRICKS_HOST: {os.getenv('DATABRICKS_HOST')}")
    print(f"  Workspace URL: {workspace_client.config.host}")
    print(f"  Embed URL: {dashboard_embed_url}")
    print(f"  Public URL: {dashboard_url}")
    
    if not dashboard_embed_url:
        flash('Dashboard not configured. Please set DASHBOARD_ID environment variable.', 'warning')
        return redirect(url_for('index'))
    
    return render_template('dashboard.html', 
                         dashboard_embed_url=dashboard_embed_url,
                         dashboard_url=dashboard_url,
                         low_stock_count=len(low_stock_items))

@app.route('/api/items')
def api_items():
    """API endpoint to get all items as JSON."""
    items = get_inventory_items()
    items_list = []
    for item in items:
        items_list.append({
            'id': item[0],
            'item_name': item[1],
            'description': item[2],
            'category_name': item[3],
            'warehouse_name': item[4],
            'supplier_name': item[5],
            'quantity': item[6],
            'unit_price': item[7],
            'location': item[8],
            'minimum_stock': item[9],
            'date_added': item[10].isoformat() if item[10] else None,
            'last_updated': item[11].isoformat() if item[11] else None,
            'category_id': item[12],
            'warehouse_id': item[13],
            'supplier_id': item[14]
        })
    return jsonify(items_list)

@app.route('/api/token-status')
def api_token_status():
    """API endpoint to check token expiry status."""
    return jsonify({
        'expired': is_token_expired(),
        'last_refresh': last_password_refresh,
        'current_time': time.time()
    })

@app.route('/api/dashboard-config')
def api_dashboard_config():
    """API endpoint to get dashboard configuration."""
    return jsonify({
        'dashboard_id': os.getenv('DASHBOARD_ID'),
        'workspace_url': os.getenv('DATABRICKS_HOST') or workspace_client.config.host,
        'embed_url': get_dashboard_embed_url(),
        'public_url': get_dashboard_public_url(),
        'configured': get_dashboard_embed_url() is not None
    })

@app.route('/api/demand-forecast')
def api_demand_forecast():
    """API endpoint to get demand forecast suggestion."""
    warehouse_id = request.args.get('warehouse_id', type=int)
    category_id = request.args.get('category_id', type=int)
    current_quantity = request.args.get('current_quantity', 0, type=int)
    minimum_stock = request.args.get('minimum_stock', type=int)
    new_quantity = request.args.get('new_quantity', 0, type=int)
    
    if not warehouse_id or not category_id:
        return jsonify({'error': 'warehouse_id and category_id are required'}), 400
    
    suggestion = get_demand_forecast_suggestion(warehouse_id, category_id, current_quantity, minimum_stock, new_quantity)
    return jsonify(suggestion)

# Category management routes
@app.route('/categories')
def categories_route():
    """Show all categories."""
    categories = get_categories()
    low_stock_items = get_low_stock_items()
    return render_template('categories.html', categories=categories, low_stock_count=len(low_stock_items))

@app.route('/categories/add', methods=['GET', 'POST'])
def add_category_route():
    """Add a new category."""
    if request.method == 'POST':
        category_name = request.form.get('category_name', '').strip()
        description = request.form.get('description', '').strip() or None
        
        if category_name:
            if add_category(category_name, description):
                flash('Category added successfully!', 'success')
            else:
                flash('Failed to add category.', 'error')
        else:
            flash('Please fill in the category name.', 'error')
        return redirect(url_for('categories_route'))
    
    low_stock_items = get_low_stock_items()
    return render_template('add_category.html', low_stock_count=len(low_stock_items))

@app.route('/categories/edit/<int:category_id>', methods=['GET', 'POST'])
def edit_category_route(category_id):
    """Edit an existing category."""
    category = get_category(category_id)
    if not category:
        flash('Category not found.', 'error')
        return redirect(url_for('categories_route'))
    
    if request.method == 'POST':
        category_name = request.form.get('category_name', '').strip()
        description = request.form.get('description', '').strip() or None
        
        if category_name:
            if update_category(category_id, category_name, description):
                flash('Category updated successfully!', 'success')
            else:
                flash('Failed to update category.', 'error')
        else:
            flash('Please fill in the category name.', 'error')
        return redirect(url_for('categories_route'))
    
    low_stock_items = get_low_stock_items()
    return render_template('edit_category.html', category=category, low_stock_count=len(low_stock_items))

@app.route('/categories/delete/<int:category_id>')
def delete_category_route(category_id):
    """Delete a category."""
    success, message = delete_category(category_id)
    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')
    return redirect(url_for('categories_route'))

# Warehouse management routes
@app.route('/warehouses')
def warehouses_route():
    """Show all warehouses."""
    warehouses = get_warehouses()
    low_stock_items = get_low_stock_items()
    return render_template('warehouses.html', warehouses=warehouses, low_stock_count=len(low_stock_items))

@app.route('/warehouses/add', methods=['GET', 'POST'])
def add_warehouse_route():
    """Add a new warehouse."""
    if request.method == 'POST':
        warehouse_name = request.form.get('warehouse_name', '').strip()
        address = request.form.get('address', '').strip() or None
        city = request.form.get('city', '').strip() or None
        state = request.form.get('state', '').strip() or None
        country = request.form.get('country', '').strip() or None
        county = request.form.get('county', '').strip() or None
        zipcode = request.form.get('zipcode', '').strip() or None
        latitude = request.form.get('latitude', type=float) or None
        longitude = request.form.get('longitude', type=float) or None
        contact_person = request.form.get('contact_person', '').strip() or None
        phone = request.form.get('phone', '').strip() or None
        email = request.form.get('email', '').strip() or None
        
        if warehouse_name:
            if add_warehouse(warehouse_name, address, city, state, country, county, zipcode, 
                           latitude, longitude, contact_person, phone, email):
                flash('Warehouse added successfully!', 'success')
            else:
                flash('Failed to add warehouse.', 'error')
        else:
            flash('Please fill in the warehouse name.', 'error')
        return redirect(url_for('warehouses_route'))
    
    low_stock_items = get_low_stock_items()
    return render_template('add_warehouse.html', low_stock_count=len(low_stock_items))

@app.route('/warehouses/edit/<int:warehouse_id>', methods=['GET', 'POST'])
def edit_warehouse_route(warehouse_id):
    """Edit an existing warehouse."""
    warehouse = get_warehouse(warehouse_id)
    if not warehouse:
        flash('Warehouse not found.', 'error')
        return redirect(url_for('warehouses_route'))
    
    if request.method == 'POST':
        warehouse_name = request.form.get('warehouse_name', '').strip()
        address = request.form.get('address', '').strip() or None
        city = request.form.get('city', '').strip() or None
        state = request.form.get('state', '').strip() or None
        country = request.form.get('country', '').strip() or None
        county = request.form.get('county', '').strip() or None
        zipcode = request.form.get('zipcode', '').strip() or None
        latitude = request.form.get('latitude', type=float) or None
        longitude = request.form.get('longitude', type=float) or None
        contact_person = request.form.get('contact_person', '').strip() or None
        phone = request.form.get('phone', '').strip() or None
        email = request.form.get('email', '').strip() or None
        
        if warehouse_name:
            if update_warehouse(warehouse_id, warehouse_name, address, city, state, country, county, zipcode, 
                              latitude, longitude, contact_person, phone, email):
                flash('Warehouse updated successfully!', 'success')
            else:
                flash('Failed to update warehouse.', 'error')
        else:
            flash('Please fill in the warehouse name.', 'error')
        return redirect(url_for('warehouses_route'))
    
    low_stock_items = get_low_stock_items()
    return render_template('edit_warehouse.html', warehouse=warehouse, low_stock_count=len(low_stock_items))

@app.route('/warehouses/delete/<int:warehouse_id>')
def delete_warehouse_route(warehouse_id):
    """Delete a warehouse."""
    if delete_warehouse(warehouse_id):
        flash('Warehouse deleted successfully!', 'success')
    else:
        flash('Failed to delete warehouse.', 'error')
    return redirect(url_for('warehouses_route'))

# Supplier management routes
@app.route('/suppliers')
def suppliers_route():
    """Show all suppliers."""
    suppliers = get_suppliers()
    low_stock_items = get_low_stock_items()
    return render_template('suppliers.html', suppliers=suppliers, low_stock_count=len(low_stock_items))

@app.route('/suppliers/add', methods=['GET', 'POST'])
def add_supplier_route():
    """Add a new supplier."""
    if request.method == 'POST':
        supplier_name = request.form.get('supplier_name', '').strip()
        contact_person = request.form.get('contact_person', '').strip() or None
        email = request.form.get('email', '').strip() or None
        phone = request.form.get('phone', '').strip() or None
        address = request.form.get('address', '').strip() or None
        city = request.form.get('city', '').strip() or None
        state = request.form.get('state', '').strip() or None
        country = request.form.get('country', '').strip() or None
        county = request.form.get('county', '').strip() or None
        zipcode = request.form.get('zipcode', '').strip() or None
        latitude = request.form.get('latitude', type=float) or None
        longitude = request.form.get('longitude', type=float) or None
        website = request.form.get('website', '').strip() or None
        tax_id = request.form.get('tax_id', '').strip() or None
        payment_terms = request.form.get('payment_terms', '').strip() or None
        
        if supplier_name:
            if add_supplier(supplier_name, contact_person, email, phone, address, city, state, country, county, 
                          zipcode, latitude, longitude, website, tax_id, payment_terms):
                flash('Supplier added successfully!', 'success')
            else:
                flash('Failed to add supplier.', 'error')
        else:
            flash('Please fill in the supplier name.', 'error')
        return redirect(url_for('suppliers_route'))
    
    low_stock_items = get_low_stock_items()
    return render_template('add_supplier.html', low_stock_count=len(low_stock_items))

@app.route('/suppliers/edit/<int:supplier_id>', methods=['GET', 'POST'])
def edit_supplier_route(supplier_id):
    """Edit an existing supplier."""
    supplier = get_supplier(supplier_id)
    if not supplier:
        flash('Supplier not found.', 'error')
        return redirect(url_for('suppliers_route'))
    
    if request.method == 'POST':
        supplier_name = request.form.get('supplier_name', '').strip()
        contact_person = request.form.get('contact_person', '').strip() or None
        email = request.form.get('email', '').strip() or None
        phone = request.form.get('phone', '').strip() or None
        address = request.form.get('address', '').strip() or None
        city = request.form.get('city', '').strip() or None
        state = request.form.get('state', '').strip() or None
        country = request.form.get('country', '').strip() or None
        county = request.form.get('county', '').strip() or None
        zipcode = request.form.get('zipcode', '').strip() or None
        latitude = request.form.get('latitude', type=float) or None
        longitude = request.form.get('longitude', type=float) or None
        website = request.form.get('website', '').strip() or None
        tax_id = request.form.get('tax_id', '').strip() or None
        payment_terms = request.form.get('payment_terms', '').strip() or None
        
        if supplier_name:
            if update_supplier(supplier_id, supplier_name, contact_person, email, phone, address, city, state, country, 
                             county, zipcode, latitude, longitude, website, tax_id, payment_terms):
                flash('Supplier updated successfully!', 'success')
            else:
                flash('Failed to update supplier.', 'error')
        else:
            flash('Please fill in the supplier name.', 'error')
        return redirect(url_for('suppliers_route'))
    
    low_stock_items = get_low_stock_items()
    return render_template('edit_supplier.html', supplier=supplier, low_stock_count=len(low_stock_items))

@app.route('/suppliers/delete/<int:supplier_id>')
def delete_supplier_route(supplier_id):
    """Delete a supplier."""
    if delete_supplier(supplier_id):
        flash('Supplier deleted successfully!', 'success')
    else:
        flash('Failed to delete supplier. Make sure no items are using this supplier.', 'error')
    return redirect(url_for('suppliers_route'))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.getenv('PORT', 8080))) 