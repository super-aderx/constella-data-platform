"""Harbor Street Market: the frontend's store (Constellate src/data/store.ts).

Same 30 products, names, categories and current prices. Five themes become the expected
communities, joined only through three planted bridges:
- Coffee <-> Breakfast via Whole Milk (coffee baskets add milk),
- Pasta night <-> Breakfast via Eggs and Parmesan (carbonara: baskets with Parmesan add eggs),
- Game day <-> Lunchbox via Cheddar (nachos: game-day baskets add cheddar).
Paper Towels is unthemed: mostly bought on errands, sometimes for game day.
"""

from generator.tenants import Bridge, CategorySpec, ProductSpec, TenantSpec

C = CategorySpec
P = ProductSpec

CATEGORIES = (
    C("dairy", "Dairy"),
    C("bakery", "Bakery"),
    C("pantry", "Pantry"),
    C("produce", "Produce"),
    C("drinks", "Drinks"),
    C("snacks", "Snacks"),
    C("deli", "Deli"),
    C("household", "Household"),
    C("milk", "Milk", "dairy"),
    C("eggs", "Eggs", "dairy"),
    C("yogurt", "Yogurt", "dairy"),
    C("butter-cream", "Butter & cream", "dairy"),
    C("cheese", "Cheese", "dairy"),
    C("bread", "Bread", "bakery"),
    C("biscuits", "Biscuits", "bakery"),
    C("spreads", "Spreads", "pantry"),
    C("cereal", "Cereal", "pantry"),
    C("coffee", "Coffee", "pantry"),
    C("pasta-sauces", "Pasta & sauces", "pantry"),
    C("oils", "Oils", "pantry"),
    C("fruit", "Fruit", "produce"),
    C("herbs", "Fresh herbs", "produce", renamed_from=(160, "Herbs & garlic")),
    C("wine-beer", "Wine & beer", "drinks"),
    C("juice", "Juice", "drinks"),
    C("chips-dips", "Chips & dips", "snacks"),
    C("cold-cuts", "Cold cuts", "deli"),
    C("kitchen", "Kitchen", "household"),
    C("paper", "Paper goods", "household"),
)

