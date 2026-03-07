"""
Inventory & Billing Manager — Desktop GUI  (v2 — Modern Redesign)
=================================================================
* Sidebar navigation  (Dashboard · Suppliers · Products · Customers ·
                        Invoices · Invoice Items · Billing)
* Dashboard with live stat-cards
* Per-table search / filter bar
* Sortable column headers
* Coloured action buttons  (green Add · blue Edit · red Delete)
* Stylish modal forms with header strip
* Live status bar  (server URL  ·  DB name  ·  record count)
* Animated progress-bar splash screen

Run from project root:
    python run_gui.py
"""

from __future__ import annotations

import threading
import time
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any

import requests
import uvicorn

# ─────────────────────────────────────────────────────────────────────────────
# Palette & constants
# ─────────────────────────────────────────────────────────────────────────────

API_HOST = "127.0.0.1"
API_PORT = 8199
API_BASE = f"http://{API_HOST}:{API_PORT}"

SB_BG       = "#1a2744"   # dark navy sidebar
SB_HOVER    = "#243560"
SB_SEL      = "#2d4a8a"
SB_FG       = "#c8d6f0"
SB_FG_SEL   = "#ffffff"
SB_ICON_FG  = "#7fa8e8"

CONTENT_BG  = "#f0f4fb"   # light blue-grey content
CARD_BG     = "#ffffff"
CARD_BORDER = "#dde5f5"

ROW_ODD     = "#f5f8ff"
ROW_EVEN    = "#ffffff"
ROW_SEL     = "#d0e4ff"

BTN_ADD     = "#27ae60"
BTN_ADD_H   = "#1e8449"
BTN_EDIT    = "#2980b9"
BTN_EDIT_H  = "#1f618d"
BTN_DEL     = "#c0392b"
BTN_DEL_H   = "#922b21"
BTN_REF     = "#7f8c8d"
BTN_REF_H   = "#626567"

HDR_BG      = "#1a2744"
HDR_SUB     = "#7fa8e8"
ACCENT      = "#2d4a8a"


# ─────────────────────────────────────────────────────────────────────────────
# Server bootstrap
# ─────────────────────────────────────────────────────────────────────────────

def _run_server() -> None:
    uvicorn.run("app.main:app", host=API_HOST, port=API_PORT, log_level="error")


def _wait_for_server(timeout: int = 30) -> bool:
    for _ in range(timeout * 2):
        try:
            requests.get(f"{API_BASE}/", timeout=1)
            return True
        except Exception:
            time.sleep(0.5)
    return False


# ─────────────────────────────────────────────────────────────────────────────
# API helpers
# ─────────────────────────────────────────────────────────────────────────────

def api_get(path: str) -> Any:
    r = requests.get(f"{API_BASE}{path}", timeout=10)
    r.raise_for_status()
    return r.json()


def api_post(path: str, data: dict) -> Any:
    r = requests.post(f"{API_BASE}{path}", json=data, timeout=10)
    r.raise_for_status()
    return r.json()


def api_put(path: str, data: dict) -> Any:
    r = requests.put(f"{API_BASE}{path}", json=data, timeout=10)
    r.raise_for_status()
    return r.json()


def api_delete(path: str) -> Any:
    r = requests.delete(f"{API_BASE}{path}", timeout=10)
    r.raise_for_status()
    return r.json()


def _api_error(exc: Exception) -> str:
    try:
        return exc.response.json().get("detail", str(exc))  # type: ignore[attr-defined]
    except Exception:
        return str(exc)


# ─────────────────────────────────────────────────────────────────────────────
# ColourButton — flat tk.Button with hover effect
# ─────────────────────────────────────────────────────────────────────────────

class ColourButton(tk.Button):
    def __init__(self, parent, text, bg, hover_bg, command=None, **kw):
        kw.setdefault("fg", "#ffffff")
        kw.setdefault("relief", "flat")
        kw.setdefault("cursor", "hand2")
        kw.setdefault("font", ("Segoe UI", 9, "bold"))
        kw.setdefault("padx", 12)
        kw.setdefault("pady", 5)
        kw.setdefault("bd", 0)
        super().__init__(parent, text=text, bg=bg, activebackground=hover_bg,
                         activeforeground="#ffffff", command=command, **kw)
        self._bg = bg
        self._hbg = hover_bg
        self.bind("<Enter>", lambda _: self.config(bg=self._hbg))
        self.bind("<Leave>", lambda _: self.config(bg=self._bg))


# ─────────────────────────────────────────────────────────────────────────────
# FormDialog — polished modal form with coloured header strip
# ─────────────────────────────────────────────────────────────────────────────

