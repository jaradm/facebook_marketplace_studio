import time
from typing import Callable, List

from playwright.sync_api import Playwright, TimeoutError as PlaywrightTimeoutError, sync_playwright

from config import MARKETPLACE_CREATE_URL
from models import ProductListing, UploadResult
from services.utils import compose_listing_description


class FacebookMarketplacePoster:
    def __init__(self, profile_dir: str, headful: bool, logger: Callable[[str], None]) -> None:
        self.profile_dir = profile_dir
        self.headful = headful
        self.logger = logger

    def post_many(self, products: List[ProductListing], on_result: Callable[[UploadResult], None]) -> None:
        with sync_playwright() as pw:
            browser = self._launch(pw)
            page = browser.pages[0] if browser.pages else browser.new_page()
            try:
                self._ensure_logged_in(page)
                for product in products:
                    on_result(self._post_one(page, product))
            finally:
                browser.close()

    def _launch(self, playwright: Playwright):
        return playwright.chromium.launch_persistent_context(
            user_data_dir=self.profile_dir,
            headless=not self.headful,
            viewport={"width": 1440, "height": 1100},
        )

    def _ensure_logged_in(self, page) -> None:
        page.goto("https://www.facebook.com/", wait_until="domcontentloaded")
        time.sleep(3)
        if "login" in page.url.lower():
            self.logger("Please log into Facebook in the opened browser window, then return here.")
            while "login" in page.url.lower():
                time.sleep(2)
                try:
                    page.reload(wait_until="domcontentloaded")
                except Exception:
                    pass

    def _safe_click_text(self, page, texts: List[str], timeout: int = 4000) -> bool:
        for text in texts:
            try:
                loc = page.get_by_text(text, exact=False).first
                if loc.is_visible(timeout=timeout):
                    loc.click(timeout=timeout)
                    return True
            except Exception:
                continue
        return False

    def _safe_fill_label(self, page, labels: List[str], value: str, timeout: int = 4000) -> bool:
        for label in labels:
            try:
                page.get_by_label(label, exact=False).first.fill(value, timeout=timeout)
                return True
            except Exception:
                continue
        return False

    def _safe_fill_placeholder(self, page, placeholders: List[str], value: str, timeout: int = 4000) -> bool:
        for ph in placeholders:
            try:
                page.get_by_placeholder(ph, exact=False).first.fill(value, timeout=timeout)
                return True
            except Exception:
                continue
        return False

    def _fill_title(self, page, title: str) -> None:
        ok = self._safe_fill_label(page, ["Title"], title) or self._safe_fill_placeholder(page, ["Title"], title)
        if not ok:
            raise RuntimeError("Could not find the Title field")

    def _fill_price(self, page, price: str) -> None:
        ok = self._safe_fill_label(page, ["Price"], price) or self._safe_fill_placeholder(page, ["Price"], price)
        if not ok:
            raise RuntimeError("Could not find the Price field")

    def _fill_description(self, page, description: str) -> None:
        ok = self._safe_fill_label(page, ["Description"], description) or self._safe_fill_placeholder(page, ["Description"], description)
        if ok:
            return
        for selector in ['textarea', '[contenteditable="true"]']:
            try:
                loc = page.locator(selector).first
                loc.click(timeout=2500)
                loc.fill(description, timeout=2500)
                return
            except Exception:
                continue
        raise RuntimeError("Could not find the Description field")

    def _upload_images(self, page, image_paths: List[str]) -> None:
        if not image_paths:
            raise RuntimeError("No images to upload")
        try:
            page.locator('input[type="file"]').first.set_input_files(image_paths, timeout=8000)
            return
        except Exception:
            pass
        with page.expect_file_chooser(timeout=5000) as fc_info:
            clicked = self._safe_click_text(page, ["Add photos", "Add Photo", "Photo", "Photos"])
            if not clicked:
                raise RuntimeError("Could not trigger the photo upload control")
        fc_info.value.set_files(image_paths)

    def _set_location(self, page, value: str) -> None:
        filled = self._safe_fill_label(page, ["Location"], value) or self._safe_fill_placeholder(page, ["Location"], value)
        if filled:
            time.sleep(2)
            self._safe_click_text(page, [value], timeout=2500)

    def _set_category(self, page, value: str) -> None:
        if self._safe_click_text(page, ["Category"], timeout=2500):
            time.sleep(1)
            self._safe_click_text(page, [value], timeout=2500)

    def _set_condition(self, page, value: str) -> None:
        if self._safe_click_text(page, ["Condition"], timeout=2500):
            time.sleep(1)
            self._safe_click_text(page, [value], timeout=2500)

    def _post_one(self, page, product: ProductListing) -> UploadResult:
        self.logger(f"Posting {product.item_number} - {product.title}")
        try:
            page.goto(MARKETPLACE_CREATE_URL, wait_until="domcontentloaded", timeout=30000)
            time.sleep(3)
            self._upload_images(page, product.image_paths)
            time.sleep(2)
            self._fill_title(page, product.title)
            self._fill_price(page, product.payment_term_price)
            self._set_category(page, product.category)
            self._set_condition(page, product.condition)
            self._fill_description(
                page,
                compose_listing_description(
                    product.description,
                    product.total_price,
                    product.down_payment_price,
                    product.payment_term_price,
                ),
            )
            self._set_location(page, product.location)
            time.sleep(2)

            if not self._safe_click_text(page, ["Next", "Publish", "Post"], timeout=5000):
                return UploadResult(product.item_number, product.title, "needs review", "Could not find the publish button automatically")
            time.sleep(4)
            return UploadResult(product.item_number, product.title, "posted", "Listing submitted")
        except PlaywrightTimeoutError as exc:
            return UploadResult(product.item_number, product.title, "error", f"Timeout: {exc}")
        except Exception as exc:
            return UploadResult(product.item_number, product.title, "error", str(exc))
