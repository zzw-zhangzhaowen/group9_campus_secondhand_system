"""Run from repository root: python3 -m gui_gao [--demo]."""
import argparse
from pathlib import Path
from tempfile import TemporaryDirectory
from .app import launch
from .gateway import Gateway


def cli():
    parser = argparse.ArgumentParser(description="Group 9 校园二手前端")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--demo", action="store_true", help="创建临时演示数据，关闭后清空")
    group.add_argument("--data-dir", type=Path, help="独立数据目录；不使用正式默认数据")
    options = parser.parse_args()
    if options.demo:
        from .demo import create_demo
        with TemporaryDirectory(prefix="group9-gui-demo-") as directory:
            launch(create_demo(directory), demo=True)
    else:
        launch(Gateway.isolated(options.data_dir) if options.data_dir else None)


if __name__ == "__main__":
    cli()