class FormDialog(tk.Toplevel):
    """Modal form.  fields = [(key, label, required, default), ...]"""

    def __init__(self, parent, title: str,
                 fields: list[tuple], on_submit) -> None:
        super().__init__(parent)
        self.title(title)
        self.resizable(False, False)
        self.grab_set()
        self.configure(bg=CONTENT_BG)
        self._fields = fields
        self._on_submit = on_submit
        self._entries: dict[str, tk.StringVar] = {}
        self._build(fields)
        self.transient(parent)
        self.update_idletasks()
        pw = parent.winfo_rootx() + parent.winfo_width()  // 2 - self.winfo_width()  // 2
        ph = parent.winfo_rooty() + parent.winfo_height() // 2 - self.winfo_height() // 2
        self.geometry(f"+{pw}+{ph}")
        self.wait_window()

    def _build(self, fields):
        # Coloured header
        hdr = tk.Frame(self, bg=ACCENT, height=46)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)
        tk.Label(hdr, text=f"  {self.title()}", bg=ACCENT, fg="white",
                 font=("Segoe UI", 11, "bold"), anchor="w").pack(
            fill=tk.X, padx=14, pady=10)

        # Form body
        body = tk.Frame(self, bg=CARD_BG, padx=20, pady=14)
        body.pack(fill=tk.BOTH)
        for i, (key, label, required, default) in enumerate(fields):
            lbl_text = label + ("  *" if required else "")
            tk.Label(body, text=lbl_text, bg=CARD_BG, font=("Segoe UI", 9),
                     fg="#333333", anchor="w").grid(
                row=i, column=0, sticky="w", pady=(6, 2), padx=(0, 14))
            var = tk.StringVar(value="" if default is None else str(default))
            self._entries[key] = var
            tk.Entry(body, textvariable=var, width=38, font=("Segoe UI", 9),
                     relief="solid", bd=1, bg="#f7f9ff", fg="#222").grid(
                row=i, column=1, pady=(6, 2), ipady=4)

        # Button row
        foot = tk.Frame(self, bg=CARD_BG, padx=20, pady=10)
        foot.pack(fill=tk.X)
        ColourButton(foot, "Save",   BTN_ADD, BTN_ADD_H,
                     command=self._submit, width=10).pack(side=tk.LEFT, padx=(0, 8))
        ColourButton(foot, "Cancel", BTN_REF, BTN_REF_H,
                     command=self.destroy, width=8).pack(side=tk.LEFT)

    def _submit(self):
        data = {k: v.get().strip() for k, v in self._entries.items()}
        for key, label, required, _ in self._fields:
            if required and not data.get(key):
                messagebox.showwarning("Required",
                                       f"'{label}' is required.", parent=self)
                return
        self._on_submit({k: v for k, v in data.items() if v != ""})
        self.destroy()


# ─────────────────────────────────────────────────────────────────────────────
# CRUDFrame — base class: table + search + sort + CRUD buttons
# ─────────────────────────────────────────────────────────────────────────────

