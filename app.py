from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
import psycopg
import os
import time
from datetime import datetime, timedelta
from databricks import sdk
from psycopg import sql
from psycopg_pool import ConnectionPool
import uuid

# Database connection setup
workspace_client = sdk.WorkspaceClient()
postgres_password = None
last_password_refresh = 0
connection_pool = None

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
        # Check if we should use OAuth or explicit postgres user
        postgres_user = os.getenv('POSTGRES_USER')
        postgres_pass = os.getenv('POSTGRES_PASSWORD')
        
        if postgres_user and postgres_pass:
            # Use explicit credentials
            password = postgres_pass
        else:
            # Use OAuth token
            refresh_oauth_token()
            password = postgres_password
            
        conn_string = (
            f"dbname={os.getenv('PGDATABASE')} "
            f"user={postgres_user or os.getenv('PGUSER')} "
            f"password={password} "
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
    
    # Recreate pool if token expired (only for OAuth mode)
    if not os.getenv('POSTGRES_USER') and (postgres_password is None or time.time() - last_password_refresh > 900):
        if connection_pool:
            connection_pool.close()
            connection_pool = None
    
    return get_connection_pool().connection()

def get_schema_name():
    """Get the schema name in the format {PGAPPNAME}_schema_{PGUSER}."""
    pgappname = os.getenv("PGAPPNAME", "ordering_app")
    pguser = os.getenv("PGUSER", "").replace('-', '')
    return f"{pgappname}_schema_{pguser}"

def init_database():
    """Initialize database schema and tables for ordering system."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                schema_name = get_schema_name()
                
                cur.execute(sql.SQL("CREATE SCHEMA IF NOT EXISTS {}").format(sql.Identifier(schema_name)))
                
                # Products table
                cur.execute(sql.SQL("""
                    CREATE TABLE IF NOT EXISTS {}.products (
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
                    )
                """).format(sql.Identifier(schema_name)))
                
                # Customers table
                cur.execute(sql.SQL("""
                    CREATE TABLE IF NOT EXISTS {}.customers (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(100) NOT NULL,
                        email VARCHAR(100) UNIQUE NOT NULL,
                        phone VARCHAR(20),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """).format(sql.Identifier(schema_name)))
                
                # Orders table
                cur.execute(sql.SQL("""
                    CREATE TABLE IF NOT EXISTS {}.orders (
                        id SERIAL PRIMARY KEY,
                        customer_id INTEGER REFERENCES {}.customers(id),
                        order_number VARCHAR(50) UNIQUE NOT NULL,
                        status VARCHAR(20) DEFAULT 'pending',
                        total_amount DECIMAL(10,2) NOT NULL,
                        pickup_time TIMESTAMP,
                        pickup_slot_id INTEGER,
                        notes TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """).format(sql.Identifier(schema_name), sql.Identifier(schema_name)))
                
                # Order items table
                cur.execute(sql.SQL("""
                    CREATE TABLE IF NOT EXISTS {}.order_items (
                        id SERIAL PRIMARY KEY,
                        order_id INTEGER REFERENCES {}.orders(id) ON DELETE CASCADE,
                        product_id INTEGER REFERENCES {}.products(id),
                        quantity INTEGER NOT NULL,
                        unit_price DECIMAL(10,2) NOT NULL,
                        subtotal DECIMAL(10,2) NOT NULL
                    )
                """).format(sql.Identifier(schema_name), sql.Identifier(schema_name), sql.Identifier(schema_name)))
                
                # Pickup slots table
                cur.execute(sql.SQL("""
                    CREATE TABLE IF NOT EXISTS {}.pickup_slots (
                        id SERIAL PRIMARY KEY,
                        slot_time TIMESTAMP NOT NULL,
                        max_orders INTEGER DEFAULT 10,
                        current_orders INTEGER DEFAULT 0,
                        is_available BOOLEAN DEFAULT TRUE
                    )
                """).format(sql.Identifier(schema_name)))
                
                conn.commit()
                return True
    except Exception as e:
        print(f"Database initialization error: {e}")
        return False

# Product Management Functions
def get_products():
    """Get all active products."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                schema = get_schema_name()
                cur.execute(sql.SQL("""
                    SELECT id, name, description, category, price, stock_quantity, reserved_quantity, image_url
                    FROM {}.products 
                    WHERE is_active = TRUE
                    ORDER BY category, name
                """).format(sql.Identifier(schema)))
                return cur.fetchall()
    except Exception as e:
        print(f"Get products error: {e}")
        return []

def get_available_stock(product_id):
    """Get available stock for a product (total - reserved)."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                schema = get_schema_name()
                cur.execute(sql.SQL("""
                    SELECT stock_quantity - reserved_quantity as available
                    FROM {}.products 
                    WHERE id = %s AND is_active = TRUE
                """).format(sql.Identifier(schema)), (product_id,))
                result = cur.fetchone()
                return result[0] if result else 0
    except Exception as e:
        print(f"Get available stock error: {e}")
        return 0

# Customer Management Functions
def create_customer(name, email, phone=None):
    """Create a new customer."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                schema = get_schema_name()
                cur.execute(sql.SQL("""
                    INSERT INTO {}.customers (name, email, phone)
                    VALUES (%s, %s, %s)
                    RETURNING id
                """).format(sql.Identifier(schema)), (name, email, phone))
                customer_id = cur.fetchone()[0]
                conn.commit()
                return customer_id
    except Exception as e:
        print(f"Create customer error: {e}")
        return None

def get_customer_by_email(email):
    """Get customer by email."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                schema = get_schema_name()
                cur.execute(sql.SQL("""
                    SELECT id, name, email, phone FROM {}.customers 
                    WHERE email = %s
                """).format(sql.Identifier(schema)), (email,))
                return cur.fetchone()
    except Exception as e:
        print(f"Get customer error: {e}")
        return None

# Order Management Functions
def create_order(customer_id, cart_items, pickup_time=None, notes=None):
    """Create a new order with items."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                schema = get_schema_name()
                
                # Generate order number
                order_number = f"ORD-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
                
                # Calculate total
                total_amount = sum(item['quantity'] * item['price'] for item in cart_items)
                
                # Create order
                cur.execute(sql.SQL("""
                    INSERT INTO {}.orders (customer_id, order_number, total_amount, pickup_time, notes)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                """).format(sql.Identifier(schema)), 
                (customer_id, order_number, total_amount, pickup_time, notes))
                
                order_id = cur.fetchone()[0]
                
                # Add order items and reserve stock
                for item in cart_items:
                    # Add order item
                    subtotal = item['quantity'] * item['price']
                    cur.execute(sql.SQL("""
                        INSERT INTO {}.order_items (order_id, product_id, quantity, unit_price, subtotal)
                        VALUES (%s, %s, %s, %s, %s)
                    """).format(sql.Identifier(schema)), 
                    (order_id, item['product_id'], item['quantity'], item['price'], subtotal))
                    
                    # Reserve stock
                    cur.execute(sql.SQL("""
                        UPDATE {}.products 
                        SET reserved_quantity = reserved_quantity + %s
                        WHERE id = %s
                    """).format(sql.Identifier(schema)), (item['quantity'], item['product_id']))
                
                conn.commit()
                return order_id, order_number
                
    except Exception as e:
        print(f"Create order error: {e}")
        return None, None

def get_order(order_id):
    """Get order details with items."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                schema = get_schema_name()
                
                # Get order info
                cur.execute(sql.SQL("""
                    SELECT o.id, o.order_number, o.status, o.total_amount, o.pickup_time, o.notes,
                           o.created_at, c.name, c.email, c.phone
                    FROM {}.orders o
                    JOIN {}.customers c ON o.customer_id = c.id
                    WHERE o.id = %s
                """).format(sql.Identifier(schema), sql.Identifier(schema)), (order_id,))
                
                order = cur.fetchone()
                if not order:
                    return None
                
                # Get order items
                cur.execute(sql.SQL("""
                    SELECT oi.product_id, oi.quantity, oi.unit_price, oi.subtotal,
                           p.name, p.description
                    FROM {}.order_items oi
                    JOIN {}.products p ON oi.product_id = p.id
                    WHERE oi.order_id = %s
                """).format(sql.Identifier(schema), sql.Identifier(schema)), (order_id,))
                
                items = cur.fetchall()
                
                return {
                    'order': order,
                    'order_items': items
                }
    except Exception as e:
        print(f"Get order error: {e}")
        return None

def update_order_status(order_id, status):
    """Update order status."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                schema = get_schema_name()
                cur.execute(sql.SQL("""
                    UPDATE {}.orders 
                    SET status = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """).format(sql.Identifier(schema)), (status, order_id))
                conn.commit()
                return True
    except Exception as e:
        print(f"Update order status error: {e}")
        return False

def cancel_order(order_id):
    """Cancel an order and release reserved stock."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                schema = get_schema_name()
                
                # Get order items to release stock
                cur.execute(sql.SQL("""
                    SELECT product_id, quantity FROM {}.order_items WHERE order_id = %s
                """).format(sql.Identifier(schema)), (order_id,))
                items = cur.fetchall()
                
                # Release reserved stock
                for product_id, quantity in items:
                    cur.execute(sql.SQL("""
                        UPDATE {}.products 
                        SET reserved_quantity = reserved_quantity - %s
                        WHERE id = %s
                    """).format(sql.Identifier(schema)), (quantity, product_id))
                
                # Update order status
                cur.execute(sql.SQL("""
                    UPDATE {}.orders 
                    SET status = 'cancelled', updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                """).format(sql.Identifier(schema)), (order_id,))
                
                conn.commit()
                return True
    except Exception as e:
        print(f"Cancel order error: {e}")
        return False

# Pickup Slot Management Functions
def get_available_pickup_slots(days_ahead=7):
    """Get available pickup slots for the next few days."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                schema = get_schema_name()
                
                # Generate slots if they don't exist
                generate_pickup_slots(days_ahead)
                
                start_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
                end_time = start_time + timedelta(days=days_ahead)
                
                cur.execute(sql.SQL("""
                    SELECT id, slot_time, max_orders, current_orders, is_available
                    FROM {}.pickup_slots
                    WHERE slot_time BETWEEN %s AND %s 
                    AND is_available = TRUE 
                    AND current_orders < max_orders
                    ORDER BY slot_time
                """).format(sql.Identifier(schema)), (start_time, end_time))
                
                return cur.fetchall()
    except Exception as e:
        print(f"Get pickup slots error: {e}")
        return []

def generate_pickup_slots(days_ahead=7):
    """Generate pickup slots for the next few days."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                schema = get_schema_name()
                
                # Operating hours: 9 AM to 6 PM, every hour
                start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
                
                for day in range(days_ahead):
                    current_date = start_date + timedelta(days=day)
                    
                    # Skip weekends for now (can be customized)
                    if current_date.weekday() >= 5:  # Saturday = 5, Sunday = 6
                        continue
                    
                    for hour in range(9, 18):  # 9 AM to 5 PM
                        slot_time = current_date.replace(hour=hour)
                        
                        # Check if slot already exists
                        cur.execute(sql.SQL("""
                            SELECT id FROM {}.pickup_slots WHERE slot_time = %s
                        """).format(sql.Identifier(schema)), (slot_time,))
                        
                        if not cur.fetchone():
                            cur.execute(sql.SQL("""
                                INSERT INTO {}.pickup_slots (slot_time, max_orders, current_orders, is_available)
                                VALUES (%s, %s, %s, %s)
                            """).format(sql.Identifier(schema)), (slot_time, 10, 0, True))
                
                conn.commit()
                return True
    except Exception as e:
        print(f"Generate pickup slots error: {e}")
        return False

def get_customer_orders(customer_id, status=None):
    """Get orders for a specific customer."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                schema = get_schema_name()
                
                if status:
                    cur.execute(sql.SQL("""
                        SELECT id, order_number, status, total_amount, pickup_time, created_at
                        FROM {}.orders 
                        WHERE customer_id = %s AND status = %s
                        ORDER BY created_at DESC
                    """).format(sql.Identifier(schema)), (customer_id, status))
                else:
                    cur.execute(sql.SQL("""
                        SELECT id, order_number, status, total_amount, pickup_time, created_at
                        FROM {}.orders 
                        WHERE customer_id = %s
                        ORDER BY created_at DESC
                    """).format(sql.Identifier(schema)), (customer_id,))
                
                return cur.fetchall()
    except Exception as e:
        print(f"Get customer orders error: {e}")
        return []

# Cart Management Functions
def add_to_cart(product_id, quantity):
    """Add item to session cart."""
    if 'cart' not in session:
        session['cart'] = {}
    
    cart = session['cart']
    product_id_str = str(product_id)
    
    if product_id_str in cart:
        cart[product_id_str] += quantity
    else:
        cart[product_id_str] = quantity
    
    session['cart'] = cart
    session.modified = True

def remove_from_cart(product_id):
    """Remove item from session cart."""
    if 'cart' in session:
        cart = session['cart']
        product_id_str = str(product_id)
        if product_id_str in cart:
            del cart[product_id_str]
            session['cart'] = cart
            session.modified = True

def get_cart_items():
    """Get cart items with product details."""
    if 'cart' not in session or not session['cart']:
        return []
    
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                schema = get_schema_name()
                cart_items = []
                
                for product_id, quantity in session['cart'].items():
                    cur.execute(sql.SQL("""
                        SELECT id, name, description, price, stock_quantity, reserved_quantity
                        FROM {}.products 
                        WHERE id = %s AND is_active = TRUE
                    """).format(sql.Identifier(schema)), (int(product_id),))
                    
                    product = cur.fetchone()
                    if product:
                        available_stock = product[4] - product[5]  # stock_quantity - reserved_quantity
                        cart_items.append({
                            'product_id': product[0],
                            'name': product[1],
                            'description': product[2],
                            'price': float(product[3]),
                            'quantity': quantity,
                            'available_stock': available_stock,
                            'subtotal': float(product[3]) * quantity
                        })
                
                return cart_items
    except Exception as e:
        print(f"Get cart items error: {e}")
        return []

def clear_cart():
    """Clear the session cart."""
    if 'cart' in session:
        session.pop('cart')
        session.modified = True

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key')

# Initialize database
if not init_database():
    print("Failed to initialize database")

@app.route('/')
def index():
    """Main page showing all products and shopping cart."""
    products = get_products()
    cart_items = get_cart_items()
    cart_total = sum(item['subtotal'] for item in cart_items)
    return render_template('index.html', products=products, cart_items=cart_items, cart_total=cart_total)

@app.route('/add-to-cart', methods=['POST'])
def add_to_cart_route():
    """Add item to cart."""
    product_id = request.form.get('product_id', type=int)
    quantity = request.form.get('quantity', type=int, default=1)
    
    if product_id and quantity > 0:
        # Check available stock
        available = get_available_stock(product_id)
        if available >= quantity:
            add_to_cart(product_id, quantity)
            flash('Item added to cart!', 'success')
        else:
            flash(f'Sorry, only {available} items available in stock.', 'error')
    else:
        flash('Invalid product or quantity.', 'error')
    
    return redirect(url_for('index'))

@app.route('/remove-from-cart/<int:product_id>')
def remove_from_cart_route(product_id):
    """Remove item from cart."""
    remove_from_cart(product_id)
    flash('Item removed from cart.', 'success')
    return redirect(url_for('cart_route'))

@app.route('/cart')
def cart_route():
    """Show cart and checkout page."""
    cart_items = get_cart_items()
    cart_total = sum(item['subtotal'] for item in cart_items)
    pickup_slots = get_available_pickup_slots()
    return render_template('cart.html', cart_items=cart_items, cart_total=cart_total, pickup_slots=pickup_slots)

@app.route('/checkout', methods=['POST'])
def checkout_route():
    """Process checkout and create order."""
    cart_items = get_cart_items()
    if not cart_items:
        flash('Your cart is empty.', 'error')
        return redirect(url_for('index'))
    
    # Get customer info
    name = request.form.get('name', '').strip()
    email = request.form.get('email', '').strip()
    phone = request.form.get('phone', '').strip()
    pickup_time = request.form.get('pickup_time')
    notes = request.form.get('notes', '').strip()
    
    if not name or not email:
        flash('Name and email are required.', 'error')
        return redirect(url_for('cart_route'))
    
    try:
        # Get or create customer
        customer = get_customer_by_email(email)
        if customer:
            customer_id = customer[0]
        else:
            customer_id = create_customer(name, email, phone)
            
        if not customer_id:
            flash('Error creating customer account.', 'error')
            return redirect(url_for('cart_route'))
        
        # Create order
        pickup_datetime = None
        if pickup_time:
            pickup_datetime = datetime.fromisoformat(pickup_time.replace('Z', '+00:00'))
        
        order_id, order_number = create_order(customer_id, cart_items, pickup_datetime, notes)
        
        if order_id:
            clear_cart()
            flash(f'Order {order_number} placed successfully!', 'success')
            return redirect(url_for('order_confirmation_route', order_id=order_id))
        else:
            flash('Error creating order. Please try again.', 'error')
            return redirect(url_for('cart_route'))
            
    except Exception as e:
        print(f"Checkout error: {e}")
        flash('Error processing order. Please try again.', 'error')
        return redirect(url_for('cart_route'))

@app.route('/order-confirmation/<int:order_id>')
def order_confirmation_route(order_id):
    """Show order confirmation page."""
    order_details = get_order(order_id)
    if not order_details:
        flash('Order not found.', 'error')
        return redirect(url_for('index'))
    
    return render_template('order_confirmation.html', order_details=order_details)

@app.route('/my-orders')
def my_orders_route():
    """Show customer orders page."""
    email = request.args.get('email')
    if not email:
        return render_template('my_orders.html', orders=[], email='')
    
    customer = get_customer_by_email(email)
    if not customer:
        flash('No orders found for this email.', 'warning')
        return render_template('my_orders.html', orders=[], email=email)
    
    orders = get_customer_orders(customer[0])
    return render_template('my_orders.html', orders=orders, email=email)

@app.route('/cancel-order/<int:order_id>')
def cancel_order_route(order_id):
    """Cancel an order."""
    if cancel_order(order_id):
        flash('Order cancelled successfully.', 'success')
    else:
        flash('Failed to cancel order.', 'error')
    
    # Redirect back to my orders with email if provided
    email = request.args.get('email')
    if email:
        return redirect(url_for('my_orders_route', email=email))
    return redirect(url_for('index'))

@app.route('/api/products')
def api_products():
    """API endpoint to get all products as JSON."""
    products = get_products()
    products_list = []
    for product in products:
        available_stock = product[4] - product[5]  # stock_quantity - reserved_quantity
        products_list.append({
            'id': product[0],
            'name': product[1],
            'description': product[2],
            'category': product[3],
            'price': float(product[4]),
            'available_stock': available_stock,
            'image_url': product[7]
        })
    return jsonify(products_list)

@app.route('/api/stock/<int:product_id>')
def api_stock(product_id):
    """API endpoint to get available stock for a product."""
    available = get_available_stock(product_id)
    return jsonify({'product_id': product_id, 'available_stock': available})

@app.route('/api/cart')
def api_cart():
    """API endpoint to get cart contents."""
    cart_items = get_cart_items()
    cart_total = sum(item['subtotal'] for item in cart_items)
    return jsonify({
        'items': cart_items,
        'total': cart_total,
        'item_count': len(cart_items)
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.getenv('PORT', 8080))) 