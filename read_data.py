import argparse
import duckdb
import io
import zipfile
import re
from pathlib import Path
from collections import defaultdict

import polars as pl
from loguru import logger


def sanitize_table_name(name: str) -> str:
    base = Path(name).stem
    base = re.sub(r"(\s+|_+)", "-", base)
    base = re.sub(
        r"-\d{8}(-part-\d+)?$", "", base, flags=re.IGNORECASE
    )  # remove trailing datestamp and part number
    return base.lower()


def extract_nested_zips(top_zip_path: Path):
    logger.info(f"Opening top-level ZIP: {top_zip_path}")
    with zipfile.ZipFile(top_zip_path, "r") as top_zip:
        namelist = top_zip.namelist()
        logger.info(f"files: {namelist}")

        for path in namelist:
            logger.info(f"No match for >{path}<")

        for path in namelist:
            match = re.search(r"(\d{4}-\d{2})/", path)
            if not match:
                continue

            year_month = match.group(1)
            timestamp = f"{year_month}-01"
            folder_prefix = f"{year_month}/"
            full_prefix = f"{top_zip_path.stem}/{folder_prefix}"

            subfiles = [
                f for f in namelist if f.startswith(full_prefix) and f.endswith(".zip")
            ]
            if not subfiles:
                logger.warning(f"No ZIP file found in {folder_prefix}")
                continue

            logger.debug(f"Found nested ZIP: {subfiles[0]}")
            sub_zip_bytes = io.BytesIO(top_zip.read(subfiles[0]))

            with zipfile.ZipFile(sub_zip_bytes, "r") as inner_zip:
                nested_zip_files = [
                    f
                    for f in inner_zip.namelist()
                    if f.endswith(".zip") and "sample" not in f.lower()
                ]
                logger.debug(
                    f"Found {len(nested_zip_files)} valid inner ZIPs in {subfiles[0]}"
                )

                grouped = defaultdict(list)
                for name in nested_zip_files:
                    prefix = re.sub(
                        r"[-_\s]*part\d+\.zip$",
                        "",
                        Path(name).stem,
                        flags=re.IGNORECASE,
                    )
                    grouped[prefix].append(name)

                for prefix, parts in grouped.items():
                    table_name = sanitize_table_name(prefix)
                    logger.info(f"Preparing to load data into table: {table_name}")
                    all_frames = []

                    for part in sorted(parts):
                        logger.debug(f"Reading part ZIP: {part}")
                        part_bytes = io.BytesIO(inner_zip.read(part))
                        with zipfile.ZipFile(part_bytes, "r") as part_zip:
                            txt_files = [
                                f for f in part_zip.namelist() if f.endswith(".txt")
                            ]
                            if not txt_files:
                                logger.warning(f"No .txt file found in part: {part}")
                                continue
                            for txt_file in txt_files:
                                logger.debug(f"Reading text file: {txt_file}")
                                content = part_zip.read(txt_file).decode(
                                    "utf-8", errors="replace"
                                )
                                try:
                                    df = pl.read_csv(
                                        io.StringIO(content),
                                        separator="|",
                                        infer_schema_length=10000,
                                        null_values=["", "XXXXX"],
                                    )
                                    df = df.with_columns(
                                        pl.lit(timestamp).alias("timestamp")
                                    )
                                    all_frames.append(df)
                                except Exception as e:
                                    logger.error(
                                        f"Failed to parse {txt_file} in {part}: {e}"
                                    )

                    if all_frames:
                        try:
                            combined = pl.concat(
                                all_frames, how="vertical", rechunk=True
                            )
                            logger.success(
                                f"Loaded {len(combined)} rows for table {table_name}"
                            )
                            yield table_name, combined
                        except Exception as e:
                            logger.error(
                                f"Failed to concatenate frames for table {table_name}: {e}"
                            )
                    else:
                        logger.warning(f"No valid data for table {table_name}")


def main():
    parser = argparse.ArgumentParser(
        description="Extract nested Monthly Prescription Drug Plan Formulary and Pharmacy Network Information zips and insert into DuckDB."
    )
    parser.add_argument(
        "--zip-path",
        type=Path,
        required=True,
        help="Path to the top-level Monthly Prescription Drug Plan Formulary and Pharmacy Network Information zip file",
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        default="database.db",
        required=True,
        help="Path to the DuckDB database file",
    )
    parser.add_argument(
        "--log-level", default="INFO", help="Log level (DEBUG, INFO, WARNING, ERROR)"
    )
    args = parser.parse_args()

    logger.remove()
    logger.add(lambda msg: print(msg, end=""), level=args.log_level.upper())

    con = duckdb.connect(args.db_path)

    for table_name, df in extract_nested_zips(args.zip_path):
        try:
            con.execute(
                f'CREATE TABLE IF NOT EXISTS "{table_name}" AS SELECT * FROM df'
            )
            logger.info(f"Created table {table_name}")
        except duckdb.CatalogException:
            con.execute(f'INSERT INTO "{table_name}" SELECT * FROM df')
            logger.info(f"Inserted into existing table {table_name}")


if __name__ == "__main__":
    main()
