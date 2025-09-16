-- SQL script to insert synthetic supplier data for US, Canada, and Mexico
-- This script provides realistic supplier information with proper coordinates for map visualization

-- US Suppliers
INSERT INTO inventory_app.inventory_supplier (supplier_name, contact_person, email, phone, address, city, state, country, county, zipcode, latitude, longitude, website, tax_id, payment_terms, date_created, last_updated) VALUES
('TechSupply Solutions Inc.', 'Sarah Johnson', 'sarah.johnson@techsupply.com', '+1-555-0101', '1234 Industrial Blvd', 'Los Angeles', 'California', 'United States', 'Los Angeles County', '90021', 34.0522, -118.2437, 'https://www.techsupply.com', '12-3456789', 'Net 30', NOW(), NOW()),
('Industrial Equipment Co.', 'Michael Chen', 'mchen@indequip.com', '+1-555-0102', '5678 Manufacturing Way', 'Chicago', 'Illinois', 'United States', 'Cook County', '60601', 41.8781, -87.6298, 'https://www.indequip.com', '98-7654321', 'Net 15', NOW(), NOW()),
('Office Solutions USA', 'Jennifer Martinez', 'j.martinez@officesolutions.com', '+1-555-0103', '9012 Business Park Dr', 'Houston', 'Texas', 'United States', 'Harris County', '77001', 29.7604, -95.3698, 'https://www.officesolutions.com', '45-6789012', 'COD', NOW(), NOW()),
('Safety First Supplies', 'Robert Wilson', 'r.wilson@safetyfirst.com', '+1-555-0104', '3456 Safety Lane', 'Phoenix', 'Arizona', 'United States', 'Maricopa County', '85001', 33.4484, -112.0740, 'https://www.safetyfirst.com', '78-9012345', 'Net 30', NOW(), NOW()),
('Global Logistics Corp', 'Lisa Anderson', 'lisa.anderson@globallog.com', '+1-555-0105', '7890 Distribution Center', 'Miami', 'Florida', 'United States', 'Miami-Dade County', '33101', 25.7617, -80.1918, 'https://www.globallog.com', '23-4567890', 'Net 45', NOW(), NOW()),
('Quality Materials Inc.', 'David Thompson', 'd.thompson@qualitymaterials.com', '+1-555-0106', '2345 Material Way', 'Seattle', 'Washington', 'United States', 'King County', '98101', 47.6062, -122.3321, 'https://www.qualitymaterials.com', '56-7890123', 'Net 30', NOW(), NOW()),
('Electronics Direct', 'Amanda Garcia', 'a.garcia@electronicsdirect.com', '+1-555-0107', '6789 Tech Street', 'Austin', 'Texas', 'United States', 'Travis County', '73301', 30.2672, -97.7431, 'https://www.electronicsdirect.com', '89-0123456', 'Net 15', NOW(), NOW()),
('Construction Supply Co.', 'James Brown', 'j.brown@constructionsupply.com', '+1-555-0108', '4567 Construction Blvd', 'Denver', 'Colorado', 'United States', 'Denver County', '80201', 39.7392, -104.9903, 'https://www.constructionsupply.com', '34-5678901', 'Net 30', NOW(), NOW()),
('Medical Equipment Ltd.', 'Dr. Patricia Lee', 'p.lee@medequip.com', '+1-555-0109', '8901 Medical Center Dr', 'Boston', 'Massachusetts', 'United States', 'Suffolk County', '02101', 42.3601, -71.0589, 'https://www.medequip.com', '67-8901234', 'Net 30', NOW(), NOW()),
('Lab Equipment Solutions', 'Dr. Christopher Davis', 'c.davis@labeq.com', '+1-555-0110', '1234 Research Park', 'San Francisco', 'California', 'United States', 'San Francisco County', '94101', 37.7749, -122.4194, 'https://www.labeq.com', '90-1234567', 'Net 15', NOW(), NOW()),

-- Canada Suppliers
('Northern Supply Co.', 'Jean-Pierre Tremblay', 'jp.tremblay@northernsupply.ca', '+1-514-555-0201', '1234 Rue Industrial', 'Montreal', 'Quebec', 'Canada', 'Montreal', 'H1A 1A1', 45.5017, -73.5673, 'https://www.northernsupply.ca', '123456789RT0001', 'Net 30', NOW(), NOW()),
('Maple Leaf Equipment', 'Sarah MacLeod', 's.macleod@mapleleafequip.ca', '+1-416-555-0202', '5678 Industrial Blvd', 'Toronto', 'Ontario', 'Canada', 'Toronto', 'M5H 2N2', 43.6532, -79.3832, 'https://www.mapleleafequip.ca', '987654321RT0001', 'Net 15', NOW(), NOW()),
('Prairie Materials Inc.', 'Michael O\'Connor', 'm.oconnor@prairiematerials.ca', '+1-403-555-0203', '9012 Materials Way', 'Calgary', 'Alberta', 'Canada', 'Calgary', 'T2P 1J9', 51.0447, -114.0719, 'https://www.prairiematerials.ca', '456789123RT0001', 'Net 30', NOW(), NOW()),
('Pacific Coast Supplies', 'Jennifer Wong', 'j.wong@pacificcoast.ca', '+1-604-555-0204', '3456 Pacific Hwy', 'Vancouver', 'British Columbia', 'Canada', 'Vancouver', 'V6B 1A1', 49.2827, -123.1207, 'https://www.pacificcoast.ca', '789123456RT0001', 'Net 30', NOW(), NOW()),
('Atlantic Equipment Ltd.', 'Robert MacDonald', 'r.macdonald@atlanticequip.ca', '+1-902-555-0205', '7890 Atlantic Ave', 'Halifax', 'Nova Scotia', 'Canada', 'Halifax', 'B3H 3J5', 44.6488, -63.5752, 'https://www.atlanticequip.ca', '234567890RT0001', 'Net 45', NOW(), NOW()),

