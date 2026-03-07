from typing import Optional

from pydantic import BaseModel, Field


class SupplierCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    contact_email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None


class SupplierUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    contact_email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None


class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    supplier_id: Optional[str] = None
    description: Optional[str] = None
    price: float = Field(..., ge=0)
    stock: int = Field(default=0, ge=0)


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    supplier_id: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = Field(default=None, ge=0)
    stock: Optional[int] = Field(default=None, ge=0)


class CustomerCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None


class CustomerUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None


class InvoiceCreate(BaseModel):
    customer_id: str
    subtotal: float = Field(..., ge=0)
    tax: float = Field(default=0, ge=0)
    total: float = Field(..., ge=0)
    status: str = Field(default="draft", min_length=1, max_length=30)


class InvoiceUpdate(BaseModel):
    customer_id: Optional[str] = None
    subtotal: Optional[float] = Field(default=None, ge=0)
    tax: Optional[float] = Field(default=None, ge=0)
    total: Optional[float] = Field(default=None, ge=0)
    status: Optional[str] = Field(default=None, min_length=1, max_length=30)


class InvoiceItemCreate(BaseModel):
    invoice_id: str
    product_id: str
    quantity: int = Field(..., gt=0)
    unit_price: float = Field(..., ge=0)


class InvoiceItemUpdate(BaseModel):
    invoice_id: Optional[str] = None
    product_id: Optional[str] = None
    quantity: Optional[int] = Field(default=None, gt=0)
    unit_price: Optional[float] = Field(default=None, ge=0)


class BillingLineItem(BaseModel):
    product_id: str
    quantity: int = Field(..., gt=0)


class BillingInvoiceCreate(BaseModel):
    customer_id: str
    items: list[BillingLineItem] = Field(..., min_items=1)
    tax_rate: float = Field(default=0, ge=0)
