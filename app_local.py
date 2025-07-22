from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, Response
import sqlite3
import os
import csv
import io
from datetime import datetime
from contextlib import contextmanager
from werkzeug.utils import secure_filename

# Database setup for local development
DATABASE = 'inventory.db'

# CSV upload configuration
ALLOWED_EXTENSIONS = {'csv'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB max file size

def allowed_file(filename):
    """Check if uploaded file is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@contextmanager
def get_db():
    """Get database connection with context manager."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_database():
    """Initialize database schema and table."""
    try:
        with get_db() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS inventory_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item_name TEXT NOT NULL,
                    description TEXT,
                    category TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    unit_price REAL NOT NULL,
                    supplier TEXT,
                    location TEXT,
                    minimum_stock INTEGER,
                    date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
            return True
    except Exception as e:
        print(f"Database initialization error: {e}")
        return False

def add_inventory_item(item_name, description, category, quantity, unit_price, supplier=None, location=None, minimum_stock=None):
    """Add a new inventory item."""
    try:
        with get_db() as conn:
            now = datetime.now().isoformat()
            conn.execute('''
                INSERT INTO inventory_items 
                (item_name, description, category, quantity, unit_price, supplier, location, minimum_stock, date_added, last_updated) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (item_name, description, category, quantity, unit_price, supplier, location, minimum_stock, now, now))
            conn.commit()
            return True
    except Exception as e:
        print(f"Add inventory item error: {e}")
        return False

def add_inventory_items_bulk(items_data):
    """Add multiple inventory items in bulk."""
    try:
        with get_db() as conn:
            # Execute bulk insert
            conn.executemany('''
                INSERT INTO inventory_items 
                (item_name, description, category, quantity, unit_price, supplier, location, minimum_stock, date_added, last_updated) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', items_data)
            conn.commit()
            return True, len(items_data)
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
    
    now = datetime.now().isoformat()
    return (item_name, description, category, quantity, unit_price, supplier, location, minimum_stock, now, now), []

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
        with get_db() as conn:
            cursor = conn.execute('''
                SELECT id, item_name, description, category, quantity, unit_price, supplier, location, minimum_stock, date_added, last_updated 
                FROM inventory_items ORDER BY item_name ASC
            ''')
            items = cursor.fetchall()
            # Convert timestamp strings to datetime objects
            result = []
            for item in items:
                item_dict = dict(item)
                if item_dict['date_added']:
                    item_dict['date_added'] = datetime.fromisoformat(item_dict['date_added'])
                if item_dict['last_updated']:
                    item_dict['last_updated'] = datetime.fromisoformat(item_dict['last_updated'])
                # Convert back to tuple format for template compatibility
                result.append((
                    item_dict['id'], item_dict['item_name'], item_dict['description'],
                    item_dict['category'], item_dict['quantity'], item_dict['unit_price'],
                    item_dict['supplier'], item_dict['location'], item_dict['minimum_stock'],
                    item_dict['date_added'], item_dict['last_updated']
                ))
            return result
    except Exception as e:
        print(f"Get inventory items error: {e}")
        return []

def get_inventory_item(item_id):
    """Get a specific inventory item by ID."""
    try:
        with get_db() as conn:
            cursor = conn.execute('''
                SELECT id, item_name, description, category, quantity, unit_price, supplier, location, minimum_stock, date_added, last_updated 
                FROM inventory_items WHERE id = ?
            ''', (item_id,))
            item = cursor.fetchone()
            if item:
                item_dict = dict(item)
                if item_dict['date_added']:
                    item_dict['date_added'] = datetime.fromisoformat(item_dict['date_added'])
                if item_dict['last_updated']:
                    item_dict['last_updated'] = datetime.fromisoformat(item_dict['last_updated'])
                # Convert back to tuple format for template compatibility
                return (
                    item_dict['id'], item_dict['item_name'], item_dict['description'],
                    item_dict['category'], item_dict['quantity'], item_dict['unit_price'],
                    item_dict['supplier'], item_dict['location'], item_dict['minimum_stock'],
                    item_dict['date_added'], item_dict['last_updated']
                )
            return None
    except Exception as e:
        print(f"Get inventory item error: {e}")
        return None

def update_inventory_item(item_id, item_name, description, category, quantity, unit_price, supplier=None, location=None, minimum_stock=None):
    """Update an existing inventory item."""
    try:
        with get_db() as conn:
            now = datetime.now().isoformat()
            conn.execute('''
                UPDATE inventory_items 
                SET item_name = ?, description = ?, category = ?, quantity = ?, unit_price = ?, 
                    supplier = ?, location = ?, minimum_stock = ?, last_updated = ?
                WHERE id = ?
            ''', (item_name, description, category, quantity, unit_price, supplier, location, minimum_stock, now, item_id))
            conn.commit()
            return True
    except Exception as e:
        print(f"Update inventory item error: {e}")
        return False

def delete_inventory_item(item_id):
    """Delete an inventory item."""
    try:
        with get_db() as conn:
            conn.execute("DELETE FROM inventory_items WHERE id = ?", (item_id,))
            conn.commit()
            return True
    except Exception as e:
        print(f"Delete inventory item error: {e}")
        return False

def get_low_stock_items():
    """Get items with quantity at or below minimum stock level."""
    try:
        with get_db() as conn:
            cursor = conn.execute('''
                SELECT id, item_name, description, category, quantity, unit_price, supplier, location, minimum_stock, date_added, last_updated 
                FROM inventory_items 
                WHERE minimum_stock IS NOT NULL AND quantity <= minimum_stock
                ORDER BY (quantity - minimum_stock) ASC
            ''')
            items = cursor.fetchall()
            # Convert timestamp strings to datetime objects
            result = []
            for item in items:
                item_dict = dict(item)
                if item_dict['date_added']:
                    item_dict['date_added'] = datetime.fromisoformat(item_dict['date_added'])
                if item_dict['last_updated']:
                    item_dict['last_updated'] = datetime.fromisoformat(item_dict['last_updated'])
                # Convert back to tuple format for template compatibility
                result.append((
                    item_dict['id'], item_dict['item_name'], item_dict['description'],
                    item_dict['category'], item_dict['quantity'], item_dict['unit_price'],
                    item_dict['supplier'], item_dict['location'], item_dict['minimum_stock'],
                    item_dict['date_added'], item_dict['last_updated']
                ))
            return result
    except Exception as e:
        print(f"Get low stock items error: {e}")
        return []

def add_sample_data():
    """Add sample data for demonstration."""
    sample_items = [
        ("Laptop - Dell XPS 13", "13-inch ultrabook with Intel i7 processor", "Electronics", 5, 1299.99, "Dell Inc.", "Office Storage Room", 2),
        ("Office Chair - Ergonomic", "Adjustable height office chair with lumbar support", "Furniture", 12, 299.99, "Office Depot", "Warehouse A", 5),
        ("Wireless Mouse", "Bluetooth wireless mouse with optical sensor", "Electronics", 3, 49.99, "Logitech", "IT Storage", 10),
        ("Safety Helmet", "OSHA approved construction safety helmet", "Safety Equipment", 8, 29.99, "SafetyFirst Corp", "Safety Locker", 15),
        ("Printer Paper - A4", "500 sheets premium white printing paper", "Office Supplies", 2, 12.99, "Staples", "Supply Closet", 20),
        ("Tablet - iPad Air", "10.9-inch iPad Air with 64GB storage", "Electronics", 0, 599.99, "Apple Inc.", "Tech Lab", 3),
        ("Desk Lamp", "LED desk lamp with adjustable brightness", "Furniture", 1, 79.99, "IKEA", "Office Storage", 5),
    ]
    
    for item in sample_items:
        add_inventory_item(*item)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'dev-secret-key-for-local-testing'
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Initialize database
if not init_database():
    print("Failed to initialize database")
else:
    print("✅ Database initialized successfully!")
    # Check if we need to add sample data
    items = get_inventory_items()
    if not items:
        print("📦 Adding sample data...")
        add_sample_data()
        print("✅ Sample data added!")

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

@app.route('/api/items')
def api_items():
    """API endpoint to get all items as JSON."""
    items = get_inventory_items()
    items_list = []
    for item in items:
        items_list.append({
            'id': item['id'],
            'item_name': item['item_name'],
            'description': item['description'],
            'category': item['category'],
            'quantity': item['quantity'],
            'unit_price': item['unit_price'],
            'supplier': item['supplier'],
            'location': item['location'],
            'minimum_stock': item['minimum_stock'],
            'date_added': item['date_added'],
            'last_updated': item['last_updated']
        })
    return jsonify(items_list)

if __name__ == '__main__':
    print("\n🚀 Starting Equipment Inventory Management System with CSV Upload")
    print("📱 Open your browser and go to: http://127.0.0.1:5000")
    print("📊 CSV Upload feature available in the navigation menu")
    print("🛑 Press CTRL+C to stop the server\n")
    app.run(debug=True, host='0.0.0.0', port=5000) 