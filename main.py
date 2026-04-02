import logging
import tkinter as tk

from styles import configure_styles
from ui import MarketplaceStudioApp


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    root = tk.Tk()
    configure_styles(root)
    MarketplaceStudioApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