class CRUDFrame(tk.Frame):
    COLUMNS:  list[tuple[str, str, int]] = []
    ENDPOINT: str = ""
    TITLE:    str = ""
    ICON:     str = ""

    def __init__(self, parent, *args, **kw):
        super().__init__(parent, bg=CONTENT_BG, *args, **kw)
        self._all_docs: list[dict] = []
        self._sort_col: str | None = None
        self._sort_asc: bool = True
        self._build_ui()
        self.after(300, self.refresh)

    def _build_ui(self):
        # Section title + record counter
        sec_hdr = tk.Frame(self, bg=CONTENT_BG)
        sec_hdr.pack(fill=tk.X, padx=20, pady=(18, 6))
        tk.Label(sec_hdr, text=f"{self.ICON}  {self.TITLE}",
                 bg=CONTENT_BG, fg="#1a2744",
                 font=("Segoe UI", 16, "bold")).pack(side=tk.LEFT)
        self._count_lbl = tk.Label(sec_hdr, text="",
                                    bg="#dde5f5", fg="#2d4a8a",
                                    font=("Segoe UI", 9, "bold"),
                                    padx=10, pady=3)
        self._count_lbl.pack(side=tk.LEFT, padx=12)

        # Toolbar card
        toolbar = tk.Frame(self, bg=CARD_BG,
                           highlightbackground=CARD_BORDER,
                           highlightthickness=1)
        toolbar.pack(fill=tk.X, padx=20, pady=(0, 8))

        btn_row = tk.Frame(toolbar, bg=CARD_BG)
        btn_row.pack(side=tk.LEFT, padx=10, pady=8)
        ColourButton(btn_row, "＋  Add New", BTN_ADD,  BTN_ADD_H,
                     command=self._on_add).pack(side=tk.LEFT, padx=(0, 6))
        ColourButton(btn_row, "✎  Edit",    BTN_EDIT, BTN_EDIT_H,
                     command=self._on_edit).pack(side=tk.LEFT, padx=(0, 6))
        ColourButton(btn_row, "✖  Delete",  BTN_DEL,  BTN_DEL_H,
                     command=self._on_delete).pack(side=tk.LEFT, padx=(0, 6))
        ColourButton(btn_row, "↻  Refresh", BTN_REF,  BTN_REF_H,
                     command=self.refresh).pack(side=tk.LEFT)

        # Search bar (right side of toolbar)
        search_row = tk.Frame(toolbar, bg=CARD_BG)
        search_row.pack(side=tk.RIGHT, padx=10, pady=8)
        tk.Label(search_row, text="🔍", bg=CARD_BG,
                 font=("Segoe UI", 11)).pack(side=tk.LEFT)
        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._apply_filter())
        tk.Entry(search_row, textvariable=self._search_var, width=28,
                 font=("Segoe UI", 9), relief="solid", bd=1,
                 bg="#f7f9ff").pack(side=tk.LEFT, ipady=4, padx=(4, 0))
        tk.Button(search_row, text="✕", relief="flat", bg=CARD_BG, fg="#888",
                  cursor="hand2", font=("Segoe UI", 9),
                  command=lambda: self._search_var.set("")).pack(side=tk.LEFT)

        # Table card
        table_card = tk.Frame(self, bg=CARD_BG,
                              highlightbackground=CARD_BORDER,
                              highlightthickness=1)
        table_card.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 16))

        cols = [c[0] for c in self.COLUMNS]
        self.tree = ttk.Treeview(table_card, columns=cols,
                                 show="headings", selectmode="browse")
        for key, heading, width in self.COLUMNS:
            self.tree.heading(key, text=heading + " ⇅",
                              command=lambda k=key: self._sort_by(k), anchor="w")
            self.tree.column(key, width=width, minwidth=50, anchor="w")

        vsb = ttk.Scrollbar(table_card, orient=tk.VERTICAL,   command=self.tree.yview)
        hsb = ttk.Scrollbar(table_card, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        table_card.rowconfigure(0, weight=1)
        table_card.columnconfigure(0, weight=1)

        self.tree.tag_configure("odd",  background=ROW_ODD)
        self.tree.tag_configure("even", background=ROW_EVEN)
        self.tree.bind("<Double-1>", lambda _: self._on_edit())

    # ── Data ─────────────────────────────────────────────────────────────────

    def get_row_values(self, doc: dict) -> list:
        return [str(doc.get(c[0], "")) for c in self.COLUMNS]

    def refresh(self):
        try:
            self._all_docs = api_get(self.ENDPOINT)
        except Exception as exc:
            messagebox.showerror("Load error", _api_error(exc))
            return
        self._apply_filter()

    def _apply_filter(self):
        q = self._search_var.get().lower()
        filtered = [d for d in self._all_docs
                    if not q or any(q in str(v).lower() for v in d.values())]
        if self._sort_col:
            filtered.sort(key=lambda d: str(d.get(self._sort_col, "")),
                          reverse=not self._sort_asc)
        self.tree.delete(*self.tree.get_children())
        for i, doc in enumerate(filtered):
            self.tree.insert("", tk.END, values=self.get_row_values(doc),
                             tags=("odd" if i % 2 else "even",))
        n = len(filtered)
        self._count_lbl.config(text=f"{n} record{'s' if n != 1 else ''}")

    def _sort_by(self, col: str):
        self._sort_asc = not self._sort_asc if self._sort_col == col else True
        self._sort_col = col
        self._apply_filter()

    def _selected_id(self) -> str | None:
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("No selection", "Please select a row first.")
            return None
        return self.tree.item(sel[0], "values")[0]

    # ── Actions ───────────────────────────────────────────────────────────────

    def _on_add(self):
        self.open_add_dialog()

    def _on_edit(self):
        doc_id = self._selected_id()
        if doc_id:
            try:
                doc = api_get(f"{self.ENDPOINT}/{doc_id}")
            except Exception as exc:
                messagebox.showerror("Error", _api_error(exc))
                return
            self.open_edit_dialog(doc)

    def _on_delete(self):
        doc_id = self._selected_id()
        if doc_id and messagebox.askyesno(
                "Confirm Delete",
                f"Permanently delete this record?\n\nID: {doc_id}",
                icon="warning"):
            try:
                api_delete(f"{self.ENDPOINT}/{doc_id}")
                self.refresh()
            except Exception as exc:
                messagebox.showerror("Delete failed", _api_error(exc))

    def open_add_dialog(self): ...
    def open_edit_dialog(self, doc: dict): ...


# ─────────────────────────────────────────────────────────────────────────────
# Suppliers
# ─────────────────────────────────────────────────────────────────────────────

class SuppliersFrame(CRUDFrame):
    ENDPOINT = "/suppliers"
    TITLE    = "Suppliers"
    ICON     = "🏭"
    COLUMNS  = [("id","ID",200),("name","Name",150),
                ("contact_email","Email",175),("phone","Phone",120),
                ("address","Address",210)]

    def get_row_values(self, doc):
        return [doc.get("id",""), doc.get("name",""),
                doc.get("contact_email",""), doc.get("phone",""),
                doc.get("address","")]

    def _fields(self, doc=None):
        d = doc or {}
        return [("name","Name",True,d.get("name")),
                ("contact_email","Email",False,d.get("contact_email")),
                ("phone","Phone",False,d.get("phone")),
                ("address","Address",False,d.get("address"))]

    def open_add_dialog(self):
        def submit(data):
            try:   api_post(self.ENDPOINT, data); self.refresh()
            except Exception as exc: messagebox.showerror("Error", _api_error(exc))
        FormDialog(self, "Add Supplier", self._fields(), submit)

    def open_edit_dialog(self, doc):
        def submit(data):
            try:   api_put(f"{self.ENDPOINT}/{doc['id']}", data); self.refresh()
            except Exception as exc: messagebox.showerror("Error", _api_error(exc))
        FormDialog(self, "Edit Supplier", self._fields(doc), submit)


# ─────────────────────────────────────────────────────────────────────────────
# Products
# ─────────────────────────────────────────────────────────────────────────────

class ProductsFrame(CRUDFrame):
    ENDPOINT = "/products"
    TITLE    = "Products"
    ICON     = "📦"
    COLUMNS  = [("id","ID",200),("name","Name",145),("sku","SKU",95),
                ("price","Price ($)",85),("stock","Stock",65),
                ("supplier_id","Supplier ID",200),("description","Description",195)]

    def get_row_values(self, doc):
        return [doc.get("id",""), doc.get("name",""), doc.get("sku",""),
                doc.get("price",""), doc.get("stock",""),
                doc.get("supplier_id",""), doc.get("description","")]

    def _fields(self, doc=None):
        d = doc or {}
        return [("name","Name",True,d.get("name")),
                ("sku","SKU",True,d.get("sku")),
                ("price","Price",True,d.get("price")),
                ("stock","Stock (qty)",False,d.get("stock",0)),
                ("supplier_id","Supplier ID",False,d.get("supplier_id")),
                ("description","Description",False,d.get("description"))]

    def open_add_dialog(self):
        def submit(data):
            try:
                data["price"] = float(data["price"])
                if "stock" in data: data["stock"] = int(data["stock"])
                api_post(self.ENDPOINT, data); self.refresh()
            except ValueError: messagebox.showerror("Error","Price/Stock must be numbers.")
            except Exception as exc: messagebox.showerror("Error", _api_error(exc))
        FormDialog(self, "Add Product", self._fields(), submit)

    def open_edit_dialog(self, doc):
        def submit(data):
            try:
                if "price" in data: data["price"] = float(data["price"])
                if "stock" in data: data["stock"] = int(data["stock"])
                api_put(f"{self.ENDPOINT}/{doc['id']}", data); self.refresh()
            except ValueError: messagebox.showerror("Error","Price/Stock must be numbers.")
            except Exception as exc: messagebox.showerror("Error", _api_error(exc))
        FormDialog(self, "Edit Product", self._fields(doc), submit)


# ─────────────────────────────────────────────────────────────────────────────
# Customers
# ─────────────────────────────────────────────────────────────────────────────

class CustomersFrame(CRUDFrame):
    ENDPOINT = "/customers"
    TITLE    = "Customers"
    ICON     = "👤"
    COLUMNS  = [("id","ID",200),("name","Name",150),("email","Email",175),
                ("phone","Phone",120),("address","Address",210)]

    def get_row_values(self, doc):
        return [doc.get("id",""), doc.get("name",""),
                doc.get("email",""), doc.get("phone",""), doc.get("address","")]

    def _fields(self, doc=None):
        d = doc or {}
        return [("name","Name",True,d.get("name")),
                ("email","Email",False,d.get("email")),
                ("phone","Phone",False,d.get("phone")),
                ("address","Address",False,d.get("address"))]

    def open_add_dialog(self):
        def submit(data):
            try:   api_post(self.ENDPOINT, data); self.refresh()
            except Exception as exc: messagebox.showerror("Error", _api_error(exc))
        FormDialog(self, "Add Customer", self._fields(), submit)

    def open_edit_dialog(self, doc):
        def submit(data):
            try:   api_put(f"{self.ENDPOINT}/{doc['id']}", data); self.refresh()
            except Exception as exc: messagebox.showerror("Error", _api_error(exc))
        FormDialog(self, "Edit Customer", self._fields(doc), submit)


# ─────────────────────────────────────────────────────────────────────────────
# Invoices
# ─────────────────────────────────────────────────────────────────────────────

class InvoicesFrame(CRUDFrame):
    ENDPOINT = "/invoices"
    TITLE    = "Invoices"
    ICON     = "📄"
    COLUMNS  = [("id","ID",200),("customer_id","Customer ID",200),
                ("subtotal","Subtotal",90),("tax","Tax",70),("total","Total",90),
                ("status","Status",80),("created_at","Created",160)]

    def get_row_values(self, doc):
        return [doc.get("id",""), doc.get("customer_id",""),
                doc.get("subtotal",""), doc.get("tax",""), doc.get("total",""),
                doc.get("status",""),
                doc.get("created_at","")[:19].replace("T"," ")
                if doc.get("created_at") else ""]

    def _fields(self, doc=None):
        d = doc or {}
        return [("customer_id","Customer ID",True,d.get("customer_id")),
                ("subtotal","Subtotal",True,d.get("subtotal")),
                ("tax","Tax",False,d.get("tax",0)),
                ("total","Total",True,d.get("total")),
                ("status","Status",False,d.get("status","draft"))]

    def open_add_dialog(self):
        def submit(data):
            try:
                data["subtotal"]=float(data["subtotal"])
                data["total"]=float(data["total"])
                if "tax" in data: data["tax"]=float(data["tax"])
                api_post(self.ENDPOINT, data); self.refresh()
            except ValueError: messagebox.showerror("Error","Subtotal/Tax/Total must be numbers.")
            except Exception as exc: messagebox.showerror("Error", _api_error(exc))
        FormDialog(self, "Add Invoice", self._fields(), submit)

    def open_edit_dialog(self, doc):
        def submit(data):
            try:
                if "subtotal" in data: data["subtotal"]=float(data["subtotal"])
                if "total"    in data: data["total"]=float(data["total"])
                if "tax"      in data: data["tax"]=float(data["tax"])
                api_put(f"{self.ENDPOINT}/{doc['id']}", data); self.refresh()
            except ValueError: messagebox.showerror("Error","Subtotal/Tax/Total must be numbers.")
            except Exception as exc: messagebox.showerror("Error", _api_error(exc))
        FormDialog(self, "Edit Invoice", self._fields(doc), submit)

    def _on_edit(self):
        doc_id = self._selected_id()
        if doc_id:
            try:
                resp = api_get(f"{self.ENDPOINT}/{doc_id}")
                doc  = resp.get("invoice", resp)
            except Exception as exc:
                messagebox.showerror("Error", _api_error(exc)); return
            self.open_edit_dialog(doc)


# ─────────────────────────────────────────────────────────────────────────────
# Invoice Items
# ─────────────────────────────────────────────────────────────────────────────

class InvoiceItemsFrame(CRUDFrame):
    ENDPOINT = "/invoice-items"
    TITLE    = "Invoice Items"
    ICON     = "🔖"
    COLUMNS  = [("id","ID",200),("invoice_id","Invoice ID",200),
                ("product_id","Product ID",200),("quantity","Qty",60),
                ("unit_price","Unit Price $",90),("line_total","Line Total $",95)]

    def get_row_values(self, doc):
        return [doc.get("id",""), doc.get("invoice_id",""),
                doc.get("product_id",""), doc.get("quantity",""),
                doc.get("unit_price",""), doc.get("line_total","")]

    def _fields(self, doc=None):
        d = doc or {}
        return [("invoice_id","Invoice ID",True,d.get("invoice_id")),
                ("product_id","Product ID",True,d.get("product_id")),
                ("quantity","Quantity",True,d.get("quantity")),
                ("unit_price","Unit Price",True,d.get("unit_price"))]

    def open_add_dialog(self):
        def submit(data):
            try:
                data["quantity"]=int(data["quantity"])
                data["unit_price"]=float(data["unit_price"])
                api_post(self.ENDPOINT, data); self.refresh()
            except ValueError: messagebox.showerror("Error","Quantity=int, Unit Price=number.")
            except Exception as exc: messagebox.showerror("Error", _api_error(exc))
        FormDialog(self, "Add Invoice Item", self._fields(), submit)

    def open_edit_dialog(self, doc):
        def submit(data):
            try:
                if "quantity"   in data: data["quantity"]=int(data["quantity"])
                if "unit_price" in data: data["unit_price"]=float(data["unit_price"])
                api_put(f"{self.ENDPOINT}/{doc['id']}", data); self.refresh()
            except ValueError: messagebox.showerror("Error","Quantity=int, Unit Price=number.")
            except Exception as exc: messagebox.showerror("Error", _api_error(exc))
        FormDialog(self, "Edit Invoice Item", self._fields(doc), submit)


# ─────────────────────────────────────────────────────────────────────────────
# Dashboard — stat cards + tips
# ─────────────────────────────────────────────────────────────────────────────

class DashboardFrame(tk.Frame):
    def __init__(self, parent, *args, **kw):
        super().__init__(parent, bg=CONTENT_BG, *args, **kw)
        self._build()
        self.after(400, self.refresh)

    def _stat_card(self, parent, icon, title, count_var, colour):
        card = tk.Frame(parent, bg=CARD_BG,
                        highlightbackground=colour, highlightthickness=2,
                        padx=20, pady=16)
        card.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=8)
        tk.Label(card, text=icon, bg=CARD_BG, font=("Segoe UI", 26)).pack(anchor="w")
        tk.Label(card, textvariable=count_var, bg=CARD_BG, fg=colour,
                 font=("Segoe UI", 30, "bold")).pack(anchor="w")
        tk.Label(card, text=title, bg=CARD_BG, fg="#555",
                 font=("Segoe UI", 10)).pack(anchor="w")

    def _build(self):
        tk.Label(self, text="📊  Dashboard", bg=CONTENT_BG, fg="#1a2744",
                 font=("Segoe UI", 18, "bold")).pack(anchor="w", padx=22, pady=(20, 4))
        tk.Label(self, text="Live overview of your inventory & billing data",
                 bg=CONTENT_BG, fg="#666",
                 font=("Segoe UI", 9)).pack(anchor="w", padx=22, pady=(0, 14))

        row = tk.Frame(self, bg=CONTENT_BG)
        row.pack(fill=tk.X, padx=14, pady=(0, 12))
        self._v_sup   = tk.StringVar(value="…")
        self._v_pro   = tk.StringVar(value="…")
        self._v_cus   = tk.StringVar(value="…")
        self._v_inv   = tk.StringVar(value="…")
        self._v_items = tk.StringVar(value="…")
        self._stat_card(row, "🏭", "Suppliers",     self._v_sup,   "#8e44ad")
        self._stat_card(row, "📦", "Products",      self._v_pro,   "#27ae60")
        self._stat_card(row, "👤", "Customers",     self._v_cus,   "#2980b9")
        self._stat_card(row, "📄", "Invoices",      self._v_inv,   "#e67e22")
        self._stat_card(row, "🔖", "Invoice Items", self._v_items, "#c0392b")

        tip_card = tk.Frame(self, bg=CARD_BG,
                            highlightbackground=CARD_BORDER, highlightthickness=1)
        tip_card.pack(fill=tk.X, padx=22, pady=(4, 0))
        tk.Label(tip_card, text="  Quick Tips", bg=CARD_BG, fg="#1a2744",
                 font=("Segoe UI", 10, "bold"),
                 anchor="w").pack(fill=tk.X, padx=12, pady=(10, 4))
        for t in [
            "  •  Use the left sidebar to navigate between sections.",
            "  •  Double-click any row in a table to edit it.",
            "  •  Click a column header (⇅) to sort the table ascending / descending.",
            "  •  Use the 🔍 search bar to filter records in real time.",
            "  •  The Billing section creates a complete invoice with auto stock deduction.",
        ]:
            tk.Label(tip_card, text=t, bg=CARD_BG, fg="#444",
                     font=("Segoe UI", 9), anchor="w").pack(fill=tk.X, padx=12, pady=1)
        tk.Label(tip_card, text="", bg=CARD_BG).pack()

        ColourButton(self, "↻  Refresh Stats", BTN_REF, BTN_REF_H,
                     command=self.refresh).pack(anchor="w", padx=22, pady=10)

    def refresh(self):
        for endpoint, var in [
            ("/suppliers",     self._v_sup),
            ("/products",      self._v_pro),
            ("/customers",     self._v_cus),
            ("/invoices",      self._v_inv),
            ("/invoice-items", self._v_items),
        ]:
            try:
                var.set(str(len(api_get(endpoint))))
            except Exception:
                var.set("–")


