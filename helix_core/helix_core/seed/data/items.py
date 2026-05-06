# Helix demo item catalog — 80 SKUs across 6 categories.
# Each entry: (code_suffix, name, uom, standard_rate_mxn, default_supplier, baseline_daily_qty_per_store)

CATEGORIES = {
	"Lácteos": "LAC",
	"Frutas y Verduras": "FYV",
	"Panadería": "PAN",
	"Bebidas": "BEB",
	"Congelados": "CON",
	"Abarrotes": "ABA",
}

ITEMS_BY_CATEGORY = {
	"Lácteos": [
		("001", "Lala leche entera 1L", "Litre", 24.50, "Grupo Lala", 48),
		("002", "Lala leche deslactosada 1L", "Litre", 28.00, "Grupo Lala", 22),
		("003", "Yoplait yogurt natural 900g", "Nos", 42.00, "Grupo Lala", 14),
		("004", "Alpura leche entera 1L", "Litre", 25.00, "Sigma Alimentos", 30),
		("005", "Nochebuena crema 250g", "Nos", 22.00, "Sigma Alimentos", 18),
		("006", "Philadelphia queso crema 190g", "Nos", 38.00, "Sigma Alimentos", 16),
		("007", "Oaxaca queso 250g", "Nos", 65.00, "Sigma Alimentos", 12),
		("008", "Lala media crema 250g", "Nos", 18.00, "Grupo Lala", 24),
		("009", "Danone yogurt griego 150g", "Nos", 18.50, "Sigma Alimentos", 26),
		("010", "Chipilo queso de cabra 200g", "Nos", 95.00, "Productores Locales del Norte", 5),
		("011", "Lala mantequilla con sal 200g", "Nos", 45.00, "Grupo Lala", 11),
		("012", "Yoplait yogurt fresa 1L", "Litre", 38.00, "Grupo Lala", 18),
		("013", "Lala queso panela 400g", "Nos", 75.00, "Grupo Lala", 9),
	],
	"Frutas y Verduras": [
		("001", "Tomate Roma kg", "Kg", 22.00, "Productores Locales del Norte", 90),
		("002", "Aguacate Hass kg", "Kg", 65.00, "Productores Locales del Norte", 55),
		("003", "Plátano Tabasco kg", "Kg", 18.00, "Comercial Mexicana", 70),
		("004", "Manzana Red Delicious kg", "Kg", 38.00, "Comercial Mexicana", 32),
		("005", "Naranja Valencia kg", "Kg", 16.00, "Productores Locales del Norte", 45),
		("006", "Cebolla blanca kg", "Kg", 20.00, "Productores Locales del Norte", 40),
		("007", "Limón sin semilla kg", "Kg", 35.00, "Productores Locales del Norte", 38),
		("008", "Zanahoria kg", "Kg", 14.00, "Productores Locales del Norte", 28),
		("009", "Papa blanca kg", "Kg", 25.00, "Comercial Mexicana", 50),
		("010", "Lechuga romana", "Nos", 18.00, "Productores Locales del Norte", 35),
		("011", "Chile jalapeño kg", "Kg", 28.00, "Productores Locales del Norte", 22),
		("012", "Pepino kg", "Kg", 16.00, "Productores Locales del Norte", 24),
		("013", "Espinaca manojo", "Nos", 22.00, "Productores Locales del Norte", 18),
	],
	"Panadería": [
		("001", "Bolillo", "Nos", 4.50, "Bimbo", 220),
		("002", "Pan Bimbo blanco grande 680g", "Nos", 48.00, "Bimbo", 28),
		("003", "Pan Bimbo integral 680g", "Nos", 52.00, "Bimbo", 22),
		("004", "Telera", "Nos", 5.00, "Bimbo", 140),
		("005", "Concha de chocolate", "Nos", 8.00, "Marinela", 55),
		("006", "Concha de vainilla", "Nos", 8.00, "Marinela", 55),
		("007", "Mantecadas Bimbo 4pz", "Nos", 28.00, "Bimbo", 18),
		("008", "Donas Bimbo glaseadas 4pz", "Nos", 32.00, "Bimbo", 16),
		("009", "Pingüinos Marinela 4pz", "Nos", 22.00, "Marinela", 24),
		("010", "Gansito Marinela 6pz", "Nos", 32.00, "Marinela", 20),
		("011", "Tortillas de harina La Banderita 10pz", "Nos", 22.00, "Bimbo", 35),
		("012", "Pan árabe Bimbo 6pz", "Nos", 28.00, "Bimbo", 14),
		("013", "Roles de canela 4pz", "Nos", 35.00, "Marinela", 12),
	],
	"Bebidas": [
		("001", "Coca-Cola 600ml", "Nos", 18.00, "Coca-Cola FEMSA", 70),
		("002", "Coca-Cola 2L", "Nos", 32.00, "Coca-Cola FEMSA", 35),
		("003", "Coca-Cola lata 355ml", "Nos", 14.00, "Coca-Cola FEMSA", 50),
		("004", "Sprite 600ml", "Nos", 17.00, "Coca-Cola FEMSA", 28),
		("005", "Fanta naranja 600ml", "Nos", 17.00, "Coca-Cola FEMSA", 24),
		("006", "Agua Ciel 1.5L", "Nos", 14.00, "Coca-Cola FEMSA", 90),
		("007", "Jumex mango 1L", "Nos", 22.00, "FEMSA", 18),
		("008", "Boing tamarindo 250ml", "Nos", 11.00, "FEMSA", 26),
		("009", "Topo Chico mineral 500ml", "Nos", 14.00, "Coca-Cola FEMSA", 32),
		("010", "Jarritos toronja 500ml", "Nos", 16.00, "FEMSA", 22),
		("011", "Powerade azul 600ml", "Nos", 22.00, "Coca-Cola FEMSA", 18),
		("012", "Red Bull 250ml", "Nos", 38.00, "FEMSA", 14),
		("013", "Té Lipton durazno 500ml", "Nos", 18.00, "FEMSA", 16),
		("014", "Nescafé Clásico soluble 100g", "Nos", 78.00, "FEMSA", 12),
	],
	"Congelados": [
		("001", "Helado Häagen-Dazs vainilla 473ml", "Nos", 165.00, "Häagen-Dazs MX", 4),
		("002", "Helado Häagen-Dazs chocolate 473ml", "Nos", 165.00, "Häagen-Dazs MX", 4),
		("003", "Helado Holanda mantecado 1L", "Nos", 95.00, "Sigma Alimentos", 14),
		("004", "Pizza congelada Tombstone pepperoni", "Nos", 110.00, "Comercial Mexicana", 9),
		("005", "Nuggets de pollo Pilgrim's 800g", "Nos", 145.00, "Comercial Mexicana", 12),
		("006", "Hamburguesas Bachoco 12pz", "Nos", 165.00, "Comercial Mexicana", 7),
		("007", "Verduras mixtas Birds Eye 500g", "Nos", 48.00, "Comercial Mexicana", 16),
		("008", "Bacalao congelado 500g", "Kg", 195.00, "Comercial Mexicana", 3),
		("009", "Helado La Lechera fresa 1L", "Nos", 92.00, "Sigma Alimentos", 11),
		("010", "Pollo entero congelado kg", "Kg", 78.00, "Comercial Mexicana", 22),
		("011", "Camarón mediano 500g", "Kg", 220.00, "Comercial Mexicana", 5),
		("012", "Tamales congelados 6pz", "Nos", 95.00, "Productores Locales del Norte", 8),
		("013", "Paletas Holanda 6pz", "Nos", 38.00, "Sigma Alimentos", 18),
	],
	"Abarrotes": [
		("001", "Arroz Verde Valle 1kg", "Kg", 32.00, "Verde Valle", 18),
		("002", "Frijol pinto Verde Valle 1kg", "Kg", 38.00, "Verde Valle", 16),
		("003", "Aceite Capullo 1L", "Litre", 65.00, "Verde Valle", 14),
		("004", "Sal La Fina 1kg", "Kg", 12.00, "Verde Valle", 9),
		("005", "Azúcar morena Zulka 1kg", "Kg", 28.00, "Verde Valle", 12),
		("006", "Pasta Barilla espagueti 200g", "Nos", 18.00, "Comercial Mexicana", 22),
		("007", "Atún Dolores en aceite 174g", "Nos", 22.00, "FEMSA", 28),
		("008", "Frijol La Costeña refrito 580g", "Nos", 26.00, "Comercial Mexicana", 20),
		("009", "Salsa Valentina 370ml", "Nos", 32.00, "FEMSA", 16),
		("010", "Mayonesa Hellmann's 470g", "Nos", 52.00, "FEMSA", 11),
		("011", "Café Nescafé Decaf 100g", "Nos", 88.00, "FEMSA", 6),
		("012", "Galletas Marías Gamesa 290g", "Nos", 22.00, "Bimbo", 24),
		("013", "Cereal Zucaritas Kellogg's 500g", "Nos", 78.00, "Comercial Mexicana", 8),
		("014", "Avena Quaker 400g", "Nos", 38.00, "Comercial Mexicana", 14),
	],
}

