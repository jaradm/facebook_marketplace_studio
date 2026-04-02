from dataclasses import dataclass, field
from typing import List

from config import DEFAULT_CATEGORY, DEFAULT_CONDITION, DEFAULT_CURRENCY, DEFAULT_LOCATION


@dataclass
class ProductListing:
    row_number: int
    item_number: str
    title: str
    description: str
    total_price: str
    down_payment_price: str = ""
    payment_term_price: str = ""
    location: str = DEFAULT_LOCATION
    category: str = DEFAULT_CATEGORY
    condition: str = DEFAULT_CONDITION
    currency: str = DEFAULT_CURRENCY
    image_paths: List[str] = field(default_factory=list)
    selected: bool = True
    ready: bool = False
    status: str = "draft"
    notes: str = ""


@dataclass
class UploadResult:
    item_number: str
    title: str
    status: str
    message: str
