from pathlib import Path
from typing import List

import pandas as pd

from models import ProductListing
from services.image_matcher import find_matching_images
from services.utils import detect_column, normalize_price


def load_products_from_excel(
    excel_path: Path,
    images_dir: Path,
    default_location: str,
) -> List[ProductListing]:
    df = pd.read_excel(excel_path)
    columns = list(df.columns)

    item_col = detect_column(columns, ["ItemNumber", "Item Number", "SKU", "Item No", "Product ID"])
    title_col = detect_column(columns, ["ProductName", "Product Name", "Name", "Title"])
    desc_col = detect_column(columns, ["Description", "Desc", "Product Description"])
    total_price_col = detect_column(columns, ["Total Price", "TotalPrice", "Full Price", "Cash Price", "Price", "Amount", "Sale Price"])
    down_payment_col = detect_column(columns, ["Down Payment Price", "DownPaymentPrice", "Down Payment", "Deposit"])
    payment_term_col = detect_column(columns, ["Payment Term Price", "PaymentTermPrice", "Biweekly Payment", "Payment", "Installment Price"])

    missing: list[str] = []
    if not item_col:
        missing.append("ItemNumber")
    if not title_col:
        missing.append("ProductName")
    if not desc_col:
        missing.append("Description")
    if not total_price_col:
        missing.append("Total Price")
    if not down_payment_col:
        missing.append("Down Payment Price")
    if not payment_term_col:
        missing.append("Payment Term Price")
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")

    products: list[ProductListing] = []
    for idx, row in df.iterrows():
        item_number = str(row[item_col]).strip()
        if not item_number or item_number.lower() == "nan":
            continue

        products.append(
            ProductListing(
                row_number=idx + 2,
                item_number=item_number,
                title=str(row[title_col]).strip() if not pd.isna(row[title_col]) else "",
                description=str(row[desc_col]).strip() if not pd.isna(row[desc_col]) else "",
                total_price=normalize_price(row[total_price_col]),
                down_payment_price=normalize_price(row[down_payment_col]),
                payment_term_price=normalize_price(row[payment_term_col]),
                location=default_location,
                image_paths=find_matching_images(item_number, images_dir),
            )
        )

    return products