# ─────────────────────────────────────────────────────────────────────────────
# Billing wizard
# ─────────────────────────────────────────────────────────────────────────────

class BillingFrame(tk.Frame):
    def __init__(self, parent, *args, **kw):
        super().__init__(parent, bg=CONTENT_BG, *args, **kw)
        self._line_items: list[dict] = []
        self._customers:  list[dict] = []
        self._products:   list[dict] = []
        self._build()
        self.after(400, self._reload)

    def _build(self):
        tk.Label(self, text="💳  Create Billing Invoice",
                 bg=CONTENT_BG, fg="#1a2744",
                 font=("Segoe UI", 16, "bold")).pack(anchor="w", padx=22, pady=(18, 6))

        # Customer + tax
        hd = tk.Frame(self, bg=CARD_BG,
                      highlightbackground=CARD_BORDER, highlightthickness=1)
        hd.pack(fill=tk.X, padx=22, pady=(0, 10))
        inner = tk.Frame(hd, bg=CARD_BG)
        inner.pack(fill=tk.X, padx=14, pady=12)
        tk.Label(inner, text="Customer:", bg=CARD_BG, fg="#333",
                 font=("Segoe UI", 9, "bold")).grid(row=0, column=0,
                                                    sticky="w", padx=(0, 8))
        self.customer_var = tk.StringVar()
        self.customer_cb  = ttk.Combobox(inner, textvariable=self.customer_var,
                                          width=42, state="readonly",
                                          font=("Segoe UI", 9))
        self.customer_cb.grid(row=0, column=1, padx=(0, 20))
        tk.Label(inner, text="Tax Rate (%):", bg=CARD_BG, fg="#333",
                 font=("Segoe UI", 9, "bold")).grid(row=0, column=2,
                                                    sticky="w", padx=(0, 8))
        self.tax_var = tk.StringVar(value="0")
        tk.Entry(inner, textvariable=self.tax_var, width=8,
                 font=("Segoe UI", 9), relief="solid", bd=1,
                 bg="#f7f9ff").grid(row=0, column=3, ipady=4)
        self.tax_var.trace_add("write", lambda *_: self._update_summary())
        ColourButton(inner, "↻ Reload", BTN_REF, BTN_REF_H,
                     command=self._reload).grid(row=0, column=4, padx=(14, 0))

        # Line items
        li_card = tk.Frame(self, bg=CARD_BG,
                           highlightbackground=CARD_BORDER, highlightthickness=1)
        li_card.pack(fill=tk.BOTH, expand=True, padx=22, pady=(0, 10))
        tk.Label(li_card, text="Line Items", bg=CARD_BG, fg="#1a2744",
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=14, pady=(10, 4))

        add_row = tk.Frame(li_card, bg=CARD_BG)
        add_row.pack(fill=tk.X, padx=14, pady=(0, 8))
        tk.Label(add_row, text="Product:", bg=CARD_BG, fg="#333",
                 font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT)
        self.product_var = tk.StringVar()
        self.product_cb  = ttk.Combobox(add_row, textvariable=self.product_var,
                                         width=46, state="readonly",
                                         font=("Segoe UI", 9))
        self.product_cb.pack(side=tk.LEFT, padx=(6, 14))
        tk.Label(add_row, text="Qty:", bg=CARD_BG, fg="#333",
                 font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT)
        self.qty_var = tk.StringVar(value="1")
        tk.Entry(add_row, textvariable=self.qty_var, width=6,
                 font=("Segoe UI", 9), relief="solid", bd=1,
                 bg="#f7f9ff").pack(side=tk.LEFT, padx=(4, 12), ipady=4)
        ColourButton(add_row, "＋ Add Line",       BTN_ADD, BTN_ADD_H,
                     command=self._add_line).pack(side=tk.LEFT, padx=(0, 6))
        ColourButton(add_row, "✖ Remove Selected", BTN_DEL, BTN_DEL_H,
                     command=self._remove_line).pack(side=tk.LEFT)

        cols = ("product_id","product_name","quantity","unit_price","line_total")
        self.lines_tree = ttk.Treeview(li_card, columns=cols, show="headings", height=9)
        for key, heading, width in [
            ("product_id",   "Product ID",   180),
            ("product_name", "Product Name", 180),
            ("quantity",     "Qty",           60),
            ("unit_price",   "Unit Price $",  110),
            ("line_total",   "Line Total $",  110),
        ]:
            self.lines_tree.heading(key, text=heading, anchor="w")
            self.lines_tree.column(key, width=width, anchor="w")
        vsb = ttk.Scrollbar(li_card, orient=tk.VERTICAL,
                             command=self.lines_tree.yview)
        self.lines_tree.configure(yscrollcommand=vsb.set)
        self.lines_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True,
                              padx=(14, 0), pady=(0, 10))
        vsb.pack(side=tk.RIGHT, fill=tk.Y, pady=(0, 10), padx=(0, 8))

        # Summary footer
        foot = tk.Frame(self, bg=CARD_BG,
                        highlightbackground=CARD_BORDER, highlightthickness=1)
        foot.pack(fill=tk.X, padx=22, pady=(0, 16))
        inner2 = tk.Frame(foot, bg=CARD_BG)
        inner2.pack(fill=tk.X, padx=14, pady=10)
        self.summary_lbl = tk.Label(inner2,
                                     text="Subtotal: —   Tax: —   Total: —",
                                     bg=CARD_BG, fg="#1a2744",
                                     font=("Segoe UI", 12, "bold"))
        self.summary_lbl.pack(side=tk.LEFT)
        ColourButton(inner2, "💳  Issue Invoice", BTN_ADD, BTN_ADD_H,
                     command=self._submit).pack(side=tk.RIGHT, padx=(8, 0))
        ColourButton(inner2, "🗑  Clear", BTN_DEL, BTN_DEL_H,
                     command=self._clear).pack(side=tk.RIGHT, padx=(0, 6))

    def _reload(self):
        try:
            self._customers = api_get("/customers")
            self.customer_cb["values"] = [
                f"{c['name']}  ({c['id'][:8]}…)" for c in self._customers]
        except Exception as exc:
            messagebox.showerror("Error", f"Customers:\n{_api_error(exc)}")
        try:
            self._products = api_get("/products")
            self.product_cb["values"] = [
                f"{p['name']}  [SKU:{p['sku']}]  Stock:{p['stock']}  ${p['price']}"
                for p in self._products]
        except Exception as exc:
            messagebox.showerror("Error", f"Products:\n{_api_error(exc)}")

    def _add_line(self):
        idx = self.product_cb.current()
        if idx < 0:
            messagebox.showwarning("Select product", "Please select a product.")
            return
        try:
            qty = int(self.qty_var.get())
            assert qty > 0
        except Exception:
            messagebox.showwarning("Invalid qty", "Quantity must be a positive integer.")
            return
        p  = self._products[idx]
        up = float(p["price"])
        lt = round(qty * up, 2)
        item = {"product_id": p["id"], "product_name": p["name"],
                "quantity": qty, "unit_price": up, "line_total": lt}
        self._line_items.append(item)
        self.lines_tree.insert("", tk.END,
            values=(item["product_id"], item["product_name"],
                    item["quantity"], f"{up:.2f}", f"{lt:.2f}"))
        self._update_summary()
        self.qty_var.set("1")

    def _remove_line(self):
        sel = self.lines_tree.selection()
        if not sel:
            return
        idx = self.lines_tree.index(sel[0])
        self.lines_tree.delete(sel[0])
        self._line_items.pop(idx)
        self._update_summary()

    def _update_summary(self):
        sub = round(sum(i["line_total"] for i in self._line_items), 2)
        try:   rate = float(self.tax_var.get()) / 100
        except ValueError: rate = 0.0
        tax = round(sub * rate, 2)
        tot = round(sub + tax, 2)
        self.summary_lbl.config(
            text=f"Subtotal: ${sub:.2f}     Tax: ${tax:.2f}     Total: ${tot:.2f}")

    def _clear(self):
        self._line_items.clear()
        self.lines_tree.delete(*self.lines_tree.get_children())
        self.customer_cb.set("")
        self.qty_var.set("1")
        self._update_summary()

    def _submit(self):
        ci = self.customer_cb.current()
        if ci < 0:
            messagebox.showwarning("No customer", "Please select a customer.")
            return
        if not self._line_items:
            messagebox.showwarning("No items", "Add at least one line item.")
            return
        try:   rate = float(self.tax_var.get()) / 100
        except ValueError: rate = 0.0
        payload = {
            "customer_id": self._customers[ci]["id"],
            "tax_rate": rate,
            "items": [{"product_id": it["product_id"],
                       "quantity":   it["quantity"]}
                      for it in self._line_items],
        }
        try:
            result = api_post("/billing/invoices", payload)
            inv = result.get("invoice", {})
            messagebox.showinfo("Invoice Created ✔",
                f"Invoice created successfully!\n\n"
                f"ID:     {inv.get('id','')}\n"
                f"Total:  ${inv.get('total','')}\n"
                f"Status: {inv.get('status','')}")
            self._clear()
            self._reload()
        except Exception as exc:
            messagebox.showerror("Billing error", _api_error(exc))