# p: chance of being picked when the theme is in the basket, set from store.ts's weekly orders.
PRODUCTS = (
    # Breakfast
    P("MILK", "Whole Milk", "milk", "Harbor Farms", "bottle", "1 L", 389, "breakfast", 0.66,
      earlier_price=(210, 369)),
    P("EGGS", "Eggs (12)", "eggs", "Harbor Farms", "pack", "12 ct", 449, "breakfast", 0.48),
    P("YOGURT", "Greek Yogurt", "yogurt", "Aegean Dairy", "tub", "500 g", 529, "breakfast", 0.22),
    P("BUTTER", "Butter", "butter-cream", "Harbor Farms", "pack", "250 g", 479, "breakfast", 0.2,
      renamed_from=(300, "Salted Butter")),
    P("BREAD", "Sourdough Bread", "bread", "Pier Bakery", "loaf", "750 g", 549, "breakfast", 0.21),
    P("JAM", "Strawberry Jam", "spreads", "Orchard Row", "jar", "340 g", 429, "breakfast", 0.09),
    P("BANANAS", "Bananas", "fruit", "Harbor Street", "kg", "1 kg", 169, "breakfast", 0.45),
    P("GRANOLA", "Granola", "cereal", "Morning Mill", "bag", "500 g", 649, "breakfast", 0.11),
    # Coffee
    P("COFFEE", "Ground Coffee", "coffee", "Dockside Roasters", "bag", "340 g", 1199, "coffee",
      0.85, earlier_price=(120, 1149)),
    P("FILTERS", "Coffee Filters", "kitchen", "Harbor Street", "pack", "100 ct", 349, "coffee",
      0.22),
    P("OAT", "Oat Milk", "milk", "Oatfield", "carton", "1 L", 459, "coffee", 0.45),
    P("BISCOTTI", "Almond Biscotti", "biscuits", "Pier Bakery", "box", "200 g", 599, "coffee",
      0.17),
    P("COLDBREW", "Cold Brew Concentrate", "coffee", "Dockside Roasters", "bottle", "946 ml",
      899, "coffee", 0.2, discontinued=150),
    # Pasta night
    P("PASTA", "Spaghetti", "pasta-sauces", "Nonna Rosa", "pack", "500 g", 199, "pasta", 0.42),
    P("SAUCE", "Tomato Sauce", "pasta-sauces", "Nonna Rosa", "jar", "680 g", 329, "pasta", 0.42),
    P("PARMESAN", "Parmesan", "cheese", "Valle Verde", "wedge", "200 g", 749, "pasta", 0.4),
    P("BASIL", "Fresh Basil", "herbs", "Harbor Street", "bunch", "30 g", 249, "pasta", 0.16),
    P("GARLIC", "Garlic", "herbs", "Harbor Street", "pack", "3 bulbs", 89, "pasta", 0.42),
    P("OIL", "Olive Oil", "oils", "Valle Verde", "bottle", "500 ml", 1099, "pasta", 0.17),
    P("WINE", "Red Wine", "wine-beer", "Hillside Cellars", "bottle", "750 ml", 1399, "pasta",
      0.2),
    # Game day
    P("CHIPS", "Tortilla Chips", "chips-dips", "Sol Snacks", "bag", "300 g", 399, "game_day",
      0.66, earlier_price=(60, 379)),
    P("SALSA", "Salsa", "chips-dips", "Sol Snacks", "jar", "450 g", 379, "game_day", 0.46),
    P("GUAC", "Guacamole", "chips-dips", "Sol Snacks", "tub", "250 g", 549, "game_day", 0.25),
    P("LAGER", "Lager (6-pack)", "wine-beer", "Tidewater Brewing", "pack", "6 × 355 ml", 1049,
      "game_day", 0.23),
    P("SOURCREAM", "Sour Cream", "butter-cream", "Harbor Farms", "tub", "250 g", 239,
      "game_day", 0.17),
    P("LIMES", "Limes", "fruit", "Harbor Street", "each", "1 ct", 59, "game_day", 0.31),
    # Lunchbox
    P("TURKEY", "Sliced Turkey", "cold-cuts", "Harbor Deli", "pack", "200 g", 699, "lunchbox",
      0.45),
    P("CHEDDAR", "Cheddar", "cheese", "Harbor Farms", "block", "250 g", 599, "lunchbox", 0.4),
    P("APPLES", "Apples", "fruit", "Orchard Row", "bag", "1.5 kg", 499, "lunchbox", 0.52),
    P("JUICE", "Juice Boxes", "juice", "Orchard Row", "pack", "8 × 200 ml", 449, "lunchbox",
      0.33),
    # Unthemed
    P("TOWELS", "Paper Towels", "paper", "Harbor Street", "pack", "6 rolls", 799, None),
)  # fmt: skip

HARBOR_STREET = TenantSpec(
    key="harbor-street",
    name="Harbor Street Market",
    timezone="Asia/Taipei",
    currency="USD",
    sku_prefix="HS-",
    categories=CATEGORIES,
    products=PRODUCTS,
    theme_weights={
        "breakfast": 0.36,
        "coffee": 0.13,
        "pasta": 0.18,
        "game_day": 0.20,
        "lunchbox": 0.13,
    },
    bridges=(
        Bridge("coffee", add="MILK", p=0.45),
        Bridge("pasta", add="EGGS", p=0.35, requires="PARMESAN"),
        Bridge("game_day", add="CHEDDAR", p=0.18),
        Bridge("game_day", add="TOWELS", p=0.06),
    ),
    errand_rate=0.05,
    errand_weights={"TOWELS": 6.0, "MILK": 1.0, "BANANAS": 1.0, "EGGS": 1.0, "LIMES": 0.5},
    noise_rate=0.03,
    affinity={
        "weekly_stocker": {"breakfast": 1.15, "coffee": 1.3, "pasta": 1.15, "lunchbox": 1.2},
        "deal_hunter": {"game_day": 1.2, "pasta": 1.1},
        "browser": {"coffee": 0.8, "game_day": 1.25},
        "one_time": {"game_day": 1.5, "coffee": 0.6},
    },
    initial_customers=2500,
    arrivals_per_day=6.0,
)
