from pymongo import MongoClient

from app.config import MONGODB_DB, MONGODB_URI

client = MongoClient(MONGODB_URI)
db = client[MONGODB_DB]


def init_indexes() -> None:
    db.products.create_index("barcode", unique=True)
    db.customers.create_index("email", unique=True, sparse=True)
    db.invoices.create_index("customer_id")
    db.invoice_items.create_index("invoice_id")
    db.invoice_items.create_index("product_id")
