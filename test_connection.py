# test_db_connection.py
import os
import time
from datetime import datetime

import psycopg
from psycopg import sql

# Load environment variables from .env file
try:
    from dotenv import load_dotenv

    load_dotenv()
    print("📄 Loaded environment variables from .env file")
except ImportError:
    print("⚠️  python-dotenv not installed. Using system environment variables.")


def get_connection_string():
    """Build the PostgreSQL connection string."""
    password = os.getenv("PGPASSWORD")
    if not password:
        print("❌ PGPASSWORD not set")
        return None

    conn_string = (
        f"dbname={os.getenv('PGDATABASE')} "
        f"user={os.getenv('PGUSER')} "
        f"password={os.getenv('PGPASSWORD')} "
        f"host={os.getenv('PGHOST')} "
        f"port={os.getenv('PGPORT')} "
        f"sslmode={os.getenv('PGSSLMODE', 'require')} "
        f"application_name={os.getenv('PGAPPNAME', 'test_connection')}"
    )

    return conn_string


def create_schema_and_table(conn, schema_name, table_name):
    """Create schema and inventory_items table if they don't exist."""
    try:
        with conn.cursor() as cur:
            print(f"🔧 Creating schema '{schema_name}' if it doesn't exist...")

            # Create schema
            cur.execute(
                sql.SQL("CREATE SCHEMA IF NOT EXISTS {}").format(
                    sql.Identifier(schema_name)
                )
            )
            print(f"Schema '{schema_name}' ready")

            print(
                f"🔧 Creating table '{schema_name}.{table_name}' if it doesn't exist..."
            )

            # Create inventory_items table (same structure as in app.py)
            create_table_sql = sql.SQL(
                """
                CREATE TABLE IF NOT EXISTS {}.{} (
                    id serial4 NOT NULL,
                    item_name varchar(100) NOT NULL,
                    description text NULL,
                    category varchar(50) NOT NULL,
                    quantity int4 NOT NULL,
                    unit_price float8 NOT NULL,
                    supplier varchar(100) NULL,
                    "location" varchar(100) NULL,
                    minimum_stock int4 NULL,
                    date_added timestamp DEFAULT CURRENT_TIMESTAMP,
                    last_updated timestamp DEFAULT CURRENT_TIMESTAMP
                );
            """
            ).format(
                sql.Identifier(schema_name),
                sql.Identifier(table_name),
                sql.Identifier(table_name),
            )

            cur.execute(create_table_sql)
            print(f"✅ Table '{schema_name}.{table_name}' ready")

            # Commit the changes
            conn.commit()
            print("✅ Schema and table creation committed")

            return True

    except Exception as e:
        print(f"❌ Failed to create schema/table: {str(e)}")
        conn.rollback()
        return False


