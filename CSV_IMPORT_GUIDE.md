# 📊 CSV Import Guide for Sample Data

## 🎯 Overview

I've created clean CSV files that you can easily import into your PostgreSQL database. This approach is much more reliable than SQL scripts and works with any PostgreSQL client.

## 📁 Files Created

- **`products.csv`** - 29 products across 6 categories
- **`customers.csv`** - 10 sample customers
- **`pickup_slots.csv`** - 45 pickup time slots (5 days × 9 hours)

## 🚀 Import Methods

### Method 1: Using pgAdmin (Recommended)

1. **Open pgAdmin** and connect to your database
2. **Navigate to your schema** (look for `ordering_app_schema_*`)
3. **For each table**, right-click → **Import/Export Data**
4. **Import settings**:
   - Format: `CSV`
   - Filename: Browse to select the CSV file
   - Header: `Yes` (first row contains column names)
   - Delimiter: `,` (comma)
   - Quote: `"` (double quote)
   - Encoding: `UTF8`

**Import Order (Important!):**
1. First: `customers.csv` → `customers` table
2. Second: `products.csv` → `products` table  
3. Third: `pickup_slots.csv` → `pickup_slots` table

### Method 2: Using DataGrip/IntelliJ

1. **Connect to your database**
2. **Right-click on each table** → **Import Data from File**
3. **Select the corresponding CSV file**
4. **Map columns** (should auto-map correctly)
5. **Import data**

### Method 3: Using psql Command Line

```bash
# Connect to your database
psql -h your_host -d your_database -U your_user

# Import each table (replace schema_name with your actual schema)
\copy your_schema_name.customers FROM 'customers.csv' DELIMITER ',' CSV HEADER;
\copy your_schema_name.products FROM 'products.csv' DELIMITER ',' CSV HEADER;
\copy your_schema_name.pickup_slots FROM 'pickup_slots.csv' DELIMITER ',' CSV HEADER;
```

### Method 4: Using DBeaver

1. **Right-click on the table** → **Import Data**
2. **Select CSV file**
3. **Configure settings**:
   - Header: `Yes`
   - Delimiter: `,`
   - Text qualifier: `"`
4. **Map columns** and **Execute**

## 🔍 Finding Your Schema Name

If you're not sure of your schema name, run this query first:

```sql
SELECT schema_name 
FROM information_schema.schemata 
WHERE schema_name LIKE '%ordering_app%' 
   OR schema_name LIKE '%schema%';
```

Look for something like: `ordering_app_schema_youruser`

## ✅ Verification Steps

After importing all files:

1. **Check product count**:
   ```sql
   SELECT COUNT(*) FROM your_schema.products;
   -- Should return: 29
   ```

2. **Check categories**:
   ```sql
   SELECT category, COUNT(*) 
   FROM your_schema.products 
   GROUP BY category;
   ```

3. **Refresh your app** - you should see "29 products available"

## 📋 What You'll Get

### 🛍️ Products (29 total):
- **Electronics** (5): Headphones, Phone Stand, Cables, Power Bank, Mouse
- **Office Supplies** (5): Chair, Organizer, Keyboard/Mouse, Lamp, Standing Desk  
- **Home & Garden** (5): Plants, Mugs, Candles, Pillows, Diffuser
- **Books & Media** (4): Programming Book, Notebooks, Art Kit, Journal
- **Sports & Outdoors** (5): Yoga Mat, Water Bottle, Resistance Bands, Foam Roller, Earbuds
- **Food & Beverages** (5): Tea Collection, Coffee, Chocolate, Honey, Herbal Tea

### 👥 Customers (10):
- Realistic names and contact information
- Use these emails to test the "My Orders" feature

### 📅 Pickup Slots (45):
- December 16-20, 2024 (update dates if needed)
- 9 AM to 5 PM daily
- 10 order capacity per slot

## 🔧 Troubleshooting

### ❌ "Column doesn't exist" error:
- Make sure your app has run at least once to create the tables
- Check that you're importing to the correct schema

### ❌ "Permission denied" error:
- Use the same database credentials as your app
- Ensure your user has INSERT permissions

### ❌ Date format issues:
- The pickup_slots.csv uses format: `YYYY-MM-DD HH:MM:SS`
- Update the dates in pickup_slots.csv to future dates if needed

### ❌ Import fails on specific rows:
- Check for special characters in CSV
- Ensure CSV encoding is UTF-8
- Try importing smaller batches

## 🎨 Customization

### Update Product Images:
- Replace image URLs in `products.csv` with your own images
- Use format: `https://your-domain.com/images/product.jpg`

### Modify Prices/Stock:
- Edit the `price` and `stock_quantity` columns in `products.csv`
- Keep `reserved_quantity` as 0 for new products

### Update Pickup Dates:
- Edit `pickup_slots.csv` to use current/future dates
- Keep the time format: `YYYY-MM-DD HH:MM:SS`

## 🎉 Success!

After successful import:
- **Refresh your browser**
- **See 29 products** instead of "0 products available"  
- **Test shopping cart** functionality
- **Try the complete checkout flow**
- **Use sample emails** to test order history

---

**🎊 Your Online Ordering & Click-and-Collect System is now ready for testing!**