# ─────────────────────────────────────────────────────────────────────────────
# Sidebar navigation button
# ─────────────────────────────────────────────────────────────────────────────

class SidebarBtn(tk.Frame):
    def __init__(self, parent, icon, label, command, **kw):
        super().__init__(parent, bg=SB_BG, cursor="hand2", **kw)
        self._cmd    = command
        self._active = False
        self._icon_lbl = tk.Label(self, text=icon, bg=SB_BG, fg=SB_ICON_FG,
                                   font=("Segoe UI", 14), width=3, anchor="e")
        self._icon_lbl.pack(side=tk.LEFT, padx=(12, 4))
        self._text_lbl = tk.Label(self, text=label, bg=SB_BG, fg=SB_FG,
                                   font=("Segoe UI", 10), anchor="w")
        self._text_lbl.pack(side=tk.LEFT, fill=tk.X, expand=True, pady=10)
        for w in (self, self._icon_lbl, self._text_lbl):
            w.bind("<Button-1>", lambda _: self._cmd())
            w.bind("<Enter>",    self._on_enter)
            w.bind("<Leave>",    self._on_leave)

    def set_active(self, active: bool):
        self._active = active
        bg = SB_SEL if active else SB_BG
        fg = SB_FG_SEL if active else SB_FG
        for w in (self, self._icon_lbl, self._text_lbl):
            w.config(bg=bg)
        self._text_lbl.config(fg=fg,
                               font=("Segoe UI", 10,
                                     "bold" if active else "normal"))
        self._icon_lbl.config(fg=SB_FG_SEL if active else SB_ICON_FG)

    def _on_enter(self, _=None):
        if not self._active:
            for w in (self, self._icon_lbl, self._text_lbl):
                w.config(bg=SB_HOVER)

    def _on_leave(self, _=None):
        if not self._active:
            for w in (self, self._icon_lbl, self._text_lbl):
                w.config(bg=SB_BG)


