import argparse
import sys
from loguru import logger


def parse_cli() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Medical Analytics Chat")
    p.add_argument("--database-path", default="database.db", help="duckdb database")
    p.add_argument("--model", default="o4-mini", help="LLM name/tag")
    p.add_argument("--logfile", default="info.log", help="Rotating log file")
    p.add_argument(
        "--provider",
        choices=["olama", "openai"],
        default="openai",
        help="LLM provider to use (olama or openai)",
    )
    return p.parse_known_args()[0]  # Streamlit swallows unknown flags


def setup_logging(logfile: str | None):
    fmt = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<cyan>{name}</cyan>:<cyan>{file}</cyan>:<cyan>{line}</cyan> | "
        "<level>{level: <8}</level> | {message}"
    )
    logger.remove()
    logger.add(sys.stderr, format=fmt)
    if logfile:
        logger.add(logfile, rotation="5 MB", format=fmt)


CLI = parse_cli()
setup_logging(CLI.logfile)
