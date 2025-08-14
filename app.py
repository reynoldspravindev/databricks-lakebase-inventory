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

# Database connection setup
workspace_client = sdk.WorkspaceClient()
postgres_password = None
last_password_refresh = 0
connection_pool = None

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

def init_database():
    """Initialize database schema and table."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                schema_name = get_schema_name()
                table_name = os.getenv("POSTGRES_TABLE", "inventory_items")
                
                # Create schema
                cur.execute(sql.SQL("CREATE SCHEMA IF NOT EXISTS {}").format(sql.Identifier(schema_name)))
                
                # Grant permissions on schema to current user
                current_user = os.getenv('PGUSER')
                if current_user:
                    cur.execute(sql.SQL("GRANT USAGE ON SCHEMA {} TO {}").format(
                        sql.Identifier(schema_name), 
                        sql.Identifier(current_user)
                    ))
                    cur.execute(sql.SQL("GRANT CREATE ON SCHEMA {} TO {}").format(
                        sql.Identifier(schema_name), 
                        sql.Identifier(current_user)
                    ))
                
                # Create table
                cur.execute(sql.SQL("""
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
	last_updated timestamp DEFAULT CURRENT_TIMESTAMP,
	CONSTRAINT {}_pkey PRIMARY KEY (id)
);
                """).format(sql.Identifier(schema_name), sql.Identifier(table_name), sql.Identifier(table_name)))
                
                # Grant permissions on table to current user
                if current_user:
                    cur.execute(sql.SQL("GRANT ALL PRIVILEGES ON TABLE {}.{} TO {}").format(
                        sql.Identifier(schema_name),
                        sql.Identifier(table_name),
                        sql.Identifier(current_user)
                    ))
                    # Grant usage on sequence for serial primary key
                    cur.execute(sql.SQL("GRANT USAGE, SELECT ON SEQUENCE {}.{}_id_seq TO {}").format(
                        sql.Identifier(schema_name),
                        sql.Identifier(table_name),
                        sql.Identifier(current_user)
                    ))
                
                conn.commit()
                return True
    except Exception as e:
        print(f"Database initialization error: {e}")
        return False

def fix_schema_permissions():
    """Fix schema and table permissions for the current user."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                schema_name = get_schema_name()
                table_name = os.getenv("POSTGRES_TABLE", "inventory_items")
                current_user = os.getenv('PGUSER')
                
                if not current_user:
                    print("❌ PGUSER environment variable not set")
                    return False
                
                print(f"🔧 Fixing permissions for user '{current_user}' on schema '{schema_name}'...")
                
                # Grant schema permissions
                cur.execute(sql.SQL("GRANT USAGE ON SCHEMA {} TO {}").format(
                    sql.Identifier(schema_name), 
                    sql.Identifier(current_user)
                ))
                cur.execute(sql.SQL("GRANT CREATE ON SCHEMA {} TO {}").format(
                    sql.Identifier(schema_name), 
                    sql.Identifier(current_user)
                ))
                
                # Grant table permissions
                cur.execute(sql.SQL("GRANT ALL PRIVILEGES ON TABLE {}.{} TO {}").format(
                    sql.Identifier(schema_name),
                    sql.Identifier(table_name),
                    sql.Identifier(current_user)
                ))
                
                # Grant sequence permissions
                cur.execute(sql.SQL("GRANT USAGE, SELECT ON SEQUENCE {}.{}_id_seq TO {}").format(
                    sql.Identifier(schema_name),
                    sql.Identifier(table_name),
                    sql.Identifier(current_user)
                ))
                
                conn.commit()
                print("✅ Permissions fixed successfully!")
                return True
                
    except Exception as e:
        print(f"❌ Error fixing permissions: {e}")
        return False

