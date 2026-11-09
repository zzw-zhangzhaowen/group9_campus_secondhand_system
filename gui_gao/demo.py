"""Disposable demo data, created exclusively through public backend services."""
from pathlib import Path
from .gateway import Gateway

DEMO_USERNAME = "gao_demo"
DEMO_PASSWORD = "Campus123"


def create_demo(directory):
    gateway = Gateway.isolated(directory)
    users = [(DEMO_USERNAME, "Gao"), ("lin_demo", "Lin"), ("chen_demo", "Chen")]
    for username, nickname in users:
        gateway.register(username, DEMO_PASSWORD, nickname)
    assets = Path(__file__).parent / "assets"
    samples = [
        (0, "Python textbook", "Books", "35", "Good condition with a few pencil notes. Suitable for Python beginners.", "book"),
        (1, "Wireless keyboard", "Electronics", "88", "Bluetooth works well. Clean keycaps. Charging cable included.", "keyboard"),
        (2, "Reading lamp", "Home & Living", "45", "Warm white light with an adjustable angle. Used for reading; works well.", "lamp"),
        (0, "Canvas tote bag", "Clothing", "22", "Beige canvas bag with room for A4 books. Washed and undamaged.", "bag"),
        (1, "Hoodie size M", "Clothing", "60", "Light blue, size M, lightly worn. Ask about measurements before meeting.", "hoodie"),
        (2, "Travel mug", "Home & Living", "28", "450 ml, good condition. Cleaned; please wash again before use.", "bottle"),
        (0, "Calculator", "Electronics", "50", "Keys and display work well. Protective cover included.", "calculator"),
        (1, "3 lined notebooks", "Books", "15", "Three unused lined notebooks, 80 pages each. Suitable for class notes.", "notebook"),
    ]
    for user_index, name, category, price, description, asset in samples:
        gateway.login(users[user_index][0], DEMO_PASSWORD)
        gateway.save_item(dict(name=name, category=category, price=price,
                          description=description, image_path=str(assets / f"{asset}.png")))
    gateway.login("lin_demo", DEMO_PASSWORD)
    gateway.features.toggle_favorite(1)
    gateway.features.add_message(1, "Is this book suitable for beginners?")
    gateway.features.create_intention(1)
    gateway.login(DEMO_USERNAME, DEMO_PASSWORD)
    gateway.features.add_message(1, "Yes. It includes basic syntax and exercises. You can check the contents first.")
    gateway.features.toggle_favorite(2)
    gateway.features.toggle_favorite(3)
    gateway.features.add_message(2, "Does this keyboard work with a Mac?")
    gateway.features.create_intention(2)
    gateway.login("lin_demo", DEMO_PASSWORD)
    gateway.features.add_message(2, "Yes, the Bluetooth connection works well.")
    gateway.logout()
    return gateway