# ─────────────────────────────────────────────────────────────────────────────
# Main application window
# ─────────────────────────────────────────────────────────────────────────────

class App(tk.Tk):
    _PAGES = [
        ("📊", "Dashboard",     DashboardFrame),
        ("🏭", "Suppliers",     SuppliersFrame),
        ("📦", "Products",      ProductsFrame),
        ("👤", "Customers",     CustomersFrame),
        ("📄", "Invoices",      InvoicesFrame),
        ("🔖", "Invoice Items", InvoiceItemsFrame),
        ("💳", "Billing",       BillingFrame),
    ]

    def __init__(self):
        super().__init__()
        self.title("Inventory & Billing Manager")
        self.geometry("1280x720")
        self.minsize(1020, 580)
        self.configure(bg=SB_BG)
        self._apply_style()
        self._build_ui()
        self._show_page(0)

    def _apply_style(self):
        style = ttk.Style(self)
        for theme in ("vista", "winnative", "clam", "alt", "default"):
            if theme in style.theme_names():
                style.theme_use(theme)
                break
        style.configure("Treeview",         rowheight=28, font=("Segoe UI", 9))
        style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"),
                        background="#e8f0fe")
        style.configure("TCombobox",        font=("Segoe UI", 9))
        style.map("Treeview",
                  background=[("selected", ROW_SEL)],
                  foreground=[("selected", "#1a2744")])

    def _build_ui(self):
        # ── Sidebar ───────────────────────────────────────────────────────────
        self._sidebar = tk.Frame(self, bg=SB_BG, width=200)
        self._sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self._sidebar.pack_propagate(False)

        # Logo block
        logo_frame = tk.Frame(self._sidebar, bg=SB_BG, height=72)
        logo_frame.pack(fill=tk.X)
        logo_frame.pack_propagate(False)
        tk.Label(logo_frame, text="📦", bg=SB_BG, fg="#ffffff",
                 font=("Segoe UI", 22)).pack(side=tk.LEFT, padx=(14, 6), pady=16)
        tk.Label(logo_frame, text="Inventory\nManager", bg=SB_BG, fg="#ffffff",
                 font=("Segoe UI", 9, "bold"),
                 justify="left").pack(side=tk.LEFT, pady=16)

        # Divider
        tk.Frame(self._sidebar, bg=SB_SEL, height=1).pack(fill=tk.X, padx=14)

        # Nav buttons
        self._nav_btns: list[SidebarBtn] = []
        for icon, label, _ in self._PAGES:
            btn = SidebarBtn(
                self._sidebar, icon, label,
                command=lambda i=len(self._nav_btns): self._show_page(i))
            btn.pack(fill=tk.X)
            self._nav_btns.append(btn)

        # Footer version text
        tk.Frame(self._sidebar, bg=SB_BG).pack(fill=tk.BOTH, expand=True)
        tk.Label(self._sidebar, text="v2.0  ·  FastAPI + MongoDB",
                 bg=SB_BG, fg="#4a6080",
                 font=("Segoe UI", 7)).pack(side=tk.BOTTOM, pady=8)

        # ── Right panel ───────────────────────────────────────────────────────
        right = tk.Frame(self, bg=CONTENT_BG)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Top header bar
        self._top_bar = tk.Frame(right, bg=HDR_BG, height=50)
        self._top_bar.pack(fill=tk.X)
        self._top_bar.pack_propagate(False)
        self._page_title = tk.Label(self._top_bar, text="",
                                     bg=HDR_BG, fg="white",
                                     font=("Segoe UI", 13, "bold"), anchor="w")
        self._page_title.pack(side=tk.LEFT, padx=20, pady=12)
        tk.Label(self._top_bar, text="MongoDB · FastAPI · Tkinter",
                 bg=HDR_BG, fg=HDR_SUB,
                 font=("Segoe UI", 8), anchor="e").pack(side=tk.RIGHT, padx=18)

        # Page stacker
        self._container = tk.Frame(right, bg=CONTENT_BG)
        self._container.pack(fill=tk.BOTH, expand=True)
        self._container.rowconfigure(0, weight=1)
        self._container.columnconfigure(0, weight=1)

        self._pages: list[tk.Frame] = []
        for _, label, cls in self._PAGES:
            frame = cls(self._container)
            frame.grid(row=0, column=0, sticky="nsew")
            self._pages.append(frame)

        # Status bar
        status = tk.Frame(right, bg="#e8f0fe",
                          highlightbackground=CARD_BORDER,
                          highlightthickness=1, height=24)
        status.pack(fill=tk.X, side=tk.BOTTOM)
        status.pack_propagate(False)
        tk.Label(status,
                 text=f"  API: {API_BASE}   ·   DB: inventory_billing_db",
                 bg="#e8f0fe", fg="#555", font=("Segoe UI", 8),
                 anchor="w").pack(side=tk.LEFT, pady=4)
        tk.Label(status, text="● Connected",
                 bg="#e8f0fe", fg="#1a8a1a",
                 font=("Segoe UI", 8, "bold")).pack(side=tk.RIGHT, padx=14)

    def _show_page(self, index: int):
        self._pages[index].tkraise()
        for i, btn in enumerate(self._nav_btns):
            btn.set_active(i == index)
        icon, label, _ = self._PAGES[index]
        self._page_title.config(text=f"{icon}  {label}")


