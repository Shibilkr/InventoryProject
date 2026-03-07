"""
show_db.py  —  Run this to display all MongoDB collections to your teacher.

Usage:
    python show_db.py

Make sure MongoDB is running before you run this.
"""

import json
from datetime import datetime

from bson import ObjectId
from pymongo import MongoClient

from app.config import MONGODB_DB, MONGODB_URI

# ── Connect ──────────────────────────────────────────────────────────────────
client = MongoClient(MONGODB_URI)
db     = client[MONGODB_DB]

SEP   = "─" * 72
THICK = "═" * 72


def fmt(val):
    """Convert BSON types to readable strings."""
    if isinstance(val, ObjectId):
        return str(val)
    if isinstance(val, datetime):
        return val.strftime("%Y-%m-%d %H:%M:%S UTC")
    if isinstance(val, list):
        return [fmt(v) for v in val]
    if isinstance(val, dict):
        return {k: fmt(v) for k, v in val.items()}
    return val


def show_collection(name: str, label: str, icon: str) -> None:
    col   = db[name]
    docs  = list(col.find().sort("created_at", -1))
    count = len(docs)

    print(f"\n{THICK}")
    print(f"  {icon}  {label.upper()}   ({count} document{'s' if count != 1 else ''})")
    print(f"  Collection: db.{name}")
    print(THICK)

    # Show index info
    indexes = list(col.index_information().values())
    idx_names = []
    for i in indexes:
        key_field = i['key'][0][0] if isinstance(i['key'], list) else list(i['key'].keys())[0]
        if key_field == '_id':
            continue
        kind = 'unique' if i.get('unique') else 'index'
        sparse = ' + sparse' if i.get('sparse') else ''
        idx_names.append(f"{key_field} ({kind}{sparse})")
    if idx_names:
        print(f"  Indexes: {', '.join(idx_names)}")
    print(SEP)

    if not docs:
        print("  (no documents yet)")
        return

    for i, doc in enumerate(docs, 1):
        print(f"  Document #{i}")
        clean = fmt(dict(doc))
        for key, val in clean.items():
            if isinstance(val, list) and len(val) > 3:
                val = val[:3] + [f"... +{len(val)-3} more"]
            print(f"    {key:20s}: {val}")
        if i < count:
            print(f"  {SEP}")


def show_connection() -> None:
    print(f"\n{THICK}")
    print("  🔌  DATABASE CONNECTION")
    print(THICK)
    print(f"  URI             : {MONGODB_URI}")
    print(f"  Database name   : {MONGODB_DB}")
    print(f"  PyMongo version : ", end="")
    import pymongo
    print(pymongo.version)
    print(f"  Connection type : MongoClient (connection pool)")

    # Ping the server
    try:
        client.admin.command("ping")
        print("  Status          : ✅  Connected successfully")
    except Exception as exc:
        print(f"  Status          : ❌  {exc}")
    print(SEP)

    # Show all collections + document counts
    print("\n  Collections in this database:")
    for cname in ["suppliers", "products", "customers", "invoices", "invoice_items"]:
        n = db[cname].count_documents({})
        print(f"    db.{cname:20s}  →  {n} document{'s' if n != 1 else ''}")

    # Show all indexes
    print("\n  Indexes created by init_indexes():")
    index_map = {
        "products":      "barcode (unique)",
        "customers":     "email (unique + sparse)",
        "invoices":      "customer_id",
        "invoice_items": "invoice_id, product_id",
    }
    for col, idx in index_map.items():
        print(f"    db.{col:20s}  →  {idx}")


def main() -> None:
    print(THICK)
    print("  📦  INVENTORY & BILLING — MONGODB DATABASE VIEWER")
    print(f"  Showing live data from: {MONGODB_DB}")
    print(THICK)

    show_connection()

    show_collection("suppliers",     "Suppliers",     "🏭")
    show_collection("products",      "Products",      "📦")
    show_collection("customers",     "Customers",     "👤")
    show_collection("invoices",      "Invoices",      "📄")
    show_collection("invoice_items", "Invoice Items", "🔖")

    print(f"\n{THICK}")
    print("  ✅  Done.  All collections displayed above.")
    print(THICK)


if __name__ == "__main__":
    main()