def insert_sample_data(conn, schema_name, table_name):
    """Insert sample inventory data if table is empty."""
    try:
        with conn.cursor() as cur:
            # Check if table has data
            cur.execute(
                sql.SQL("SELECT COUNT(*) FROM {}.{}").format(
                    sql.Identifier(schema_name), sql.Identifier(table_name)
                )
            )
            count = cur.fetchone()[0]

            if count > 0:
                print(
                    f"ℹ️  Table already has {count} records, skipping sample data insertion"
                )
                return True

            print("🔧 Inserting sample inventory data...")

            # Sample data
            sample_items = [
                (
                    "Laptop - MacBook Pro",
                    "High-performance laptop for development",
                    "Electronics",
                    5,
                    2499.99,
                    "Apple Inc.",
                    "IT Storage Room",
                    2,
                ),
                (
                    "Office Desk",
                    "Adjustable height standing desk",
                    "Furniture",
                    10,
                    399.50,
                    "Office Furniture Ltd.",
                    "Warehouse A",
                    3,
                ),
                (
                    "Safety Helmet",
                    "OSHA approved construction helmet",
                    "Safety Equipment",
                    25,
                    29.99,
                    "Safety First Inc.",
                    "Safety Storage",
                    10,
                ),
                (
                    "Wireless Mouse",
                    "Ergonomic wireless mouse",
                    "Electronics",
                    50,
                    45.99,
                    "Tech Accessories Co.",
                    "IT Storage Room",
                    20,
                ),
                (
                    "Office Chair",
                    "Ergonomic office chair with lumbar support",
                    "Furniture",
                    15,
                    299.99,
                    "Comfort Seating Ltd.",
                    "Warehouse A",
                    5,
                ),
            ]

            insert_sql = sql.SQL(
                """
                INSERT INTO {}.{}
                (item_name, description, category, quantity, unit_price, supplier, location, minimum_stock, date_added, last_updated)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            ).format(sql.Identifier(schema_name), sql.Identifier(table_name))

            current_time = datetime.now()
            for item in sample_items:
                item_data = item + (current_time, current_time)
                cur.execute(insert_sql, item_data)

            conn.commit()
            print(f"✅ Inserted {len(sample_items)} sample inventory items")

            return True

    except Exception as e:
        print(f"❌ Failed to insert sample data: {str(e)}")
        conn.rollback()
        return False


def test_table_operations(conn, schema_name, table_name):
    """Test basic table operations."""
    try:
        with conn.cursor() as cur:
            print("🧪 Testing table operations...")

            # Test SELECT
            cur.execute(
                sql.SQL("SELECT COUNT(*) FROM {}.{}").format(
                    sql.Identifier(schema_name), sql.Identifier(table_name)
                )
            )
            total_count = cur.fetchone()[0]
            print(f"✅ Total items: {total_count}")

            # Test SELECT with WHERE clause
            cur.execute(
                sql.SQL(
                    """
                SELECT item_name, quantity, minimum_stock
                FROM {}.{}
                WHERE quantity <= minimum_stock
            """
                ).format(sql.Identifier(schema_name), sql.Identifier(table_name))
            )

            low_stock = cur.fetchall()
            if low_stock:
                print(f"⚠️  Low stock items found: {len(low_stock)}")
                for item in low_stock:
                    print(f"   - {item[0]}: {item[1]} (min: {item[2]})")
            else:
                print("✅ No low stock items")

            # Test GROUP BY
            cur.execute(
                sql.SQL(
                    """
                SELECT category, COUNT(*) as item_count, SUM(quantity * unit_price) as total_value
                FROM {}.{}
                GROUP BY category
                ORDER BY total_value DESC
            """
                ).format(sql.Identifier(schema_name), sql.Identifier(table_name))
            )

            categories = cur.fetchall()
            print("📊 Inventory by category:")
            for cat in categories:
                print(f"   - {cat[0]}: {cat[1]} items, ${cat[2]:,.2f} total value")

            return True

    except Exception as e:
        print(f"❌ Table operations test failed: {str(e)}")
        return False


def test_connection():
    """Test the Postgres database connection and create inventory table."""

    # Get connection string
    conn_string = get_connection_string()
    if not conn_string:
        return False

    print("🔄 Testing database connection...")
    print(f"Connecting to: {os.getenv('PGHOST')}:{os.getenv('PGPORT')}")
    print(f"Database: {os.getenv('PGDATABASE')}")
    print(f"User: {os.getenv('PGUSER')}")

    try:
        # Test basic connection
        with psycopg.connect(conn_string) as conn:
            with conn.cursor() as cur:
                # Test basic query
                cur.execute("SELECT version();")
                version = cur.fetchone()[0]
                print(f"✅ Connected successfully!")
                print(f"PostgreSQL version: {version}")

                # Get current user and database
                cur.execute("SELECT current_database(), current_user;")
                db, user = cur.fetchone()
                print(f"Current database: {db}")
                print(f"Current user: {user}")

            # Get schema and table names
            schema_name = os.getenv("POSTGRES_SCHEMA", "inventory_app")
            table_name = os.getenv("POSTGRES_TABLE", "inventory_items")

            print(f"\n🏗️  Setting up inventory schema and table...")

            # Create schema and table
            if not create_schema_and_table(conn, schema_name, table_name):
                return False

            # Insert sample data
            if not insert_sample_data(conn, schema_name, table_name):
                return False

            # Test table operations
            if not test_table_operations(conn, schema_name, table_name):
                return False

        return True

    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")
        return False


def check_environment():
    """Check if all required environment variables are set."""
    required_vars = ["PGDATABASE", "PGUSER", "PGHOST", "PGPORT", "PGPASSWORD"]
    missing_vars = []

    print("🔍 Checking environment variables...")
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Don't print sensitive values, just confirm they exist
            if var in ["PGPASSWORD"]:
                print(f"✅ {var}: {'*' * 8}")
            elif var in ["PGHOST", "PGDATABASE"]:
                print(f"✅ {var}: {value}")
            else:
                print(
                    f"✅ {var}: {'*' * min(len(value), 8) if len(value) > 0 else 'SET'}"
                )
        else:
            print(f"❌ {var}: NOT SET")
            missing_vars.append(var)

    # Check optional vars
    optional_vars = ["PGSSLMODE", "PGAPPNAME", "POSTGRES_SCHEMA", "POSTGRES_TABLE"]
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {value}")
        else:
            print(f"⚠️  {var}: NOT SET (using default)")

    return len(missing_vars) == 0, missing_vars


if __name__ == "__main__":
    print("=" * 60)
    print("🚀 POSTGRES CONNECTION TEST & TABLE SETUP")
    print("=" * 60)

    # Check environment first
    env_ok, missing = check_environment()

    if not env_ok:
        print(f"\n❌ Missing required environment variables: {', '.join(missing)}")
        print("Please set these variables and try again.")
        exit(1)

    print("\n" + "=" * 60)

    # Test connection and setup tables
    if test_connection():
        print(
            "\n🎉 All tests passed! Database connection is working and inventory table is ready."
        )
    else:
        print("\n💥 Connection test failed. Check your configuration.")