def add_inventory_item(item_name, description, category, quantity, unit_price, supplier=None, location=None, minimum_stock=None):
    """Add a new inventory item."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                schema = get_schema_name()
                cur.execute(sql.SQL("""
                    INSERT INTO {}.inventory_items 
                    (item_name, description, category, quantity, unit_price, supplier, location, minimum_stock, date_added, last_updated) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """).format(sql.Identifier(schema)), 
                (item_name, description, category, quantity, unit_price, supplier, location, minimum_stock, datetime.now(), datetime.now()))
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
                
                # Prepare the bulk insert
                insert_query = sql.SQL("""
                    INSERT INTO {}.inventory_items 
                    (item_name, description, category, quantity, unit_price, supplier, location, minimum_stock, date_added, last_updated) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """).format(sql.Identifier(schema))
                
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
    category = row.get('category', '').strip()
    
    # Validate required fields
    if not item_name:
        errors.append(f"Row {row_num}: item_name is required")
    elif len(item_name) > 100:
        errors.append(f"Row {row_num}: item_name must be 100 characters or less")
        
    if not category:
        errors.append(f"Row {row_num}: category is required")
    elif len(category) > 50:
        errors.append(f"Row {row_num}: category must be 50 characters or less")
    
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
    location = row.get('location', '').strip() or None
    
    if supplier and len(supplier) > 100:
        errors.append(f"Row {row_num}: supplier must be 100 characters or less")
        
    if location and len(location) > 100:
        errors.append(f"Row {row_num}: location must be 100 characters or less")
    
    # Validate minimum_stock
    minimum_stock = None
    if row.get('minimum_stock', '').strip():
        try:
            minimum_stock = int(row.get('minimum_stock'))
            if minimum_stock < 0:
                errors.append(f"Row {row_num}: minimum_stock must be 0 or greater")
        except (ValueError, TypeError):
            errors.append(f"Row {row_num}: minimum_stock must be a valid number or empty")
    
    if errors:
        return None, errors
    
    return (item_name, description, category, quantity, unit_price, supplier, location, minimum_stock, datetime.now(), datetime.now()), []

def process_csv_file(file_content):
    """Process uploaded CSV file and return results."""
    try:
        # Parse CSV content
        csv_reader = csv.DictReader(io.StringIO(file_content))
        
        # Expected columns
        required_columns = {'item_name', 'category', 'quantity', 'unit_price'}
        optional_columns = {'description', 'supplier', 'location', 'minimum_stock'}
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
    """Get all inventory items."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                schema = get_schema_name()
                cur.execute(sql.SQL("""
                    SELECT id, item_name, description, category, quantity, unit_price, supplier, location, minimum_stock, date_added, last_updated 
                    FROM {}.inventory_items ORDER BY item_name ASC
                """).format(sql.Identifier(schema)))
                return cur.fetchall()
    except Exception as e:
        print(f"Get inventory items error: {e}")
        return []

def get_inventory_item(item_id):
    """Get a specific inventory item by ID."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                schema = get_schema_name()
                cur.execute(sql.SQL("""
                    SELECT id, item_name, description, category, quantity, unit_price, supplier, location, minimum_stock, date_added, last_updated 
                    FROM {}.inventory_items WHERE id = %s
                """).format(sql.Identifier(schema)), (item_id,))
                return cur.fetchone()
    except Exception as e:
        print(f"Get inventory item error: {e}")
        return None

def update_inventory_item(item_id, item_name, description, category, quantity, unit_price, supplier=None, location=None, minimum_stock=None):
    """Update an existing inventory item."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                schema = get_schema_name()
                cur.execute(sql.SQL("""
                    UPDATE {}.inventory_items 
                    SET item_name = %s, description = %s, category = %s, quantity = %s, unit_price = %s, 
                        supplier = %s, location = %s, minimum_stock = %s, last_updated = %s
                    WHERE id = %s
                """).format(sql.Identifier(schema)), 
                (item_name, description, category, quantity, unit_price, supplier, location, minimum_stock, datetime.now(), item_id))
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
                cur.execute(sql.SQL("DELETE FROM {}.inventory_items WHERE id = %s").format(sql.Identifier(schema)), (item_id,))
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
                cur.execute(sql.SQL("""
                    SELECT id, item_name, description, category, quantity, unit_price, supplier, location, minimum_stock, date_added, last_updated 
                    FROM {}.inventory_items 
                    WHERE minimum_stock IS NOT NULL AND quantity <= minimum_stock
                    ORDER BY (quantity - minimum_stock) ASC
                """).format(sql.Identifier(schema)))
                return cur.fetchall()
    except Exception as e:
        print(f"Get low stock items error: {e}")
        return []

