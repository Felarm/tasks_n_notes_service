import json
from argparse import ArgumentParser

from loguru import logger

from main import app


def export_contracts():
    with open("openapi.json", "w") as f:
        json.dump(app.openapi(), f, indent=2)
    logger.info("exported schemas to openapi.json")



def main():
    parser = ArgumentParser(description="CLI manager")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("export_openapi")

    args = parser.parse_args()
    if args.command == "export_openapi":
        export_contracts()


if __name__ == "__main__":
    main()