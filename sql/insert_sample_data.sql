-- Insert sample data for the inventory app
-- This script populates the database with sample products for demonstration

-- Insert sample products
INSERT INTO {schema_name}.products (name, description, category, price, stock_quantity, image_url) VALUES
('Leather Journal', 'Handcrafted leather-bound journal with 200 pages', 'Stationery', 24.99, 15, 'https://images.unsplash.com/photo-1544716278-e2247dc0e21c?w=400'),
('Portable Power Bank', '10000mAh portable charger with fast charging', 'Electronics', 39.99, 8, 'https://images.unsplash.com/photo-1609592094731-8c1f5a9e0eb3?w=400'),
('USB-C Cable 6ft', 'High-speed USB-C to USB-C cable', 'Electronics', 12.99, 25, 'https://images.unsplash.com/photo-1558618047-3c8c76ca7d13?w=400'),
('Honey Gift Set', 'Artisanal honey collection with 3 varieties', 'Food & Beverages', 18.99, 12, 'https://images.unsplash.com/photo-1587049016823-c90bb28637b6?w=400'),
('Ceramic Coffee Mug Set', 'Set of 2 hand-painted ceramic mugs', 'Home & Kitchen', 22.99, 6, 'https://images.unsplash.com/photo-1514228742587-6b1558fcf93a?w=400'),
('Scented Candle Collection', 'Set of 3 soy candles with natural scents', 'Home & Kitchen', 29.99, 10, 'https://images.unsplash.com/photo-1602874801006-47c1c6c54a9b?w=400'),
('Wireless Bluetooth Headphones', 'Noise-cancelling over-ear headphones', 'Electronics', 89.99, 4, 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400'),
('Organic Tea Sampler', 'Collection of 12 premium organic teas', 'Food & Beverages', 16.99, 20, 'https://images.unsplash.com/photo-1556679343-c7306c1976bc?w=400'),
('Bamboo Cutting Board', 'Eco-friendly bamboo cutting board with juice groove', 'Home & Kitchen', 19.99, 7, 'https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=400'),
('Stainless Steel Water Bottle', 'Insulated 32oz water bottle with leak-proof lid', 'Sports & Outdoors', 24.99, 14, 'https://images.unsplash.com/photo-1602143407151-7111542de6e8?w=400')
ON CONFLICT DO NOTHING;