-- Mexico Suppliers
('Suministros Industriales México', 'Carlos Rodriguez', 'c.rodriguez@suministrosmx.com', '+52-55-5555-0301', 'Av. Industrial 1234', 'Ciudad de México', 'CDMX', 'México', 'Álvaro Obregón', '01200', 19.4326, -99.1332, 'https://www.suministrosmx.com', 'SIR123456789', 'Net 30', NOW(), NOW()),
('Equipos del Norte S.A.', 'Maria Gonzalez', 'm.gonzalez@equiposnorte.com', '+52-81-5555-0302', 'Blvd. Industrial 5678', 'Monterrey', 'Nuevo León', 'México', 'Monterrey', '64000', 25.6866, -100.3161, 'https://www.equiposnorte.com', 'EN987654321', 'Net 15', NOW(), NOW()),
('Proveedores del Pacífico', 'Jose Martinez', 'j.martinez@proveedorespacifico.com', '+52-33-5555-0303', 'Calle Industrial 9012', 'Guadalajara', 'Jalisco', 'México', 'Guadalajara', '44100', 20.6597, -103.3496, 'https://www.proveedorespacifico.com', 'PP456789123', 'Net 30', NOW(), NOW()),
('Materiales del Sureste', 'Ana Lopez', 'a.lopez@materialessureste.com', '+52-999-5555-0304', 'Av. Comercial 3456', 'Mérida', 'Yucatán', 'México', 'Mérida', '97000', 20.9674, -89.5926, 'https://www.materialessureste.com', 'MS789123456', 'Net 30', NOW(), NOW()),
('Suministros Técnicos S.A.', 'Luis Hernandez', 'l.hernandez@suministrostecnicos.com', '+52-222-5555-0305', 'Blvd. Tecnológico 7890', 'Puebla', 'Puebla', 'México', 'Puebla', '72000', 19.0414, -98.2063, 'https://www.suministrostecnicos.com', 'ST234567890', 'Net 15', NOW(), NOW()),
('Equipos Médicos México', 'Dr. Carmen Silva', 'c.silva@equiposmedicos.com', '+52-55-5555-0306', 'Av. Médica 1234', 'Ciudad de México', 'CDMX', 'México', 'Coyoacán', '04000', 19.3441, -99.1626, 'https://www.equiposmedicos.com', 'EM345678901', 'Net 30', NOW(), NOW()),
('Laboratorios del Norte', 'Dr. Fernando Torres', 'f.torres@laboratoriosnorte.com', '+52-81-5555-0307', 'Calle Científica 5678', 'Monterrey', 'Nuevo León', 'México', 'San Pedro Garza García', '66220', 25.6591, -100.4021, 'https://www.laboratoriosnorte.com', 'LN456789012', 'Net 15', NOW(), NOW()),
('Construcciones del Golfo', 'Roberto Vargas', 'r.vargas@construccionesgolfo.com', '+52-81-5555-0308', 'Blvd. Construcción 9012', 'Tampico', 'Tamaulipas', 'México', 'Tampico', '89000', 22.2551, -97.8686, 'https://www.construccionesgolfo.com', 'CG567890123', 'Net 30', NOW(), NOW()),
('Tecnología Avanzada S.A.', 'Patricia Morales', 'p.morales@tecnologiaavanzada.com', '+52-33-5555-0309', 'Av. Tecnológica 3456', 'Guadalajara', 'Jalisco', 'México', 'Zapopan', '45000', 20.7224, -103.3843, 'https://www.tecnologiaavanzada.com', 'TA678901234', 'Net 15', NOW(), NOW()),
('Suministros de Seguridad', 'Miguel Castro', 'm.castro@suministrosseguridad.com', '+52-55-5555-0310', 'Calle Seguridad 7890', 'Ciudad de México', 'CDMX', 'México', 'Iztapalapa', '09000', 19.3574, -99.0671, 'https://www.suministrosseguridad.com', 'SS789012345', 'Net 30', NOW(), NOW());

-- Note: This script assumes the inventory_app schema exists and the inventory_supplier table has been created
-- The coordinates are real coordinates for the cities mentioned
-- Tax IDs follow the format appropriate for each country
-- Phone numbers include country codes
-- All suppliers have realistic business information suitable for map visualization
