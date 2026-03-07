# InventoryProject

Simple Inventory + Billing CRUD API built with Python, FastAPI, and MongoDB.

## Features

- CRUD operations for **5 MongoDB collections**:
`suppliers`, `products`, `customers`, `invoices`, `invoice_items`
- Billing endpoint to create an invoice from product line items
- Automatic stock deduction during billing
- Basic duplicate protections with MongoDB indexes

## Tech Stack

- Python
- FastAPI
- PyMongo
- MongoDB

## Project Structure

```text
.
├── app
│   ├── __init__.py
│   ├── config.py
│   ├── database.py
│   ├── main.py
│   ├── schemas.py
│   └── utils.py
├── .env.example
├── .gitignore
├── README.md
└── requirements.txt
```

## Setup

1. Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Copy environment file and edit values if needed:

```bash
cp .env.example .env
```

4. Ensure MongoDB is running (default URI in `.env.example`):

```text
mongodb://localhost:27017
```

5. Run API server:

```bash
uvicorn app.main:app --reload
```

6. Open docs:

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## API Endpoints

### Suppliers

- `POST /suppliers`
- `GET /suppliers`
- `GET /suppliers/{supplier_id}`
- `PUT /suppliers/{supplier_id}`
- `DELETE /suppliers/{supplier_id}`

### Products

- `POST /products`
- `GET /products`
- `GET /products/{product_id}`
- `PUT /products/{product_id}`
- `DELETE /products/{product_id}`

### Customers

- `POST /customers`
- `GET /customers`
- `GET /customers/{customer_id}`
- `PUT /customers/{customer_id}`
- `DELETE /customers/{customer_id}`

### Invoices

- `POST /invoices`
- `GET /invoices`
- `GET /invoices/{invoice_id}`
- `PUT /invoices/{invoice_id}`
- `DELETE /invoices/{invoice_id}`

### Invoice Items

- `POST /invoice-items`
- `GET /invoice-items`
- `GET /invoice-items/{invoice_item_id}`
- `PUT /invoice-items/{invoice_item_id}`
- `DELETE /invoice-items/{invoice_item_id}`

### Billing Workflow

- `POST /billing/invoices`

Creates an invoice from product lines, inserts invoice items, and decreases stock.

## Example Billing Request

```bash
curl -X POST "http://127.0.0.1:8000/billing/invoices" \
	-H "Content-Type: application/json" \
	-d '{
		"customer_id": "CUSTOMER_OBJECT_ID",
		"tax_rate": 0.05,
		"items": [
			{"product_id": "PRODUCT_OBJECT_ID_1", "quantity": 2},
			{"product_id": "PRODUCT_OBJECT_ID_2", "quantity": 1}
		]
	}'
```

## Notes

- MongoDB uses collections, which are the equivalent of SQL tables.
- This project is intentionally simple and does not implement auth.
