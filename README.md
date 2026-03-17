# Inventory & Billing Manager

Desktop inventory and billing app built with Tkinter for the UI and FastAPI for the local API layer.

## What It Does

- Manage suppliers, products, customers, invoices, and invoice items
- Create billing invoices with automatic stock deduction
- Run as a single desktop app from `run_gui.py`
- Use MongoDB automatically when available
- Fall back to an in-memory demo database when MongoDB is not installed

## Best Option For Your Teacher Demo

On another machine, especially a MacBook, you do not need to install MongoDB just to show the project.

The app now supports:

- `INVENTORY_DB_MODE=auto`: try MongoDB first, then fall back to in-memory demo data
- `INVENTORY_DB_MODE=memory`: always run with seeded demo data
- `INVENTORY_DB_MODE=mongodb`: require a real MongoDB connection

For a presentation, use `memory` mode so the app always opens with sample data.

## macOS Setup

1. Install Python 3.11+.
2. Open Terminal in the project folder.
3. Create and activate a virtual environment.
4. Install dependencies.
5. Run the GUI.

Commands:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export INVENTORY_DB_MODE=memory
python run_gui.py
```

If your Mac Python does not include Tkinter, install Python from python.org and recreate the virtual environment. The app depends on Tkinter for the desktop window.

## Windows Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:INVENTORY_DB_MODE="memory"
python run_gui.py
```

## Optional MongoDB Mode

If you want to use a real database instead of demo mode, create a `.env` file from `.env.example` and set:

```text
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB=inventory_billing_db
INVENTORY_DB_MODE=mongodb
INVENTORY_DEMO_SEED=true
```

Then start the app normally:

```bash
python run_gui.py
```

## Project Structure

```text
.
├── app/
│   ├── config.py
│   ├── database.py
│   ├── gui.py
│   ├── main.py
│   ├── schemas.py
│   └── utils.py
├── run_gui.py
├── requirements.txt
└── README.md
```

## Presentation Notes

- In demo mode, the app opens with sample suppliers, products, customers, invoices, and invoice items.
- The status bar shows whether you are using MongoDB or the in-memory demo backend.
- The GUI starts the local API automatically, so only `python run_gui.py` is needed.
