"""Disposable demo data, created exclusively through public backend services."""
from pathlib import Path
from .gateway import Gateway

DEMO_USERNAME = "gao_demo"
DEMO_PASSWORD = "Campus123"


def create_demo(directory):
    gateway = Gateway.isolated(directory)
    users = [(DEMO_USERNAME, "Gao同学"), ("lin_demo", "小林"), ("chen_demo", "陈同学")]
    for username, nickname in users:
        gateway.register(username, DEMO_PASSWORD, nickname)
    assets = Path(__file__).parent / "assets"
    samples = [
        (0, "Python 入门教材", "书籍", "35", "九成新，少量铅笔笔记。适合 Python 入门学习。", "book"),
        (1, "无线键盘", "电子产品", "88", "蓝牙连接正常，键帽整洁。附充电线。", "keyboard"),
        (2, "桌面阅读灯", "生活用品", "45", "暖白光，可调整角度。宿舍阅读使用，功能正常。", "lamp"),
        (0, "轻便帆布包", "服饰", "22", "米色帆布袋，可放 A4 书本。已清洗，无破损。", "bag"),
        (1, "连帽卫衣 M 码", "服饰", "60", "浅蓝色，M 码，少量穿着。尺寸可参考描述。", "hoodie"),
        (2, "不锈钢保温杯", "生活用品", "28", "450ml，外观完好。已清洁，请收到后再次清洗。", "bottle"),
        (0, "科学计算器", "电子产品", "50", "按键和显示正常，适合日常计算。附保护盖。", "calculator"),
        (1, "横线笔记本三本", "书籍", "15", "三本全新横线本，每本 80 页，适合课堂笔记。", "notebook"),
    ]
    for user_index, name, category, price, description, asset in samples:
        gateway.login(users[user_index][0], DEMO_PASSWORD)
        gateway.save_item(dict(name=name, category=category, price=price,
                          description=description, image_path=str(assets / f"{asset}.png")))
    gateway.login("lin_demo", DEMO_PASSWORD)
    gateway.features.toggle_favorite(1)
    gateway.features.add_message(1, "这本书适合没有基础的同学吗？")
    gateway.features.create_intention(1)
    gateway.login(DEMO_USERNAME, DEMO_PASSWORD)
    gateway.features.add_message(1, "适合的，包含基础语法和练习，可以先看看目录。")
    gateway.features.toggle_favorite(2)
    gateway.features.toggle_favorite(3)
    gateway.features.add_message(2, "键盘可以连接 Mac 吗？")
    gateway.features.create_intention(2)
    gateway.login("lin_demo", DEMO_PASSWORD)
    gateway.features.add_message(2, "可以，蓝牙连接正常。")
    gateway.logout()
    return gateway
