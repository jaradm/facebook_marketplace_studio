import re
from typing import List, Optional

import pandas as pd

from models import ProductListing


def slug_token(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9]", "", str(value)).lower()


def normalize_price(value: object) -> str:
    if pd.isna(value):
        return ""
    if isinstance(value, (int, float)):
        if float(value).is_integer():
            return str(int(value))
        return f"{float(value):.2f}"
    return str(value).strip().replace("$", "").replace(",", "")


def detect_column(columns: List[str], candidates: List[str]) -> Optional[str]:
    normalized = {str(c).strip().lower(): c for c in columns}
    for candidate in candidates:
        found = normalized.get(candidate.strip().lower())
        if found:
            return found
    return None


def listing_is_ready(product: ProductListing) -> bool:
    return bool(
        product.title.strip()
        and product.payment_term_price.strip()
        and product.total_price.strip()
        and product.down_payment_price.strip()
        and product.location.strip()
        and product.image_paths
    )


def make_notes(product: ProductListing) -> str:
    issues: list[str] = []
    if not product.title.strip():
        issues.append("missing title")
    if not product.total_price.strip():
        issues.append("missing total price")
    if not product.down_payment_price.strip():
        issues.append("missing down payment")
    if not product.payment_term_price.strip():
        issues.append("missing payment term price")
    if not product.location.strip():
        issues.append("missing location")
    if not product.image_paths:
        issues.append("no matching image")
    return "Ready" if not issues else ", ".join(issues)


def refresh_product_status(product: ProductListing) -> None:
    product.ready = listing_is_ready(product)
    product.notes = make_notes(product)
    if product.status == "posted":
        return
    product.status = "ready" if product.ready else "needs attention"


def compose_listing_description(
    base_description: str,
    total_price: str,
    down_payment: str,
    payment_term: str,
) -> str:
    lines: list[str] = []
    base = base_description.strip()
    if base:
        lines.append(base)
        lines.append("")
    if total_price:
        lines.append(f"Total of the set: ${total_price}")
    if down_payment:
        lines.append(f"Down payment: ${down_payment}")
    if payment_term:
        lines.append(f"Payment term: ${payment_term} every 2 weeks")
    return "\n".join(lines).strip()