WAREHOUSES = [
	"Casias Foods – Centro",
	"Casias Foods – San Pedro",
	"Casias Foods – Cumbres",
	"Casias Foods – Apodaca",
	"Casias Foods – Santa Catarina",
]

# Per-store demand multiplier (San Pedro is highest-volume store, Apodaca smallest).
WAREHOUSE_FACTORS = {
	"Casias Foods – Centro": 1.00,
	"Casias Foods – San Pedro": 1.25,
	"Casias Foods – Cumbres": 1.05,
	"Casias Foods – Apodaca": 0.80,
	"Casias Foods – Santa Catarina": 0.95,
}

SUPPLIERS = [
	"Grupo Lala",
	"Bimbo",
	"FEMSA",
	"Sigma Alimentos",
	"Comercial Mexicana",
	"Productores Locales del Norte",
	"Marinela",
	"Coca-Cola FEMSA",
	"Häagen-Dazs MX",
	"Verde Valle",
]

# Items where promo windows apply (Bebidas — used to drive the demo's "model saw the spike" moment).
PROMO_ITEMS = [
	"ITM-BEB-001",  # Coca-Cola 600ml
	"ITM-BEB-002",  # Coca-Cola 2L
	"ITM-BEB-006",  # Agua Ciel 1.5L
	"ITM-BEB-011",  # Powerade azul 600ml
]

# Items engineered to show <3 days of cover (the §5.1 KPI "Items at Stockout Risk").
STOCKOUT_RISK_ITEMS = [
	"ITM-LAC-001",  # Lala leche entera 1L
	"ITM-PAN-001",  # Bolillo
	"ITM-FYV-001",  # Tomate Roma kg
	"ITM-FYV-002",  # Aguacate Hass kg
	"ITM-BEB-001",  # Coca-Cola 600ml
	"ITM-LAC-007",  # Oaxaca queso 250g
	"ITM-PAN-002",  # Pan Bimbo blanco grande
]

# Items engineered to show 25+ days of cover (the over-stocked counter-example).
OVERSTOCK_ITEMS = [
	"ITM-CON-001",  # Häagen-Dazs vainilla
	"ITM-ABA-013",  # Cereal Zucaritas
	"ITM-CON-008",  # Bacalao congelado
]

COMPANY_NAME = "Casias Foods"
COMPANY_ABBR = "CF"
PARENT_WAREHOUSE = f"All Warehouses - {COMPANY_ABBR}"
