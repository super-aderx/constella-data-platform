"""Maple Corner Grocery: the backend's sample catalog (Constellate backend/app/sample_data.py).

Same 30 products, one-level categories and prices, five themes and four unthemed products.
No planted bridges. SKUs are MC-0001 … in the backend's order.
"""

from generator.tenants import CategorySpec, ProductSpec, TenantSpec

C = CategorySpec
P = ProductSpec

CATEGORIES = (
    C("dairy", "Dairy"),
    C("bakery", "Bakery"),
    C("produce", "Produce"),
    C("beverages", "Beverages"),
    C("snacks", "Snacks"),
    C("pantry", "Pantry"),
    C("household", "Household", renamed_from=(90, "Home care")),
)

PRODUCTS = (
    P("0001", "Whole Milk", "dairy", "Maple Dairy", "carton", "1 gal", 249, "breakfast", 0.55),
    P("0002", "Greek Yogurt", "dairy", "Maple Dairy", "tub", "32 oz", 499, "breakfast", 0.35),
    P("0003", "Sourdough Bread", "bakery", "Corner Oven", "loaf", "24 oz", 549, "breakfast", 0.4),
    P("0004", "Bananas", "produce", "Maple Corner", "lb", "1 lb", 129, "breakfast", 0.5),
    P("0005", "Ground Coffee", "beverages", "Cascade Roast", "bag", "12 oz", 999, "breakfast",
      0.3, earlier_price=(180, 949)),
    P("0006", "Granola", "pantry", "Trailhead", "bag", "16 oz", 649, "breakfast", 0.25),
    P("0007", "All-Purpose Flour", "pantry", "Corner Oven", "bag", "5 lb", 399, "baking", 0.6),
    P("0008", "Cane Sugar", "pantry", "Maple Corner", "bag", "4 lb", 349, "baking", 0.5),
    P("0009", "Eggs (12)", "dairy", "Maple Dairy", "carton", "12 ct", 429, "baking", 0.55,
      earlier_price=(240, 379)),
    P("0010", "Unsalted Butter", "dairy", "Maple Dairy", "pack", "1 lb", 599, "baking", 0.5),
    P("0011", "Baking Soda", "pantry", "Maple Corner", "box", "16 oz", 149, "baking", 0.25),
    P("0012", "Chocolate Chips", "snacks", "Trailhead", "bag", "12 oz", 449, "baking", 0.4),
    P("0013", "Tortilla Chips", "snacks", "Canyon Crunch", "bag", "13 oz", 399, "party", 0.6),
    P("0014", "Salsa", "pantry", "Canyon Crunch", "jar", "16 oz", 449, "party", 0.45),
    P("0015", "Cola 6-Pack", "beverages", "Fizzwell", "pack", "6 × 12 oz", 699, "party", 0.4),
    P("0016", "Guacamole", "produce", "Canyon Crunch", "tub", "8 oz", 549, "party", 0.3),
    P("0017", "Paper Plates", "household", "Maple Corner", "pack", "50 ct", 499, "party", 0.25),
    P("0018", "Spaghetti", "pantry", "Via Roma", "box", "16 oz", 199, "pasta", 0.6),
    P("0019", "Marinara Sauce", "pantry", "Via Roma", "jar", "24 oz", 399, "pasta", 0.55),
    P("0020", "Parmesan", "dairy", "Via Roma", "wedge", "8 oz", 699, "pasta", 0.35),
    P("0021", "Garlic", "produce", "Maple Corner", "bulb", "3 ct", 99, "pasta", 0.35),
    P("0022", "Basil", "produce", "Maple Corner", "bunch", "1 oz", 249, "pasta", 0.2),
    P("0023", "Dish Soap", "household", "Brightway", "bottle", "24 oz", 349, "cleaning", 0.5),
    P("0024", "Sponges", "household", "Brightway", "pack", "6 ct", 299, "cleaning", 0.4),
    P("0025", "Paper Towels", "household", "Maple Corner", "pack", "6 rolls", 799, "cleaning",
      0.45),
    P("0026", "Trash Bags", "household", "Brightway", "box", "40 ct", 899, "cleaning", 0.35),
    P("0027", "Apples", "produce", "Maple Corner", "lb", "1 lb", 399, None, addon_p=0.05),
    P("0028", "Sparkling Water", "beverages", "Fizzwell", "pack", "8 × 12 oz", 499, None,
      addon_p=0.04),
    P("0029", "Peanut Butter", "pantry", "Trailhead", "jar", "16 oz", 379, None, addon_p=0.03,
      renamed_from=(200, "Creamy Peanut Butter")),
    P("0030", "Cheddar", "dairy", "Maple Dairy", "block", "8 oz", 549, None, addon_p=0.04),
    P("0031", "Pumpkin Pie Spice", "pantry", "Maple Corner", "jar", "1 oz", 429, "baking", 0.15,
      discontinued=280),
)  # fmt: skip

MAPLE_CORNER = TenantSpec(
    key="maple-corner",
    name="Maple Corner Grocery",
    timezone="America/Los_Angeles",
    currency="USD",
    sku_prefix="MC-",
    categories=CATEGORIES,
    products=PRODUCTS,
    theme_weights={
        "breakfast": 0.3,
        "baking": 0.17,
        "party": 0.2,
        "pasta": 0.2,
        "cleaning": 0.13,
    },
    errand_rate=0.04,
    errand_weights={"0025": 2.0, "0001": 2.0, "0004": 1.0, "0028": 1.0},
    noise_rate=0.03,
    initial_customers=1420,
    arrivals_per_day=3.3,
)