# ─────────────────────────────────────────────────────────────────────────────
# Splash screen + entry point
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    # 1. Start FastAPI server in a daemon thread
    threading.Thread(target=_run_server, daemon=True).start()

    # 2. Animated splash screen
    splash = tk.Tk()
    splash.overrideredirect(True)
    splash.configure(bg=SB_BG)
    splash.geometry("420x200")
    splash.eval("tk::PlaceWindow . center")
    tk.Label(splash, text="📦", bg=SB_BG, fg="white",
             font=("Segoe UI", 36)).pack(pady=(22, 2))
    tk.Label(splash, text="Inventory & Billing Manager",
             bg=SB_BG, fg="white",
             font=("Segoe UI", 13, "bold")).pack()
    tk.Label(splash, text="Starting API server…",
             bg=SB_BG, fg="#7fa8e8",
             font=("Segoe UI", 9)).pack(pady=(6, 10))
    pb = ttk.Progressbar(splash, mode="indeterminate", length=280)
    pb.pack()
    pb.start(12)
    splash.update()

    ok = _wait_for_server()
    pb.stop()
    splash.destroy()

    if not ok:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "Server failed to start",
            "Could not connect to the API server.\n\n"
            "Make sure MongoDB is running and try again.")
        return

    # 3. Launch main window
    App().mainloop()


if __name__ == "__main__":
    main()
