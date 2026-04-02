# Facebook Marketplace Studio

A powerful desktop application that helps you **bulk create, preview, edit, and post product listings to Facebook Marketplace** using an Excel file and product images.

---

## 🚀 Features

### 📦 Bulk Product Import
- Import products from an Excel file
- Automatically matches images to products using Item Number / SKU

### 🖼️ Smart Image Matching
- Matches images like:
  - `123.jpg`
  - `123_1.jpg`
  - `123-2.png`

### 🧠 AI Description Generator
- Uses AI to analyze product images
- Generates clean, marketplace-ready descriptions
- Automatically includes:
  - Delivery included messaging
  - Clean, realistic descriptions (no fake specs)

### 🛠️ Full Editing UI
- Edit everything before posting:
  - Title
  - Description
  - Total Price
  - Down Payment
  - Payment Term (bi-weekly)
  - Location
  - Category
  - Condition

### 👀 Live Listing Preview
- See exactly how your listing will look before posting
- Includes:
  - Image preview
  - Title
  - Payment display
  - Full formatted description

### 📊 Payment-Based Pricing
- Designed for installment-style selling
- Automatically formats:
  - Total price
  - Down payment
  - Payment every 2 weeks

### 📈 Progress Tracking
- Visual progress bar while posting
- Shows:
  - Number of items posted
  - Completion status

### 👤 Multiple Facebook Profiles
- Save multiple login sessions
- Easily switch between accounts

### 💾 Auto Save
- Automatically saves your session
- Resume where you left off

---

## 📁 Project Structure

```
facebook_marketplace_studio/
│
├─ main.py                 # App entry point
├─ ui.py                   # Main UI (Tkinter)
├─ models.py               # Data models
├─ config.py               # App configuration
├─ styles.py               # UI styling
│
├─ services/
│   ├─ excel_loader.py     # Reads Excel files
│   ├─ image_matcher.py    # Matches images to products
│   ├─ ai_service.py       # AI description generator
│   ├─ facebook_poster.py  # Facebook automation
│   ├─ state_manager.py    # Save/load state
│   └─ utils.py            # Shared helpers
│
├─ requirements.txt
└─ README.md
```

---

## ⚙️ Installation

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Install Playwright browser

```bash
playwright install chromium
```

---

## 🔑 Optional: AI Setup

If you want AI-generated descriptions:

### Windows CMD
```bash
set OPENAI_API_KEY=your_api_key_here
```

### PowerShell
```bash
$env:OPENAI_API_KEY="your_api_key_here"
```

---

## ▶️ Running the App

```bash
python main.py
```

---

## 📊 Excel Format

Your Excel file should include these columns:

| Column Name           | Description |
|----------------------|------------|
| ItemNumber           | Unique ID (used to match images) |
| ProductName          | Product title |
| Description          | Base description |
| Total Price          | Full price |
| Down Payment Price   | Initial payment |
| Payment Term Price   | Bi-weekly payment |

---

## 🖼️ Image Requirements

Images must be named using the Item Number:

```
123.jpg
123_1.jpg
123-2.png
```

---

## 🧭 How It Works

1. Load your Excel file
2. Select your images folder
3. Click **Load Products**
4. Review each product
5. Edit details if needed
6. (Optional) Generate AI descriptions
7. Click **Post Selected** or **Post All Ready**

---

## ⚠️ Important Notes

- First time posting will open a browser
- You must log into Facebook manually once
- Session is saved for future use
- Facebook UI changes may occasionally break automation

---

## 🧠 Design Philosophy

This app is built to:
- Save hours of manual listing work
- Reduce human error
- Allow full control before posting
- Scale Marketplace listings efficiently

---

## 🔮 Future Improvements

- Thumbnail product grid view
- Error retry system
- Auto pricing rules
- Multi-platform posting (OfferUp, Craigslist, etc.)

---

## 📄 License

This project is provided as-is for personal and business use.

---

## 💡 Tip

Start by testing with 1–2 products before bulk posting.

---

If you want help customizing or expanding this tool, feel free to ask.

