"""Run from repository root: python3 -m gui_gao [--demo]."""
import argparse
from pathlib import Path
from tempfile import TemporaryDirectory
from .app import launch
from .gateway import Gateway


def cli():
    parser = argparse.ArgumentParser(description="Group 9 Campus Market frontend")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--demo", action="store_true", help="Create temporary demo data and clear it on exit")
    group.add_argument("--data-dir", type=Path, help="Use a separate data directory instead of production data")
    options = parser.parse_args()
    if options.demo:
        from .demo import create_demo
        with TemporaryDirectory(prefix="group9-gui-demo-") as directory:
            launch(create_demo(directory), demo=True)
    else:
        launch(Gateway.isolated(options.data_dir) if options.data_dir else None)


if __name__ == "__main__":
    cli()
