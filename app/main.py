from collections import defaultdict
from typing import Any

from bson import ObjectId
from fastapi import FastAPI, HTTPException, status
from pymongo.collection import Collection
from pymongo.errors import DuplicateKeyError

from app.database import db, init_indexes, verify_connection
from app.schemas import (
    BillingInvoiceCreate,
    CustomerCreate,
    CustomerUpdate,
    InvoiceCreate,
    InvoiceItemCreate,
    InvoiceItemUpdate,
    InvoiceUpdate,
    ProductCreate,
    ProductUpdate,
    SupplierCreate,
    SupplierUpdate,
)
from app.utils import generate_barcode, model_to_dict, now_utc, parse_object_id, serialize_document, serialize_documents

app = FastAPI(title="Inventory + Billing API", version="1.0.0")

suppliers_col: Collection = db["suppliers"]
products_col: Collection = db["products"]
customers_col: Collection = db["customers"]
invoices_col: Collection = db["invoices"]
invoice_items_col: Collection = db["invoice_items"]


@app.on_event("startup")
def startup_event() -> None:
    verify_connection()
    init_indexes()


@app.get("/")
def health() -> dict[str, str]:
    return {"message": "Inventory + Billing API is running"}


def _ensure_exists(collection: Collection, oid: ObjectId, name: str) -> None:
    if not collection.find_one({"_id": oid}):
        raise HTTPException(status_code=404, detail=f"{name} not found")


def _get_or_404(collection: Collection, doc_id: str, name: str) -> tuple[ObjectId, dict[str, Any]]:
    oid = parse_object_id(doc_id)
    doc = collection.find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=404, detail=f"{name} not found")
    return oid, doc


# ─────────────────────────────────────────────────────────────────────────────
# SUPPLIERS CRUD
# MongoDB shell equivalents shown in each function
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/suppliers", status_code=status.HTTP_201_CREATED)
def create_supplier(payload: SupplierCreate) -> dict[str, Any]:
    # MongoDB shell:
    # db.suppliers.insertOne({
    #   name: "ABC Electronics",
    #   contact_email: "abc@email.com",
    #   phone: "9876543210",
    #   address: "Dubai, UAE",
    #   created_at: ISODate("2026-03-07T10:00:00Z"),
    #   updated_at: ISODate("2026-03-07T10:00:00Z")
    # })
    now = now_utc()
    data = model_to_dict(payload)
    data["created_at"] = now
    data["updated_at"] = now

    result = suppliers_col.insert_one(data)
    created = suppliers_col.find_one({"_id": result.inserted_id})
    return serialize_document(created)


@app.get("/suppliers")
def list_suppliers() -> list[dict[str, Any]]:
    # MongoDB shell:
    # db.suppliers.find().sort({ created_at: -1 })
    docs = list(suppliers_col.find().sort("created_at", -1))
    return serialize_documents(docs)


@app.get("/suppliers/{supplier_id}")
def get_supplier(supplier_id: str) -> dict[str, Any]:
    # MongoDB shell:
    # db.suppliers.findOne({ _id: ObjectId("<supplier_id>") })
    _, doc = _get_or_404(suppliers_col, supplier_id, "Supplier")
    return serialize_document(doc)


