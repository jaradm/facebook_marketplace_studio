import tkinter as tk
from tkinter import ttk


def configure_styles(root: tk.Tk) -> None:
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except Exception:
        pass

    bg = "#eef2f7"
    card = "#f8fafc"
    white = "#ffffff"
    text = "#111827"
    muted = "#475569"
    accent = "#2563eb"
    accent_dark = "#1d4ed8"
    border = "#cbd5e1"

    root.configure(bg=bg)
    style.configure("App.TFrame", background=bg)
    style.configure("Card.TFrame", background=card)
    style.configure("App.TLabel", background=bg, foreground=text, font=("Segoe UI", 10))
    style.configure("Card.TLabel", background=card, foreground=text, font=("Segoe UI", 10))
    style.configure("Muted.TLabel", background=card, foreground=muted, font=("Segoe UI", 9))
    style.configure("CardTitle.TLabel", background=card, foreground=text, font=("Segoe UI", 12, "bold"))
    style.configure("PreviewTitle.TLabel", background=card, foreground=text, font=("Segoe UI", 16, "bold"))
    style.configure("PreviewPrice.TLabel", background=card, foreground=accent, font=("Segoe UI", 13, "bold"))
    style.configure("Primary.TButton", font=("Segoe UI", 10, "bold"), padding=(10, 8), background=accent, foreground="#ffffff", borderwidth=0)
    style.map("Primary.TButton", background=[("active", accent_dark)])
    style.configure("Secondary.TButton", font=("Segoe UI", 10), padding=(10, 8), background=white, foreground=text, borderwidth=1, relief="solid")
    style.map("Secondary.TButton", background=[("active", "#eff6ff")])
    style.configure("Modern.TEntry", fieldbackground=white, foreground=text, insertcolor=text, bordercolor=border, lightcolor=border, darkcolor=border, padding=8)
    style.configure("Modern.TCombobox", fieldbackground=white, background=white, foreground=text, arrowsize=16)
    style.configure("Modern.TCheckbutton", background=bg, foreground=text, font=("Segoe UI", 10))
    style.map("Modern.TCheckbutton", background=[("active", bg)])
    style.configure("Modern.Horizontal.TProgressbar", troughcolor="#dbe4f0", background=accent, bordercolor="#dbe4f0", lightcolor=accent, darkcolor=accent)
