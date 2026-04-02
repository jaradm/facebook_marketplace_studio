from __future__ import annotations

import os
import threading
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageOps, ImageTk

from config import (
    APP_TITLE,
    DEFAULT_CATEGORY,
    DEFAULT_CONDITION,
    DEFAULT_LOCATION,
    PROFILE_DIR,
    PROFILES_ROOT,
    THUMBNAIL_SIZE,
)
from models import ProductListing, UploadResult
from services.ai_service import AIDescriptionService
from services.excel_loader import load_products_from_excel
from services.facebook_poster import FacebookMarketplacePoster
from services.state_manager import load_state, products_from_state, save_state
from services.utils import compose_listing_description, refresh_product_status


class MarketplaceStudioApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("1480x900")
        self.root.minsize(1280, 780)

        self.products: List[ProductListing] = []
        self.current_index: Optional[int] = None
        self.excel_path: Optional[Path] = None
        self.images_dir: Optional[Path] = None
        self.ai_service = AIDescriptionService()
        self.thumbnail_cache: Dict[str, ImageTk.PhotoImage] = {}

        self.default_location_var = tk.StringVar(value=DEFAULT_LOCATION)
        self.headful_var = tk.BooleanVar(value=True)
        self.profile_name_var = tk.StringVar(value="default")
        self.profile_path_var = tk.StringVar()
        self.saved_profiles: List[str] = []
        self.profile_combo: Optional[ttk.Combobox] = None

        self.status_var = tk.StringVar(value="Ready")
        self.filter_var = tk.StringVar(value="All")
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_text_var = tk.StringVar(value="Idle")

        self.item_var = tk.StringVar()
        self.title_var = tk.StringVar()
        self.total_price_var = tk.StringVar()
        self.down_payment_var = tk.StringVar()
        self.payment_term_var = tk.StringVar()
        self.location_var = tk.StringVar(value=DEFAULT_LOCATION)
        self.category_var = tk.StringVar(value=DEFAULT_CATEGORY)
        self.condition_var = tk.StringVar(value=DEFAULT_CONDITION)
        self.selected_var = tk.BooleanVar(value=True)

        self.product_list: Optional[tk.Listbox] = None
        self.image_label: Optional[ttk.Label] = None
        self.preview_title: Optional[ttk.Label] = None
        self.preview_price: Optional[ttk.Label] = None
        self.preview_location: Optional[ttk.Label] = None
        self.preview_desc: Optional[tk.Text] = None
        self.description_text: Optional[tk.Text] = None
        self.log_text: Optional[tk.Text] = None
        self.progress_bar: Optional[ttk.Progressbar] = None

        self._build_ui()
        self.refresh_saved_profiles(silent=True)
        self.activate_profile(silent=True)
        self._load_state_if_present()

    def _build_ui(self) -> None:
        self.root.columnconfigure(0, weight=0)
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(0, weight=0)
        self.root.rowconfigure(1, weight=1)

        self._build_top_bar()
        self._build_left_panel()
        self._build_center_panel()

        for var in [
            self.title_var,
            self.total_price_var,
            self.down_payment_var,
            self.payment_term_var,
            self.location_var,
            self.category_var,
            self.condition_var,
        ]:
            var.trace_add("write", lambda *_: self.refresh_preview())

    def _build_top_bar(self) -> None:
        top = ttk.Frame(self.root, padding=14, style="App.TFrame")
        top.grid(row=0, column=0, columnspan=2, sticky="ew")

        for i in range(9):
            top.columnconfigure(i, weight=1, uniform="top")

        ttk.Button(top, text="Open Excel", command=self.choose_excel, style="Primary.TButton").grid(
            row=0, column=0, padx=4, pady=4, sticky="ew"
        )
        ttk.Button(top, text="Open Images Folder", command=self.choose_images_dir, style="Primary.TButton").grid(
            row=0, column=1, padx=4, pady=4, sticky="ew"
        )
        ttk.Button(top, text="Load Products", command=self.load_products, style="Primary.TButton").grid(
            row=0, column=2, padx=4, pady=4, sticky="ew"
        )
        ttk.Button(top, text="Save Edits", command=self.save_current_product, style="Primary.TButton").grid(
            row=0, column=3, padx=4, pady=4, sticky="ew"
        )
        ttk.Button(top, text="Validate All", command=self.validate_all, style="Primary.TButton").grid(
            row=0, column=4, padx=4, pady=4, sticky="ew"
        )
        ttk.Button(top, text="Generate AI For Selected", command=self.generate_ai_for_selected, style="Primary.TButton").grid(
            row=0, column=5, padx=4, pady=4, sticky="ew"
        )
        ttk.Button(top, text="Post Selected", command=self.post_selected, style="Primary.TButton").grid(
            row=0, column=6, padx=4, pady=4, sticky="ew"
        )
        ttk.Button(top, text="Post All Ready", command=self.post_all_ready, style="Primary.TButton").grid(
            row=0, column=7, padx=4, pady=4, sticky="ew"
        )
        ttk.Label(top, textvariable=self.status_var, style="App.TLabel", anchor="e").grid(
            row=0, column=8, padx=4, pady=4, sticky="ew"
        )

        settings = ttk.Frame(top, style="App.TFrame")
        settings.grid(row=1, column=0, columnspan=9, sticky="ew", pady=(6, 0))
        for i in range(8):
            settings.columnconfigure(i, weight=1)

        ttk.Label(settings, text="Default location", style="App.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Entry(settings, textvariable=self.default_location_var, style="Modern.TEntry").grid(
            row=0, column=1, sticky="ew", padx=(6, 12)
        )

        ttk.Label(settings, text="Facebook profile", style="App.TLabel").grid(row=0, column=2, sticky="w")
        self.profile_combo = ttk.Combobox(settings, textvariable=self.profile_name_var, style="Modern.TCombobox")
        self.profile_combo.grid(row=0, column=3, sticky="ew", padx=(6, 12))
        self.profile_combo.bind("<<ComboboxSelected>>", lambda e: self.activate_profile())

        ttk.Button(settings, text="Refresh Profiles", command=self.refresh_saved_profiles, style="Secondary.TButton").grid(
            row=0, column=4, sticky="ew", padx=4
        )
        ttk.Button(settings, text="Use / Create Profile", command=self.activate_profile, style="Secondary.TButton").grid(
            row=0, column=5, sticky="ew", padx=4
        )
        ttk.Button(settings, text="Open Profile Folder", command=self.open_profiles_folder, style="Secondary.TButton").grid(
            row=0, column=6, sticky="ew", padx=4
        )
        ttk.Checkbutton(settings, text="Show browser while posting", variable=self.headful_var, style="Modern.TCheckbutton").grid(
            row=0, column=7, sticky="e"
        )

        progress_row = ttk.Frame(top, style="App.TFrame")
        progress_row.grid(row=2, column=0, columnspan=9, sticky="ew", pady=(10, 0))
        progress_row.columnconfigure(0, weight=1)
        progress_row.columnconfigure(1, weight=0)

        self.progress_bar = ttk.Progressbar(
            progress_row,
            variable=self.progress_var,
            maximum=100,
            mode="determinate",
            style="Modern.Horizontal.TProgressbar",
        )
        self.progress_bar.grid(row=0, column=0, sticky="ew", padx=(0, 10))

        ttk.Label(progress_row, textvariable=self.progress_text_var, style="App.TLabel").grid(
            row=0, column=1, sticky="e"
        )

    def _build_left_panel(self) -> None:
        left = ttk.Frame(self.root, padding=(14, 0, 10, 14), style="Card.TFrame")
        left.grid(row=1, column=0, sticky="nsew")
        left.columnconfigure(0, weight=1)
        left.rowconfigure(2, weight=1)

        ttk.Label(left, text="Products", style="CardTitle.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 8))

        filter_frame = ttk.Frame(left, style="Card.TFrame")
        filter_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        filter_frame.columnconfigure(1, weight=1)

        ttk.Label(filter_frame, text="Filter", style="Card.TLabel").grid(row=0, column=0, sticky="w")
        filter_box = ttk.Combobox(
            filter_frame,
            textvariable=self.filter_var,
            values=["All", "Ready", "Needs attention", "Posted"],
            state="readonly",
            style="Modern.TCombobox",
        )
        filter_box.grid(row=0, column=1, sticky="ew", padx=(8, 0))
        filter_box.bind("<<ComboboxSelected>>", lambda e: self.refresh_product_list())

        list_frame = ttk.Frame(left, style="Card.TFrame")
        list_frame.grid(row=2, column=0, sticky="nsew")
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        self.product_list = tk.Listbox(
            list_frame,
            bg="#ffffff",
            fg="#111827",
            selectbackground="#2563eb",
            selectforeground="#ffffff",
            highlightthickness=1,
            highlightbackground="#cbd5e1",
            bd=0,
            font=("Segoe UI", 10),
            activestyle="none",
        )
        self.product_list.grid(row=0, column=0, sticky="nsew")
        self.product_list.bind("<<ListboxSelect>>", self.on_product_selected)

        product_scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.product_list.yview)
        product_scroll.grid(row=0, column=1, sticky="ns")
        self.product_list.configure(yscrollcommand=product_scroll.set)

    def _build_center_panel(self) -> None:
        center = ttk.Frame(self.root, padding=(0, 0, 14, 14), style="App.TFrame")
        center.grid(row=1, column=1, sticky="nsew")
        center.columnconfigure(0, weight=1)
        center.columnconfigure(1, weight=1)
        center.rowconfigure(0, weight=1)

        self._build_preview_panel(center)
        self._build_resizable_right_panel(center)

    def _build_preview_panel(self, parent: ttk.Frame) -> None:
        preview_frame = ttk.Frame(parent, padding=14, style="Card.TFrame")
        preview_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(5, weight=1)

        ttk.Label(preview_frame, text="Listing Preview", style="CardTitle.TLabel").grid(
            row=0, column=0, sticky="w", pady=(0, 10)
        )

        self.image_label = ttk.Label(preview_frame, text="No image loaded", style="Card.TLabel", anchor="center")
        self.image_label.grid(row=1, column=0, sticky="ew", pady=(0, 12))

        self.preview_title = ttk.Label(
            preview_frame,
            text="Title",
            style="PreviewTitle.TLabel",
            wraplength=360,
            justify="center",
        )
        self.preview_title.grid(row=2, column=0, sticky="ew")

        self.preview_price = ttk.Label(
            preview_frame,
            text="$0 / every 2 weeks",
            style="PreviewPrice.TLabel",
        )
        self.preview_price.grid(row=3, column=0, sticky="ew", pady=(6, 4))

        self.preview_location = ttk.Label(
            preview_frame,
            text=DEFAULT_LOCATION,
            style="Muted.TLabel",
            wraplength=360,
            justify="center",
        )
        self.preview_location.grid(row=4, column=0, sticky="ew", pady=(0, 10))

        preview_text_frame = ttk.Frame(preview_frame, style="Card.TFrame")
        preview_text_frame.grid(row=5, column=0, sticky="nsew")
        preview_text_frame.columnconfigure(0, weight=1)
        preview_text_frame.rowconfigure(0, weight=1)

        self.preview_desc = tk.Text(
            preview_text_frame,
            wrap="word",
            bg="#ffffff",
            fg="#111827",
            insertbackground="#111827",
            relief="flat",
            bd=0,
            font=("Segoe UI", 10),
            padx=12,
            pady=12,
        )
        self.preview_desc.grid(row=0, column=0, sticky="nsew")

        preview_scroll = ttk.Scrollbar(preview_text_frame, orient="vertical", command=self.preview_desc.yview)
        preview_scroll.grid(row=0, column=1, sticky="ns")
        self.preview_desc.configure(yscrollcommand=preview_scroll.set, state="disabled")

    def _build_resizable_right_panel(self, parent: ttk.Frame) -> None:
        pane = tk.PanedWindow(
            parent,
            orient=tk.VERTICAL,
            sashwidth=8,
            bd=0,
            bg="#eef2f7",
            relief="flat",
        )
        pane.grid(row=0, column=1, sticky="nsew")

        form = self._create_edit_listing_section(pane)
        desc = self._create_description_section(pane)
        log = self._create_log_section(pane)

        pane.add(form, minsize=220)
        pane.add(desc, minsize=220)
        pane.add(log, minsize=160)

    def _create_edit_listing_section(self, parent: tk.PanedWindow) -> ttk.Frame:
        form = ttk.Frame(parent, padding=14, style="Card.TFrame")
        form.columnconfigure(0, weight=1)
        form.rowconfigure(1, weight=1)

        ttk.Label(form, text="Edit Listing", style="CardTitle.TLabel").grid(
            row=0, column=0, sticky="w", pady=(0, 10)
        )

        form_canvas = tk.Canvas(form, bg="#f8fafc", highlightthickness=0, bd=0)
        form_canvas.grid(row=1, column=0, sticky="nsew")

        form_scroll = ttk.Scrollbar(form, orient="vertical", command=form_canvas.yview)
        form_scroll.grid(row=1, column=1, sticky="ns")
        form_canvas.configure(yscrollcommand=form_scroll.set)

        form_inner = ttk.Frame(form_canvas, style="Card.TFrame")
        form_window = form_canvas.create_window((0, 0), window=form_inner, anchor="nw")

        def sync_form_scroll(_event=None) -> None:
            form_canvas.configure(scrollregion=form_canvas.bbox("all"))
            form_canvas.itemconfigure(form_window, width=form_canvas.winfo_width())

        form_inner.bind("<Configure>", sync_form_scroll)
        form_canvas.bind("<Configure>", sync_form_scroll)

        row = 0
        fields = [
            ("Item Number", self.item_var, "readonly"),
            ("Title", self.title_var, "normal"),
            ("Total Price", self.total_price_var, "normal"),
            ("Down Payment", self.down_payment_var, "normal"),
            ("Payment Every 2 Weeks", self.payment_term_var, "normal"),
            ("Location", self.location_var, "normal"),
            ("Category", self.category_var, "normal"),
            ("Condition", self.condition_var, "normal"),
        ]

        for label, var, state in fields:
            ttk.Label(form_inner, text=label, style="Card.TLabel").grid(
                row=row, column=0, sticky="w", padx=(0, 10), pady=6
            )
            ttk.Entry(form_inner, textvariable=var, state=state, style="Modern.TEntry").grid(
                row=row, column=1, sticky="ew", pady=6
            )
            row += 1

        form_inner.columnconfigure(1, weight=1)
        ttk.Checkbutton(
            form_inner,
            text="Selected for posting",
            variable=self.selected_var,
            style="Modern.TCheckbutton",
        ).grid(row=row, column=1, sticky="w", pady=6)

        return form

    def _create_description_section(self, parent: tk.PanedWindow) -> ttk.Frame:
        desc_frame = ttk.Frame(parent, padding=14, style="Card.TFrame")
        desc_frame.columnconfigure(0, weight=1)
        desc_frame.rowconfigure(1, weight=1)

        ttk.Label(desc_frame, text="Description", style="CardTitle.TLabel").grid(
            row=0, column=0, sticky="w", pady=(0, 10)
        )

        desc_text_frame = ttk.Frame(desc_frame, style="Card.TFrame")
        desc_text_frame.grid(row=1, column=0, sticky="nsew")
        desc_text_frame.columnconfigure(0, weight=1)
        desc_text_frame.rowconfigure(0, weight=1)

        self.description_text = tk.Text(
            desc_text_frame,
            wrap="word",
            bg="#ffffff",
            fg="#111827",
            insertbackground="#111827",
            relief="flat",
            bd=0,
            font=("Segoe UI", 10),
            padx=12,
            pady=12,
        )
        self.description_text.grid(row=0, column=0, sticky="nsew")

        desc_scroll = ttk.Scrollbar(desc_text_frame, orient="vertical", command=self.description_text.yview)
        desc_scroll.grid(row=0, column=1, sticky="ns")
        self.description_text.configure(yscrollcommand=desc_scroll.set)

        desc_buttons = ttk.Frame(desc_frame, style="Card.TFrame")
        desc_buttons.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        for i in range(3):
            desc_buttons.columnconfigure(i, weight=1)

        ttk.Button(
            desc_buttons,
            text="Generate AI Description",
            command=self.generate_ai_for_current,
            style="Secondary.TButton",
        ).grid(row=0, column=0, sticky="ew", padx=(0, 6))

        ttk.Button(
            desc_buttons,
            text="Refresh Preview",
            command=self.refresh_preview,
            style="Secondary.TButton",
        ).grid(row=0, column=1, sticky="ew", padx=6)

        ttk.Button(
            desc_buttons,
            text="Apply Default Location to All",
            command=self.apply_default_location_to_all,
            style="Secondary.TButton",
        ).grid(row=0, column=2, sticky="ew", padx=(6, 0))

        return desc_frame

    def _create_log_section(self, parent: tk.PanedWindow) -> ttk.Frame:
        log_frame = ttk.Frame(parent, padding=14, style="Card.TFrame")
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(1, weight=1)

        ttk.Label(log_frame, text="Activity Log", style="CardTitle.TLabel").grid(
            row=0, column=0, sticky="w", pady=(0, 10)
        )

        log_text_frame = ttk.Frame(log_frame, style="Card.TFrame")
        log_text_frame.grid(row=1, column=0, sticky="nsew")
        log_text_frame.columnconfigure(0, weight=1)
        log_text_frame.rowconfigure(0, weight=1)

        self.log_text = tk.Text(
            log_text_frame,
            wrap="word",
            bg="#ffffff",
            fg="#111827",
            insertbackground="#111827",
            relief="flat",
            bd=0,
            font=("Consolas", 10),
            padx=12,
            pady=12,
        )
        self.log_text.grid(row=0, column=0, sticky="nsew")

        log_scroll = ttk.Scrollbar(log_text_frame, orient="vertical", command=self.log_text.yview)
        log_scroll.grid(row=0, column=1, sticky="ns")
        self.log_text.configure(yscrollcommand=log_scroll.set)

        return log_frame

    def log(self, message: str) -> None:
        if self.log_text is not None:
            self.log_text.insert("end", message + "\n")
            self.log_text.see("end")
        self.status_var.set(message)
        self.root.update_idletasks()

    def _state_payload(self) -> Dict[str, Any]:
        return {
            "excel_path": str(self.excel_path) if self.excel_path else "",
            "images_dir": str(self.images_dir) if self.images_dir else "",
            "default_location": self.default_location_var.get().strip(),
            "profile_name": self.profile_name_var.get().strip() or "default",
            "products": [p.__dict__ for p in self.products],
        }

    def _save_state_file(self) -> None:
        save_state(self._state_payload())

    def _load_state_if_present(self) -> None:
        data = load_state()
        if not data:
            return
        try:
            self.default_location_var.set(data.get("default_location", DEFAULT_LOCATION))
            self.profile_name_var.set(data.get("profile_name", "default"))
            self.refresh_saved_profiles(silent=True)
            self.activate_profile(silent=True)

            if data.get("excel_path"):
                self.excel_path = Path(data["excel_path"])
            if data.get("images_dir"):
                self.images_dir = Path(data["images_dir"])

            self.products = products_from_state(data.get("products", []))
            for product in self.products:
                refresh_product_status(product)

            self.refresh_product_list()
            self.log("Restored previous session.")
        except Exception as exc:
            self.log(f"Could not restore saved session: {exc}")

    def choose_excel(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx *.xls")])
        if path:
            self.excel_path = Path(path)
            self.log(f"Selected Excel file: {self.excel_path}")

    def choose_images_dir(self) -> None:
        path = filedialog.askdirectory()
        if path:
            self.images_dir = Path(path)
            self.log(f"Selected images folder: {self.images_dir}")

    def refresh_saved_profiles(self, silent: bool = False) -> None:
        profiles_root = Path(PROFILES_ROOT)
        profiles_root.mkdir(parents=True, exist_ok=True)
        self.saved_profiles = sorted([p.name for p in profiles_root.iterdir() if p.is_dir()]) or ["default"]

        if self.profile_combo is not None:
            self.profile_combo["values"] = self.saved_profiles

        if not self.profile_name_var.get().strip():
            self.profile_name_var.set(self.saved_profiles[0])

        if not silent:
            self.log(f"Loaded {len(self.saved_profiles)} saved profile(s).")

    def activate_profile(self, silent: bool = False) -> None:
        profile_name = self.profile_name_var.get().strip() or "default"
        profile_name = "".join(c if c.isalnum() or c in "._-" else "_" for c in profile_name)
        self.profile_name_var.set(profile_name)

        profiles_root = Path(PROFILES_ROOT)
        profiles_root.mkdir(parents=True, exist_ok=True)
        profile_path = (profiles_root / profile_name).resolve()
        profile_path.mkdir(parents=True, exist_ok=True)

        self.profile_path_var.set(str(profile_path))
        self.refresh_saved_profiles(silent=True)

        if self.profile_combo is not None:
            self.profile_combo.set(profile_name)

        if not silent:
            self.log(f"Active Facebook profile: {profile_name} -> {profile_path}")

        self._save_state_file()

    def open_profiles_folder(self) -> None:
        profiles_root = Path(PROFILES_ROOT).resolve()
        profiles_root.mkdir(parents=True, exist_ok=True)
        try:
            import subprocess
            import sys

            if sys.platform.startswith("win"):
                os.startfile(str(profiles_root))
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(profiles_root)])
            else:
                subprocess.Popen(["xdg-open", str(profiles_root)])

            self.log(f"Opened profiles folder: {profiles_root}")
        except Exception as exc:
            messagebox.showerror(APP_TITLE, f"Could not open profiles folder: {exc}")

    def load_products(self) -> None:
        if not self.excel_path or not self.images_dir:
            messagebox.showerror(APP_TITLE, "Please choose both the Excel file and the images folder.")
            return

        try:
            self.products = load_products_from_excel(
                self.excel_path,
                self.images_dir,
                self.default_location_var.get().strip(),
            )
            for product in self.products:
                refresh_product_status(product)
            self.refresh_product_list()
            self._save_state_file()
            self.log(f"Loaded {len(self.products)} products.")
        except Exception as exc:
            messagebox.showerror(APP_TITLE, str(exc))

    def _filtered_products_with_index(self) -> List[tuple[int, ProductListing]]:
        rows: List[tuple[int, ProductListing]] = []
        selected_filter = self.filter_var.get()

        for idx, product in enumerate(self.products):
            if selected_filter == "Ready" and product.status != "ready":
                continue
            if selected_filter == "Needs attention" and product.status != "needs attention":
                continue
            if selected_filter == "Posted" and product.status != "posted":
                continue
            rows.append((idx, product))

        return rows

    def refresh_product_list(self) -> None:
        if self.product_list is None:
            return

        self.product_list.delete(0, "end")
        for _, product in self._filtered_products_with_index():
            marker = "[x]" if product.selected else "[ ]"
            self.product_list.insert(
                "end",
                f"{marker} {product.item_number} | {product.title or '(untitled)'} | {product.status}",
            )

    def on_product_selected(self, _event=None) -> None:
        if self.product_list is None:
            return

        selection = self.product_list.curselection()
        if not selection:
            return

        filtered = self._filtered_products_with_index()
        if selection[0] >= len(filtered):
            return

        self.current_index = filtered[selection[0]][0]
        self.load_current_product_into_form()

    def load_current_product_into_form(self) -> None:
        if self.current_index is None or self.description_text is None:
            return

        product = self.products[self.current_index]
        self.item_var.set(product.item_number)
        self.title_var.set(product.title)
        self.total_price_var.set(product.total_price)
        self.down_payment_var.set(product.down_payment_price)
        self.payment_term_var.set(product.payment_term_price)
        self.location_var.set(product.location)
        self.category_var.set(product.category)
        self.condition_var.set(product.condition)
        self.selected_var.set(product.selected)

        self.description_text.delete("1.0", "end")
        self.description_text.insert("1.0", product.description)
        self.refresh_preview()

    def refresh_preview(self) -> None:
        if not all([self.preview_title, self.preview_price, self.preview_location, self.preview_desc]):
            return

        title = self.title_var.get().strip() or "Untitled listing"
        payment_term = self.payment_term_var.get().strip() or "0"
        location = self.location_var.get().strip() or self.default_location_var.get().strip()
        description = self.description_text.get("1.0", "end").strip() if self.description_text else ""
        total_price = self.total_price_var.get().strip()
        down_payment = self.down_payment_var.get().strip()

        self.preview_title.configure(text=title)
        self.preview_price.configure(text=f"${payment_term} / every 2 weeks")
        self.preview_location.configure(text=location)

        details_block = compose_listing_description(description, total_price, down_payment, payment_term)
        self.preview_desc.configure(state="normal")
        self.preview_desc.delete("1.0", "end")
        self.preview_desc.insert("1.0", details_block)
        self.preview_desc.configure(state="disabled")

        if self.current_index is None or self.image_label is None:
            if self.image_label is not None:
                self.image_label.configure(text="No image loaded", image="")
                self.image_label.image = None
            return

        product = self.products[self.current_index]
        if not product.image_paths:
            self.image_label.configure(text="No matching image", image="")
            self.image_label.image = None
            return

        image_path = product.image_paths[0]
        if image_path not in self.thumbnail_cache:
            img = Image.open(image_path).convert("RGB")
            img = ImageOps.contain(img, THUMBNAIL_SIZE)
            self.thumbnail_cache[image_path] = ImageTk.PhotoImage(img)

        photo = self.thumbnail_cache[image_path]
        self.image_label.configure(image=photo, text="")
        self.image_label.image = photo

    def save_current_product(self) -> None:
        if self.current_index is None or self.description_text is None:
            return

        product = self.products[self.current_index]
        product.title = self.title_var.get().strip()
        product.total_price = self.total_price_var.get().strip()
        product.down_payment_price = self.down_payment_var.get().strip()
        product.payment_term_price = self.payment_term_var.get().strip()
        product.location = self.location_var.get().strip()
        product.category = self.category_var.get().strip() or DEFAULT_CATEGORY
        product.condition = self.condition_var.get().strip() or DEFAULT_CONDITION
        product.description = self.description_text.get("1.0", "end").strip()
        product.selected = self.selected_var.get()

        refresh_product_status(product)
        self.refresh_product_list()
        self.refresh_preview()
        self._save_state_file()
        self.log(f"Saved edits for {product.item_number}.")

    def apply_default_location_to_all(self) -> None:
        location = self.default_location_var.get().strip()
        if not location:
            messagebox.showerror(APP_TITLE, "Default location cannot be blank.")
            return

        for product in self.products:
            product.location = location
            refresh_product_status(product)

        self._save_state_file()
        self.refresh_product_list()
        self.load_current_product_into_form()
        self.log(f"Applied location '{location}' to all products.")

    def validate_all(self) -> None:
        for product in self.products:
            refresh_product_status(product)

        self.refresh_product_list()
        self._save_state_file()
        ready = sum(1 for product in self.products if product.ready)
        self.log(f"Validation complete. {ready}/{len(self.products)} products are ready.")

    def generate_ai_for_current(self) -> None:
        if self.current_index is None:
            messagebox.showinfo(APP_TITLE, "Select a product first.")
            return

        self.save_current_product()
        product = self.products[self.current_index]
        self._run_in_thread(lambda: self._generate_ai_worker([product], focus_current=True))

    def generate_ai_for_selected(self) -> None:
        self.save_if_possible()
        selected = [product for product in self.products if product.selected]
        if not selected:
            messagebox.showinfo(APP_TITLE, "No selected products found.")
            return

        self._run_in_thread(lambda: self._generate_ai_worker(selected, focus_current=False))

    def _generate_ai_worker(self, products: List[ProductListing], focus_current: bool) -> None:
        if not self.ai_service.available():
            self._ui(lambda: messagebox.showerror(
                APP_TITLE,
                "AI is not available. Set OPENAI_API_KEY and install the openai package.",
            ))
            return

        for product in products:
            try:
                self._ui(lambda p=product: self.log(f"Generating AI description for {p.item_number}..."))
                product.description = self.ai_service.generate_description(product)
                refresh_product_status(product)
                self._ui(lambda p=product: self.log(f"AI description ready for {p.item_number}."))
            except Exception as exc:
                self._ui(lambda p=product, e=exc: self.log(f"AI generation failed for {p.item_number}: {e}"))

        self._ui(self._after_ai_generation)
        if focus_current:
            self._ui(self.load_current_product_into_form)

    def _after_ai_generation(self) -> None:
        self.refresh_product_list()
        self._save_state_file()

    def post_selected(self) -> None:
        self.save_if_possible()
        products = [product for product in self.products if product.selected and product.ready and product.status != "posted"]
        if not products:
            messagebox.showinfo(APP_TITLE, "There are no selected ready items to post.")
            return

        self._run_in_thread(lambda: self._post_worker(products))

    def post_all_ready(self) -> None:
        self.save_if_possible()
        products = [product for product in self.products if product.ready and product.status != "posted"]
        if not products:
            messagebox.showinfo(APP_TITLE, "There are no ready items to post.")
            return

        self._run_in_thread(lambda: self._post_worker(products))

    def _post_worker(self, products: List[ProductListing]) -> None:
        total = len(products)
        self._ui(lambda: self._set_progress(0, f"Starting 0/{total}"))

        poster = FacebookMarketplacePoster(
            profile_dir=self.profile_path_var.get().strip() or PROFILE_DIR,
            headful=self.headful_var.get(),
            logger=lambda msg: self._ui(lambda m=msg: self.log(m)),
        )

        completed = {"count": 0}

        def on_result(result: UploadResult) -> None:
            for product in self.products:
                if product.item_number == result.item_number:
                    product.status = result.status
                    product.notes = result.message
                    break

            completed["count"] += 1
            percent = (completed["count"] / total) * 100 if total else 0

            self._ui(lambda: self.log(f"{result.item_number}: {result.status} - {result.message}"))
            self._ui(lambda: self._set_progress(percent, f"Posted {completed['count']}/{total}"))
            self._ui(self.refresh_product_list)
            self._ui(self._save_state_file)

        try:
            poster.post_many(products, on_result)
            self._ui(lambda: self._set_progress(100, f"Completed {total}/{total}"))
        except Exception as exc:
            self._ui(lambda: self.log(f"Posting stopped: {exc}"))

    def _set_progress(self, value: float, text: str) -> None:
        self.progress_var.set(value)
        self.progress_text_var.set(text)
        self.root.update_idletasks()

    def _run_in_thread(self, fn: Callable[[], None]) -> None:
        threading.Thread(target=fn, daemon=True).start()

    def _ui(self, fn: Callable[[], None]) -> None:
        self.root.after(0, fn)

    def save_if_possible(self) -> None:
        if self.current_index is not None:
            self.save_current_product()