def get_dashboard_embed_url():
    """Generate dashboard embed URL with proper authentication."""
    try:
        # Get workspace URL from environment or workspace client
        workspace_url = os.getenv('DATABRICKS_HOST') or workspace_client.config.host
        dashboard_id = os.getenv('DASHBOARD_ID')  # Set this in your environment
        
        if not dashboard_id:
            return None
            
        # Construct embed URL
        base_url = workspace_url.rstrip('/')
        embed_url = f"{base_url}/dashboardsv3/{dashboard_id}/embed"
        
        # Add authentication parameters
        if refresh_oauth_token():
            embed_url += f"?access_token={postgres_password}"
        
        return embed_url
    except Exception as e:
        print(f"Dashboard URL generation error: {e}")
        return None

def get_dashboard_public_url():
    """Get the public dashboard URL for opening in new tab."""
    try:
        workspace_url = os.getenv('DATABRICKS_HOST') or workspace_client.config.host
        dashboard_id = os.getenv('DASHBOARD_ID')
        
        if not dashboard_id:
            return None
            
        base_url = workspace_url.rstrip('/')
        return f"{base_url}/dashboardsv3/{dashboard_id}"
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
    # Try to fix permissions if initialization failed
    print("Attempting to fix permissions...")
    fix_schema_permissions()

@app.route('/')
def index():
    """Main page showing all inventory items."""
    items = get_inventory_items()
    low_stock_items = get_low_stock_items()
    return render_template('index.html', items=items, low_stock_count=len(low_stock_items))

@app.route('/add', methods=['GET', 'POST'])
def add_item_route():
    """Add a new inventory item."""
    if request.method == 'POST':
        item_name = request.form.get('item_name', '').strip()
        description = request.form.get('description', '').strip()
        category = request.form.get('category', '').strip()
        quantity = request.form.get('quantity', type=int)
        unit_price = request.form.get('unit_price', type=float)
        supplier = request.form.get('supplier', '').strip() or None
        location = request.form.get('location', '').strip() or None
        minimum_stock = request.form.get('minimum_stock', type=int) or None
        
        if item_name and category and quantity is not None and unit_price is not None:
            if add_inventory_item(item_name, description, category, quantity, unit_price, supplier, location, minimum_stock):
                flash('Item added successfully!', 'success')
            else:
                flash('Failed to add item.', 'error')
        else:
            flash('Please fill in all required fields.', 'error')
        return redirect(url_for('index'))
    
    low_stock_items = get_low_stock_items()
    return render_template('add_item.html', low_stock_count=len(low_stock_items))

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
    template_content = """item_name,description,category,quantity,unit_price,supplier,location,minimum_stock
"Laptop - Example Model","High-performance laptop for office use","Electronics",5,1299.99,"Tech Supplier Co.","IT Storage Room",2
"Office Desk","Adjustable height standing desk","Furniture",10,399.50,"Office Furniture Ltd.","Warehouse A",3
"Safety Helmet","OSHA approved construction helmet","Safety Equipment",25,29.99,"Safety First Inc.","Safety Storage",10"""
    
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
        category = request.form.get('category', '').strip()
        quantity = request.form.get('quantity', type=int)
        unit_price = request.form.get('unit_price', type=float)
        supplier = request.form.get('supplier', '').strip() or None
        location = request.form.get('location', '').strip() or None
        minimum_stock = request.form.get('minimum_stock', type=int) or None
        
        if item_name and category and quantity is not None and unit_price is not None:
            if update_inventory_item(item_id, item_name, description, category, quantity, unit_price, supplier, location, minimum_stock):
                flash('Item updated successfully!', 'success')
            else:
                flash('Failed to update item.', 'error')
        else:
            flash('Please fill in all required fields.', 'error')
        return redirect(url_for('index'))
    
    low_stock_items = get_low_stock_items()
    return render_template('edit_item.html', item=item, low_stock_count=len(low_stock_items))

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
            'category': item[3],
            'quantity': item[4],
            'unit_price': item[5],
            'supplier': item[6],
            'location': item[7],
            'minimum_stock': item[8],
            'date_added': item[9].isoformat() if item[9] else None,
            'last_updated': item[10].isoformat() if item[10] else None
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

@app.route('/api/fix-permissions')
def api_fix_permissions():
    """API endpoint to manually fix database permissions."""
    try:
        success = fix_schema_permissions()
        return jsonify({
            'success': success,
            'message': 'Permissions fixed successfully!' if success else 'Failed to fix permissions'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error fixing permissions: {str(e)}'
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.getenv('PORT', 8080))) 