"""
Flavor configuration system for multi-industry inventory management.
Defines industry-specific fields, categories, and UI customizations.
"""

# Industry flavor configurations
FLAVOR_CONFIGS = {
    'mfg': {
        'name': 'Manufacturing',
        'icon': 'fas fa-industry',
        'color': '#007bff',  # Blue
        'description': 'Manufacturing and Industrial Equipment',
        'categories': [
            'Machinery',
            'Tools',
            'Raw Materials',
            'Safety Equipment',
            'Maintenance Parts',
            'Quality Control Equipment',
            'Production Line Equipment'
        ],
        'fields': {
            'supplier': {'label': 'Vendor/Supplier', 'required': False},
            'location': {'label': 'Plant/Line Location', 'required': False},
            'minimum_stock': {'label': 'Safety Stock Level', 'required': False},
            'description': {'label': 'Equipment Specifications', 'required': False},
            'serial_number': {'label': 'Serial/Model Number', 'required': False},
            'maintenance_schedule': {'label': 'Maintenance Schedule', 'required': False}
        },
        'unit_labels': {
            'quantity': 'Units/Pieces',
            'unit_price': 'Cost per Unit ($)'
        },
        'sample_data': [
            ("CNC Milling Machine", "High-precision CNC mill for aluminum parts", "Machinery", 2, 85000.00, "Haas Automation", "Production Line A", 1),
            ("Safety Goggles", "ANSI Z87.1 certified safety eyewear", "Safety Equipment", 50, 12.99, "3M Industrial", "Safety Storage", 20),
            ("Torque Wrench Set", "Calibrated torque wrenches 10-150 ft-lbs", "Tools", 8, 299.99, "Snap-on Tools", "Tool Crib", 3),
            ("Steel Rod - 1/2 inch", "Cold rolled steel rod, 20 ft lengths", "Raw Materials", 100, 15.50, "Steel Supply Co", "Materials Warehouse", 25),
            ("Hydraulic Press", "50-ton hydraulic press for forming", "Machinery", 1, 12500.00, "Enerpac Corp", "Press Shop", 1)
        ]
    },
    'retail': {
        'name': 'Retail',
        'icon': 'fas fa-store',
        'color': '#28a745',  # Green
        'description': 'Retail Store Inventory Management',
        'categories': [
            'Electronics',
            'Clothing & Apparel',
            'Home & Garden',
            'Sports & Recreation',
            'Books & Media',
            'Health & Beauty',
            'Food & Beverages',
            'Toys & Games'
        ],
        'fields': {
            'supplier': {'label': 'Brand/Supplier', 'required': False},
            'location': {'label': 'Store Location/Section', 'required': False},
            'minimum_stock': {'label': 'Reorder Point', 'required': False},
            'description': {'label': 'Product Description', 'required': False},
            'sku': {'label': 'SKU/Barcode', 'required': False},
            'retail_price': {'label': 'Retail Price ($)', 'required': False}
        },
        'unit_labels': {
            'quantity': 'Items in Stock',
            'unit_price': 'Cost per Item ($)'
        },
        'sample_data': [
            ("iPhone 15 Pro", "Latest Apple smartphone with 256GB storage", "Electronics", 15, 899.99, "Apple Inc.", "Electronics Section", 5),
            ("Levi's 501 Jeans", "Classic straight-leg denim jeans, size 32x34", "Clothing & Apparel", 25, 59.99, "Levi Strauss", "Men's Clothing", 10),
            ("Garden Hose", "50ft expandable garden hose with spray nozzle", "Home & Garden", 12, 24.99, "Gardena", "Outdoor Section", 6),
            ("Nike Running Shoes", "Air Max series athletic shoes, size 10", "Sports & Recreation", 8, 129.99, "Nike Inc.", "Footwear", 4),
            ("Coffee Maker", "12-cup programmable coffee maker", "Home & Garden", 6, 79.99, "Cuisinart", "Kitchen Appliances", 3)
        ]
    },
    'telecom': {
        'name': 'Telecommunications',
        'icon': 'fas fa-broadcast-tower',
        'color': '#6f42c1',  # Purple
        'description': 'Telecom Equipment and Infrastructure',
        'categories': [
            'Network Equipment',
            'Fiber Optic Components',
            'Wireless Equipment',
            'Testing Equipment',
            'Power Systems',
            'Installation Tools',
            'Cable Management',
            'Customer Premises Equipment'
        ],
        'fields': {
            'supplier': {'label': 'Manufacturer', 'required': False},
            'location': {'label': 'Site/Facility', 'required': False},
            'minimum_stock': {'label': 'Critical Stock Level', 'required': False},
            'description': {'label': 'Technical Specifications', 'required': False},
            'part_number': {'label': 'Part Number', 'required': False},
            'warranty_period': {'label': 'Warranty (months)', 'required': False}
        },
        'unit_labels': {
            'quantity': 'Units Available',
            'unit_price': 'Unit Cost ($)'
        },
        'sample_data': [
            ("5G Base Station", "Outdoor 5G mmWave base station unit", "Wireless Equipment", 3, 45000.00, "Ericsson", "Cell Tower Site A", 1),
            ("Fiber Optic Cable", "Single-mode fiber 144-strand, per 1000ft", "Fiber Optic Components", 20, 850.00, "Corning", "Fiber Warehouse", 5),
            ("Network Switch", "48-port Gigabit managed switch", "Network Equipment", 12, 1299.99, "Cisco Systems", "Data Center", 4),
            ("OTDR Tester", "Optical time-domain reflectometer for fiber testing", "Testing Equipment", 2, 8500.00, "JDSU/Viavi", "Test Equipment Room", 1),
            ("Power Amplifier", "RF power amplifier 800-2700 MHz", "Wireless Equipment", 8, 2500.00, "Keysight", "RF Equipment Storage", 3)
        ]
    }
}

def get_flavor_config(flavor_key):
    """Get configuration for a specific flavor."""
    return FLAVOR_CONFIGS.get(flavor_key, FLAVOR_CONFIGS['mfg'])

def get_available_flavors():
    """Get list of all available flavors."""
    return [(key, config['name']) for key, config in FLAVOR_CONFIGS.items()]

def get_categories_for_flavor(flavor_key):
    """Get categories for a specific flavor."""
    config = get_flavor_config(flavor_key)
    return config['categories']

def get_fields_for_flavor(flavor_key):
    """Get field configuration for a specific flavor."""
    config = get_flavor_config(flavor_key)
    return config['fields']

def get_unit_labels_for_flavor(flavor_key):
    """Get unit labels for a specific flavor."""
    config = get_flavor_config(flavor_key)
    return config['unit_labels']

def get_sample_data_for_flavor(flavor_key):
    """Get sample data for a specific flavor."""
    config = get_flavor_config(flavor_key)
    return config['sample_data']

def validate_flavor(flavor_key):
    """Validate if a flavor key is valid."""
    return flavor_key in FLAVOR_CONFIGS

def get_default_flavor():
    """Get the default flavor."""
    return 'mfg'