@app.put("/suppliers/{supplier_id}")
def update_supplier(supplier_id: str, payload: SupplierUpdate) -> dict[str, Any]:
    # MongoDB shell:
    # db.suppliers.updateOne(
    #   { _id: ObjectId("<supplier_id>") },
    #   { $set: { name: "New Name", updated_at: ISODate("...") } }
    # )
    supplier_oid, _ = _get_or_404(suppliers_col, supplier_id, "Supplier")
    updates = model_to_dict(payload, exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields provided for update")

    updates["updated_at"] = now_utc()
    suppliers_col.update_one({"_id": supplier_oid}, {"$set": updates})
    updated = suppliers_col.find_one({"_id": supplier_oid})
    return serialize_document(updated)


@app.delete("/suppliers/{supplier_id}")
def delete_supplier(supplier_id: str) -> dict[str, str]:
    # MongoDB shell:
    # db.suppliers.deleteOne({ _id: ObjectId("<supplier_id>") })
    # Guard: cannot delete if linked products exist:
    # db.products.findOne({ supplier_id: ObjectId("<supplier_id>") })
    supplier_oid, _ = _get_or_404(suppliers_col, supplier_id, "Supplier")

    if products_col.find_one({"supplier_id": supplier_oid}):
        raise HTTPException(status_code=409, detail="Cannot delete supplier linked to products")

    suppliers_col.delete_one({"_id": supplier_oid})
    return {"message": "Supplier deleted"}


# ─────────────────────────────────────────────────────────────────────────────
# PRODUCTS CRUD
# MongoDB shell equivalents shown in each function
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/products", status_code=status.HTTP_201_CREATED)
def create_product(payload: ProductCreate) -> dict[str, Any]:
    # Barcode is auto-generated (EAN-13): no user input needed.
    # MongoDB shell:
    # db.products.insertOne({
    #   name: "Laptop Dell XPS",
    #   barcode: "4901234567890",   // auto-generated EAN-13
    #   price: 1299.99,
    #   stock: 50,
    #   supplier_id: ObjectId("<supplier_id>"),
    #   description: "15-inch laptop",
    #   created_at: ISODate("2026-03-07T10:00:00Z"),
    #   updated_at: ISODate("2026-03-07T10:00:00Z")
    # })
    data = model_to_dict(payload)
    supplier_id = data.get("supplier_id")
    if supplier_id:
        supplier_oid = parse_object_id(supplier_id)
        _ensure_exists(suppliers_col, supplier_oid, "Supplier")
        data["supplier_id"] = supplier_oid

    # Auto-generate a unique EAN-13 barcode
    for _ in range(10):  # retry on the rare collision
        barcode = generate_barcode()
        if not products_col.find_one({"barcode": barcode}):
            data["barcode"] = barcode
            break
    else:
        raise HTTPException(status_code=500, detail="Could not generate a unique barcode")

    now = now_utc()
    data["created_at"] = now
    data["updated_at"] = now

    result = products_col.insert_one(data)
    created = products_col.find_one({"_id": result.inserted_id})
    return serialize_document(created)


@app.get("/products")
def list_products() -> list[dict[str, Any]]:
    # MongoDB shell:
    # db.products.find().sort({ created_at: -1 })
    docs = list(products_col.find().sort("created_at", -1))
    return serialize_documents(docs)


@app.get("/products/{product_id}")
def get_product(product_id: str) -> dict[str, Any]:
    # MongoDB shell:
    # db.products.findOne({ _id: ObjectId("<product_id>") })
    _, doc = _get_or_404(products_col, product_id, "Product")
    return serialize_document(doc)


@app.put("/products/{product_id}")
def update_product(product_id: str, payload: ProductUpdate) -> dict[str, Any]:
    # MongoDB shell:
    # db.products.updateOne(
    #   { _id: ObjectId("<product_id>") },
    #   { $set: { name: "New Name", price: 999.99, updated_at: ISODate("...") } }
    # )
    product_oid, _ = _get_or_404(products_col, product_id, "Product")
    updates = model_to_dict(payload, exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields provided for update")

    if "supplier_id" in updates and updates["supplier_id"]:
        supplier_oid = parse_object_id(updates["supplier_id"])
        _ensure_exists(suppliers_col, supplier_oid, "Supplier")
        updates["supplier_id"] = supplier_oid

    updates["updated_at"] = now_utc()
    products_col.update_one({"_id": product_oid}, {"$set": updates})
    updated = products_col.find_one({"_id": product_oid})
    return serialize_document(updated)


@app.delete("/products/{product_id}")
def delete_product(product_id: str) -> dict[str, str]:
    # MongoDB shell:
    # db.products.deleteOne({ _id: ObjectId("<product_id>") })
    # Guard: cannot delete if used in any invoice item:
    # db.invoice_items.findOne({ product_id: ObjectId("<product_id>") })
    product_oid, _ = _get_or_404(products_col, product_id, "Product")

    if invoice_items_col.find_one({"product_id": product_oid}):
        raise HTTPException(status_code=409, detail="Cannot delete product used in invoice items")

    products_col.delete_one({"_id": product_oid})
    return {"message": "Product deleted"}


# ─────────────────────────────────────────────────────────────────────────────
# CUSTOMERS CRUD
# MongoDB shell equivalents shown in each function
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/customers", status_code=status.HTTP_201_CREATED)
def create_customer(payload: CustomerCreate) -> dict[str, Any]:
    # MongoDB shell:
    # db.customers.insertOne({
    #   name: "John Smith",
    #   email: "john@gmail.com",   // sparse unique index — duplicates rejected
    #   phone: "0501234567",
    #   address: "Abu Dhabi, UAE",
    #   created_at: ISODate("2026-03-07T10:00:00Z"),
    #   updated_at: ISODate("2026-03-07T10:00:00Z")
    # })
    now = now_utc()
    data = model_to_dict(payload)
    data["created_at"] = now
    data["updated_at"] = now

    try:
        result = customers_col.insert_one(data)
    except DuplicateKeyError as exc:
        raise HTTPException(status_code=409, detail="Email already exists") from exc

    created = customers_col.find_one({"_id": result.inserted_id})
    return serialize_document(created)


@app.get("/customers")
def list_customers() -> list[dict[str, Any]]:
    # MongoDB shell:
    # db.customers.find().sort({ created_at: -1 })
    docs = list(customers_col.find().sort("created_at", -1))
    return serialize_documents(docs)


@app.get("/customers/{customer_id}")
def get_customer(customer_id: str) -> dict[str, Any]:
    # MongoDB shell:
    # db.customers.findOne({ _id: ObjectId("<customer_id>") })
    _, doc = _get_or_404(customers_col, customer_id, "Customer")
    return serialize_document(doc)


@app.put("/customers/{customer_id}")
def update_customer(customer_id: str, payload: CustomerUpdate) -> dict[str, Any]:
    # MongoDB shell:
    # db.customers.updateOne(
    #   { _id: ObjectId("<customer_id>") },
    #   { $set: { phone: "0509999999", updated_at: ISODate("...") } }
    # )
    customer_oid, _ = _get_or_404(customers_col, customer_id, "Customer")
    updates = model_to_dict(payload, exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields provided for update")

    updates["updated_at"] = now_utc()

    try:
        customers_col.update_one({"_id": customer_oid}, {"$set": updates})
    except DuplicateKeyError as exc:
        raise HTTPException(status_code=409, detail="Email already exists") from exc

    updated = customers_col.find_one({"_id": customer_oid})
    return serialize_document(updated)


@app.delete("/customers/{customer_id}")
def delete_customer(customer_id: str) -> dict[str, str]:
    # MongoDB shell:
    # db.customers.deleteOne({ _id: ObjectId("<customer_id>") })
    # Guard: cannot delete if they have invoices:
    # db.invoices.findOne({ customer_id: ObjectId("<customer_id>") })
    customer_oid, _ = _get_or_404(customers_col, customer_id, "Customer")

    if invoices_col.find_one({"customer_id": customer_oid}):
        raise HTTPException(status_code=409, detail="Cannot delete customer with existing invoices")

    customers_col.delete_one({"_id": customer_oid})
    return {"message": "Customer deleted"}


# ─────────────────────────────────────────────────────────────────────────────
# INVOICES CRUD
# MongoDB shell equivalents shown in each function
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/invoices", status_code=status.HTTP_201_CREATED)
def create_invoice(payload: InvoiceCreate) -> dict[str, Any]:
    # MongoDB shell:
    # db.invoices.insertOne({
    #   customer_id: ObjectId("<customer_id>"),  // indexed foreign key
    #   subtotal: 1299.99,
    #   tax: 65.00,
    #   total: 1364.99,
    #   status: "draft",
    #   line_item_ids: [],
    #   created_at: ISODate("2026-03-07T10:00:00Z"),
    #   updated_at: ISODate("2026-03-07T10:00:00Z")
    # })
    data = model_to_dict(payload)
    customer_oid = parse_object_id(data["customer_id"])
    _ensure_exists(customers_col, customer_oid, "Customer")
    data["customer_id"] = customer_oid

    now = now_utc()
    data["created_at"] = now
    data["updated_at"] = now
    data.setdefault("line_item_ids", [])

    result = invoices_col.insert_one(data)
    created = invoices_col.find_one({"_id": result.inserted_id})
    return serialize_document(created)


@app.get("/invoices")
def list_invoices() -> list[dict[str, Any]]:
    # MongoDB shell:
    # db.invoices.find().sort({ created_at: -1 })
    docs = list(invoices_col.find().sort("created_at", -1))
    return serialize_documents(docs)


@app.get("/invoices/{invoice_id}")
def get_invoice(invoice_id: str) -> dict[str, Any]:
    # MongoDB shell (invoice + its items):
    # db.invoices.findOne({ _id: ObjectId("<invoice_id>") })
    # db.invoice_items.find({ invoice_id: ObjectId("<invoice_id>") }).sort({ created_at: 1 })
    invoice_oid, doc = _get_or_404(invoices_col, invoice_id, "Invoice")
    items = list(invoice_items_col.find({"invoice_id": invoice_oid}).sort("created_at", 1))
    return {"invoice": serialize_document(doc), "items": serialize_documents(items)}


@app.put("/invoices/{invoice_id}")
def update_invoice(invoice_id: str, payload: InvoiceUpdate) -> dict[str, Any]:
    # MongoDB shell:
    # db.invoices.updateOne(
    #   { _id: ObjectId("<invoice_id>") },
    #   { $set: { status: "paid", updated_at: ISODate("...") } }
    # )
    invoice_oid, _ = _get_or_404(invoices_col, invoice_id, "Invoice")
    updates = model_to_dict(payload, exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields provided for update")

    if "customer_id" in updates and updates["customer_id"]:
        customer_oid = parse_object_id(updates["customer_id"])
        _ensure_exists(customers_col, customer_oid, "Customer")
        updates["customer_id"] = customer_oid

    updates["updated_at"] = now_utc()

    invoices_col.update_one({"_id": invoice_oid}, {"$set": updates})
    updated = invoices_col.find_one({"_id": invoice_oid})
    return serialize_document(updated)


@app.delete("/invoices/{invoice_id}")
def delete_invoice(invoice_id: str) -> dict[str, str]:
    # MongoDB shell (cascade delete — items first, then invoice):
    # db.invoice_items.deleteMany({ invoice_id: ObjectId("<invoice_id>") })
    # db.invoices.deleteOne({ _id: ObjectId("<invoice_id>") })
    invoice_oid, _ = _get_or_404(invoices_col, invoice_id, "Invoice")
    invoice_items_col.delete_many({"invoice_id": invoice_oid})
    invoices_col.delete_one({"_id": invoice_oid})
    return {"message": "Invoice and related invoice items deleted"}


# ─────────────────────────────────────────────────────────────────────────────
# INVOICE ITEMS CRUD
# MongoDB shell equivalents shown in each function
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/invoice-items", status_code=status.HTTP_201_CREATED)
def create_invoice_item(payload: InvoiceItemCreate) -> dict[str, Any]:
    # MongoDB shell:
    # db.invoice_items.insertOne({
    #   invoice_id: ObjectId("<invoice_id>"),   // indexed foreign key
    #   product_id: ObjectId("<product_id>"),   // indexed foreign key
    #   quantity: 2,
    #   unit_price: 1299.99,
    #   line_total: 2599.98,    // computed: quantity * unit_price
    #   created_at: ISODate("2026-03-07T10:00:00Z"),
    #   updated_at: ISODate("2026-03-07T10:00:00Z")
    # })
    data = model_to_dict(payload)

    invoice_oid = parse_object_id(data["invoice_id"])
    product_oid = parse_object_id(data["product_id"])
    _ensure_exists(invoices_col, invoice_oid, "Invoice")
    _ensure_exists(products_col, product_oid, "Product")

    quantity = data["quantity"]
    unit_price = data["unit_price"]

    data["invoice_id"] = invoice_oid
    data["product_id"] = product_oid
    data["line_total"] = round(quantity * unit_price, 2)

    now = now_utc()
    data["created_at"] = now
    data["updated_at"] = now

    result = invoice_items_col.insert_one(data)
    created = invoice_items_col.find_one({"_id": result.inserted_id})
    return serialize_document(created)


@app.get("/invoice-items")
def list_invoice_items() -> list[dict[str, Any]]:
    # MongoDB shell:
    # db.invoice_items.find().sort({ created_at: -1 })
    docs = list(invoice_items_col.find().sort("created_at", -1))
    return serialize_documents(docs)


@app.get("/invoice-items/{invoice_item_id}")
def get_invoice_item(invoice_item_id: str) -> dict[str, Any]:
    # MongoDB shell:
    # db.invoice_items.findOne({ _id: ObjectId("<invoice_item_id>") })
    _, doc = _get_or_404(invoice_items_col, invoice_item_id, "Invoice item")
    return serialize_document(doc)


@app.put("/invoice-items/{invoice_item_id}")
def update_invoice_item(invoice_item_id: str, payload: InvoiceItemUpdate) -> dict[str, Any]:
    invoice_item_oid, existing = _get_or_404(invoice_items_col, invoice_item_id, "Invoice item")
    updates = model_to_dict(payload, exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields provided for update")

    if "invoice_id" in updates and updates["invoice_id"]:
        invoice_oid = parse_object_id(updates["invoice_id"])
        _ensure_exists(invoices_col, invoice_oid, "Invoice")
        updates["invoice_id"] = invoice_oid

    if "product_id" in updates and updates["product_id"]:
        product_oid = parse_object_id(updates["product_id"])
        _ensure_exists(products_col, product_oid, "Product")
        updates["product_id"] = product_oid

    effective_quantity = updates.get("quantity", existing["quantity"])
    effective_unit_price = updates.get("unit_price", existing["unit_price"])
    updates["line_total"] = round(effective_quantity * effective_unit_price, 2)
    updates["updated_at"] = now_utc()

    invoice_items_col.update_one({"_id": invoice_item_oid}, {"$set": updates})
    updated = invoice_items_col.find_one({"_id": invoice_item_oid})
    return serialize_document(updated)


@app.delete("/invoice-items/{invoice_item_id}")
def delete_invoice_item(invoice_item_id: str) -> dict[str, str]:
    invoice_item_oid, _ = _get_or_404(invoice_items_col, invoice_item_id, "Invoice item")
    invoice_items_col.delete_one({"_id": invoice_item_oid})
    return {"message": "Invoice item deleted"}


# ─────────────────────────────────────────────────────────────────────────────
# BILLING FLOW  — most important route
# Creates an invoice + all items + decrements stock atomically.
# MongoDB shell equivalents (all 3 steps happen in one API call):
#
# Step 1 — Insert the invoice:
# db.invoices.insertOne({
#   customer_id: ObjectId("<customer_id>"),
#   subtotal: 1299.99, tax: 65.00, total: 1364.99,
#   status: "issued", line_item_ids: [],
#   created_at: ISODate("..."), updated_at: ISODate("...")
# })
#
# Step 2 — Insert all line items at once:
# db.invoice_items.insertMany([
#   { invoice_id: ObjectId("<inv_id>"), product_id: ObjectId("<prod_id>"),
#     quantity: 1, unit_price: 1299.99, line_total: 1299.99,
#     created_at: ISODate("..."), updated_at: ISODate("...") }
# ])
#
# Step 3 — Decrement stock using $inc (atomic — no race condition):
# db.products.updateOne(
#   { _id: ObjectId("<product_id>"), stock: { $gte: 1 } },  // safety check
#   { $inc: { stock: -1 }, $set: { updated_at: ISODate("...") } }
# )
#
# On ANY error → full manual rollback:
#   $inc stock back (+qty), deleteMany items, deleteOne invoice
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/billing/invoices", status_code=status.HTTP_201_CREATED)
def create_billing_invoice(payload: BillingInvoiceCreate) -> dict[str, Any]:
    customer_oid = parse_object_id(payload.customer_id)
    _ensure_exists(customers_col, customer_oid, "Customer")

    requested_qty: defaultdict[ObjectId, int] = defaultdict(int)
    ordered_product_ids: list[ObjectId] = []

    for line in payload.items:
        product_oid = parse_object_id(line.product_id)
        requested_qty[product_oid] += line.quantity
        ordered_product_ids.append(product_oid)

    product_map: dict[ObjectId, dict[str, Any]] = {}
    for product_oid, total_qty in requested_qty.items():
        product = products_col.find_one({"_id": product_oid})
        if not product:
            raise HTTPException(status_code=404, detail=f"Product not found: {product_oid}")
        if product.get("stock", 0) < total_qty:
            raise HTTPException(
                status_code=409,
                detail=f"Insufficient stock for product {product.get('name', str(product_oid))}",
            )
        product_map[product_oid] = product

    subtotal = 0.0
    line_item_docs: list[dict[str, Any]] = []
    now = now_utc()

    for idx, line in enumerate(payload.items):
        product_oid = ordered_product_ids[idx]
        product = product_map[product_oid]
        quantity = line.quantity
        unit_price = float(product.get("price", 0))
        line_total = round(quantity * unit_price, 2)

        subtotal += line_total
        line_item_docs.append(
            {
                "invoice_id": None,
                "product_id": product_oid,
                "quantity": quantity,
                "unit_price": unit_price,
                "line_total": line_total,
                "created_at": now,
                "updated_at": now,
            }
        )

    subtotal = round(subtotal, 2)
    tax = round(subtotal * payload.tax_rate, 2)
    total = round(subtotal + tax, 2)

    invoice_doc = {
        "customer_id": customer_oid,
        "subtotal": subtotal,
        "tax": tax,
        "total": total,
        "status": "issued",
        "line_item_ids": [],
        "created_at": now,
        "updated_at": now,
    }

    invoice_id: ObjectId | None = None
    inserted_item_ids: list[ObjectId] = []
    decremented: list[tuple[ObjectId, int]] = []

    try:
        invoice_result = invoices_col.insert_one(invoice_doc)
        invoice_id = invoice_result.inserted_id

        for line_item_doc in line_item_docs:
            line_item_doc["invoice_id"] = invoice_id

        if line_item_docs:
            insert_items_result = invoice_items_col.insert_many(line_item_docs)
            inserted_item_ids = list(insert_items_result.inserted_ids)

        for product_oid, total_qty in requested_qty.items():
            updated = products_col.update_one(
                {"_id": product_oid, "stock": {"$gte": total_qty}},
                {"$inc": {"stock": -total_qty}, "$set": {"updated_at": now_utc()}},
            )
            if updated.modified_count == 0:
                raise HTTPException(
                    status_code=409,
                    detail=f"Stock changed while billing for product {product_oid}",
                )
            decremented.append((product_oid, total_qty))

        invoices_col.update_one(
            {"_id": invoice_id},
            {"$set": {"line_item_ids": inserted_item_ids, "updated_at": now_utc()}},
        )
    except HTTPException:
        for product_oid, qty in decremented:
            products_col.update_one(
                {"_id": product_oid},
                {"$inc": {"stock": qty}, "$set": {"updated_at": now_utc()}},
            )
        if inserted_item_ids:
            invoice_items_col.delete_many({"_id": {"$in": inserted_item_ids}})
        if invoice_id:
            invoices_col.delete_one({"_id": invoice_id})
        raise
    except Exception as exc:
        for product_oid, qty in decremented:
            products_col.update_one(
                {"_id": product_oid},
                {"$inc": {"stock": qty}, "$set": {"updated_at": now_utc()}},
            )
        if inserted_item_ids:
            invoice_items_col.delete_many({"_id": {"$in": inserted_item_ids}})
        if invoice_id:
            invoices_col.delete_one({"_id": invoice_id})
        raise HTTPException(status_code=500, detail="Failed to create billing invoice") from exc

    created_invoice = invoices_col.find_one({"_id": invoice_id})
    created_items = list(invoice_items_col.find({"invoice_id": invoice_id}).sort("created_at", 1))
    return {"invoice": serialize_document(created_invoice), "items": serialize_documents(created_items)}
