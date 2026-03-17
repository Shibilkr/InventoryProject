"""
Inventory & Billing Manager — Desktop GUI  (v3 — Modern & Polished)
====================================================================
* Refined sidebar with gradient-feel, larger icons, smooth hover
* Dashboard with shadow-cards, large numbers, clean layout
* Crisp CRUD tables with bigger rows, clear headers, zebra stripes
* Elegant modal forms with large inputs and rounded buttons
* Modern colour palette — cleaner whites, deeper accents
* Auto-refresh every 5 seconds (silent)
* Animated splash with progress bar

Run:  python run_gui.py
"""

from __future__ import annotations

import sys
import threading
import time
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any

import requests
import uvicorn

from app.database import DATABASE_BACKEND, DATABASE_LABEL

# ─────────────────────────────────────────────────────────────────────────────
# Modern Palette
# ─────────────────────────────────────────────────────────────────────────────

API_HOST = "127.0.0.1"
API_PORT = 8199
API_BASE = f"http://{API_HOST}:{API_PORT}"

# Sidebar
SB_BG       = "#0f1b2d"
SB_HOVER    = "#1a2d4a"
SB_SEL      = "#234680"
SB_FG       = "#8ba3c7"
SB_FG_SEL   = "#ffffff"
SB_ICON_FG  = "#5b8bd4"

# Content area
BG          = "#eef2f7"
CARD_BG     = "#ffffff"
CARD_BORDER = "#d8e0ec"
CARD_SHADOW = "#c5cfdf"

# Table
ROW_ODD     = "#f6f8fc"
ROW_EVEN    = "#ffffff"
ROW_SEL     = "#cde0ff"
HDR_TBL     = "#e4ecf7"

# Buttons
BTN_GREEN   = "#1aab52"
BTN_GREEN_H = "#158f44"
BTN_BLUE    = "#2574d4"
BTN_BLUE_H  = "#1b5eb0"
BTN_RED     = "#d43b2c"
BTN_RED_H   = "#b0301f"
BTN_GREY    = "#6b7d94"
BTN_GREY_H  = "#556878"

# Header / accent
HDR_BG      = "#0f1b2d"
HDR_SUB     = "#5b8bd4"
ACCENT      = "#234680"

# Fonts
if sys.platform == "darwin":
    FONT = "SF Pro Text"
elif sys.platform.startswith("win"):
    FONT = "Segoe UI"
else:
    FONT = "Helvetica"

FONT_TITLE  = (FONT, 17, "bold")
FONT_HDR    = (FONT, 13, "bold")
FONT_BTN    = (FONT, 10, "bold")
FONT_LBL    = (FONT, 10)
FONT_ENTRY  = (FONT, 10)
FONT_SMALL  = (FONT, 9)
FONT_TINY   = (FONT, 8)
FONT_BIG    = (FONT, 32, "bold")
FONT_ICON   = (FONT, 28)
FONT_NAV    = (FONT, 11)
FONT_LOGO   = (FONT, 10, "bold")

DB_BRAND_TEXT = "In-Memory Demo" if DATABASE_BACKEND == "memory" else "MongoDB"
DB_STATUS_TEXT = "Demo Mode" if DATABASE_BACKEND == "memory" else "Connected"
DB_STATUS_COLOR = "#d97706" if DATABASE_BACKEND == "memory" else "#059669"


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
# ModernButton — styled flat button with smooth hover
# ─────────────────────────────────────────────────────────────────────────────

class ModernButton(tk.Button):
    def __init__(self, parent, text, bg, hover_bg, command=None, **kw):
        kw.setdefault("fg", "#ffffff")
        kw.setdefault("relief", "flat")
        kw.setdefault("cursor", "hand2")
        kw.setdefault("font", FONT_BTN)
        kw.setdefault("padx", 16)
        kw.setdefault("pady", 7)
        kw.setdefault("bd", 0)
        kw.setdefault("highlightthickness", 0)
        super().__init__(parent, text=text, bg=bg, activebackground=hover_bg,
                         activeforeground="#ffffff", command=command, **kw)
        self._bg = bg
        self._hbg = hover_bg
        self.bind("<Enter>", lambda _: self.config(bg=self._hbg))
        self.bind("<Leave>", lambda _: self.config(bg=self._bg))


# ─────────────────────────────────────────────────────────────────────────────
# FormDialog — elegant modal form with large inputs
# ─────────────────────────────────────────────────────────────────────────────

class FormDialog(tk.Toplevel):
    """Modal form.  fields = [(key, label, required, default, [choices]), ...]"""

    def __init__(self, parent, title: str,
                 fields: list[tuple], on_submit) -> None:
        super().__init__(parent)
        self.title(title)
        self.resizable(False, False)
        self.grab_set()
        self.configure(bg=CARD_BG)
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
        # Header strip
        hdr = tk.Frame(self, bg=ACCENT, height=52)
        hdr.pack(fill=tk.X)
        hdr.pack_propagate(False)
        tk.Label(hdr, text=f"   {self.title()}", bg=ACCENT, fg="white",
                 font=FONT_HDR, anchor="w").pack(fill=tk.X, padx=16, pady=14)

        # Form body
        body = tk.Frame(self, bg=CARD_BG, padx=28, pady=18)
        body.pack(fill=tk.BOTH)
        self._combo_maps: dict[str, dict[str, str]] = {}
        for i, field_def in enumerate(fields):
            key, label, required, default = field_def[:4]
            choices = field_def[4] if len(field_def) > 4 else None
            lbl_text = f"{label}{'  *' if required else ''}"
            tk.Label(body, text=lbl_text, bg=CARD_BG, font=FONT_LBL,
                     fg="#374151", anchor="w").grid(
                row=i, column=0, sticky="w", pady=(10, 3), padx=(0, 18))
            var = tk.StringVar(value="" if default is None else str(default))
            self._entries[key] = var
            if choices:
                display_list = [display for _, display in choices]
                value_map = {display: val for val, display in choices}
                self._combo_maps[key] = value_map
                if default:
                    for val, display in choices:
                        if str(val) == str(default):
                            var.set(display)
                            break
                cb = ttk.Combobox(body, textvariable=var, values=display_list,
                                 width=40, font=FONT_ENTRY, state="readonly")
                cb.grid(row=i, column=1, pady=(10, 3), ipady=5)
            else:
                e = tk.Entry(body, textvariable=var, width=42, font=FONT_ENTRY,
                             relief="solid", bd=1, bg="#f8fafd", fg="#1f2937",
                             insertbackground="#234680",
                             highlightcolor="#5b8bd4", highlightthickness=1)
                e.grid(row=i, column=1, pady=(10, 3), ipady=6)

        # Button row
        foot = tk.Frame(self, bg=CARD_BG, padx=28, pady=14)
        foot.pack(fill=tk.X)
        ModernButton(foot, "   Save   ", BTN_GREEN, BTN_GREEN_H,
                     command=self._submit).pack(side=tk.LEFT, padx=(0, 10))
        ModernButton(foot, "  Cancel  ", BTN_GREY, BTN_GREY_H,
                     command=self.destroy).pack(side=tk.LEFT)

    def _submit(self):
        data = {k: v.get().strip() for k, v in self._entries.items()}
        for key, value_map in self._combo_maps.items():
            if key in data and data[key] in value_map:
                data[key] = value_map[data[key]]
        for field_def in self._fields:
            key, label, required = field_def[0], field_def[1], field_def[2]
            if required and not data.get(key):
                messagebox.showwarning("Required",
                                       f"'{label}' is required.", parent=self)
                return
        self._on_submit({k: v for k, v in data.items() if v != ""})
        self.destroy()


# ─────────────────────────────────────────────────────────────────────────────
# CRUDFrame — polished table view with toolbar
# ─────────────────────────────────────────────────────────────────────────────

class CRUDFrame(tk.Frame):
    COLUMNS:  list[tuple[str, str, int]] = []
    ENDPOINT: str = ""
    TITLE:    str = ""
    ICON:     str = ""

    _AUTO_REFRESH_MS = 5000

    def __init__(self, parent, *args, **kw):
        super().__init__(parent, bg=BG, *args, **kw)
        self._all_docs: list[dict] = []
        self._sort_col: str | None = None
        self._sort_asc: bool = True
        self._build_ui()
        self.after(300, self.refresh)
        self._schedule_auto_refresh()

    def _schedule_auto_refresh(self):
        self.after(self._AUTO_REFRESH_MS, self._auto_refresh)

    def _auto_refresh(self):
        self.refresh(_silent=True)
        self._schedule_auto_refresh()

    def _build_ui(self):
        # Section header
        hdr_frame = tk.Frame(self, bg=BG)
        hdr_frame.pack(fill=tk.X, padx=24, pady=(22, 10))
        tk.Label(hdr_frame, text=f"{self.ICON}  {self.TITLE}",
                 bg=BG, fg="#1e293b", font=FONT_TITLE).pack(side=tk.LEFT)
        self._count_lbl = tk.Label(hdr_frame, text="",
                                    bg="#dce6f2", fg=ACCENT,
                                    font=(FONT, 10, "bold"),
                                    padx=14, pady=4)
        self._count_lbl.pack(side=tk.LEFT, padx=16)

        # Toolbar
        toolbar = tk.Frame(self, bg=CARD_BG, highlightbackground=CARD_BORDER,
                           highlightthickness=1)
        toolbar.pack(fill=tk.X, padx=24, pady=(0, 10))

        btn_row = tk.Frame(toolbar, bg=CARD_BG)
        btn_row.pack(side=tk.LEFT, padx=14, pady=10)
        ModernButton(btn_row, "  + Add New  ", BTN_GREEN, BTN_GREEN_H,
                     command=self._on_add).pack(side=tk.LEFT, padx=(0, 8))
        ModernButton(btn_row, "  Edit  ", BTN_BLUE, BTN_BLUE_H,
                     command=self._on_edit).pack(side=tk.LEFT, padx=(0, 8))
        ModernButton(btn_row, "  Delete  ", BTN_RED, BTN_RED_H,
                     command=self._on_delete).pack(side=tk.LEFT, padx=(0, 8))
        ModernButton(btn_row, "  Refresh  ", BTN_GREY, BTN_GREY_H,
                     command=self.refresh).pack(side=tk.LEFT, padx=(0, 16))

        # Separator
        tk.Frame(btn_row, bg=CARD_BORDER, width=2, height=24).pack(
            side=tk.LEFT, padx=(0, 16), fill=tk.Y, pady=2)

        # Bulk operations
        ModernButton(btn_row, "  Update All  ", "#7c3aed", "#6525c4",
                     command=self._on_update_all).pack(side=tk.LEFT, padx=(0, 8))
        ModernButton(btn_row, "  Delete All  ", "#991b1b", "#7f1d1d",
                     command=self._on_delete_all).pack(side=tk.LEFT)

        # Search
        search_row = tk.Frame(toolbar, bg=CARD_BG)
        search_row.pack(side=tk.RIGHT, padx=14, pady=10)
        tk.Label(search_row, text="Search:", bg=CARD_BG,
                 font=FONT_LBL, fg="#4b5563").pack(side=tk.LEFT, padx=(0, 6))
        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", lambda *_: self._apply_filter())
        se = tk.Entry(search_row, textvariable=self._search_var, width=30,
                      font=FONT_ENTRY, relief="solid", bd=1,
                      bg="#f8fafd", fg="#1f2937",
                      insertbackground="#234680",
                      highlightcolor="#5b8bd4", highlightthickness=1)
        se.pack(side=tk.LEFT, ipady=5, padx=(0, 4))
        tk.Button(search_row, text="  X  ", relief="flat", bg=CARD_BG, fg="#9ca3af",
                  cursor="hand2", font=FONT_SMALL, bd=0,
                  command=lambda: self._search_var.set("")).pack(side=tk.LEFT)

        # Table
        table_card = tk.Frame(self, bg=CARD_BG, highlightbackground=CARD_BORDER,
                              highlightthickness=1)
        table_card.pack(fill=tk.BOTH, expand=True, padx=24, pady=(0, 20))

        cols = [c[0] for c in self.COLUMNS]
        self.tree = ttk.Treeview(table_card, columns=cols,
                                 show="headings", selectmode="browse")
        for key, heading, width in self.COLUMNS:
            self.tree.heading(key, text=f"  {heading}",
                              command=lambda k=key: self._sort_by(k), anchor="w")
            self.tree.column(key, width=width, minwidth=60, anchor="w")

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

    def refresh(self, _silent: bool = False):
        try:
            self._all_docs = api_get(self.ENDPOINT)
        except Exception as exc:
            if not _silent:
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

    def _on_update_all(self):
        """Open a form dialog; the filled-in fields are applied to ALL records."""
        self.open_update_all_dialog()

    def _on_delete_all(self):
        n = len(self._all_docs)
        if n == 0:
            messagebox.showinfo("Empty", "There are no records to delete.")
            return
        if messagebox.askyesno(
                "Delete ALL Records",
                f"This will permanently delete ALL {n} record(s) "
                f"from {self.TITLE}.\n\n"
                f"Records linked to other collections will be skipped.\n\n"
                f"Are you sure?",
                icon="warning"):
            try:
                result = api_delete(self.ENDPOINT)
                msg = result.get("message", "Done")
                messagebox.showinfo("Delete All", msg)
                self.refresh()
            except Exception as exc:
                messagebox.showerror("Delete All failed", _api_error(exc))

    def open_add_dialog(self): ...
    def open_edit_dialog(self, doc: dict): ...
    def open_update_all_dialog(self): ...


# ─────────────────────────────────────────────────────────────────────────────
# Suppliers
# ─────────────────────────────────────────────────────────────────────────────

class SuppliersFrame(CRUDFrame):
    ENDPOINT = "/suppliers"
    TITLE    = "Suppliers"
    ICON     = "🏭"
    COLUMNS  = [("id","ID",220),("name","Name",160),
                ("contact_email","Email",185),("phone","Phone",130),
                ("address","Address",220)]

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

    def open_update_all_dialog(self):
        fields = [(k, l, False, None) for k, l, _, _ in self._fields()]
        def submit(data):
            if not data:
                messagebox.showinfo("No changes", "Fill in at least one field."); return
            try:
                r = api_put(f"{self.ENDPOINT}/bulk-update", data)
                messagebox.showinfo("Update All", r.get("message","Done")); self.refresh()
            except Exception as exc: messagebox.showerror("Error", _api_error(exc))
        FormDialog(self, f"Update All Suppliers — fill only fields to change", fields, submit)


# ─────────────────────────────────────────────────────────────────────────────
# Products
# ─────────────────────────────────────────────────────────────────────────────

class ProductsFrame(CRUDFrame):
    ENDPOINT = "/products"
    TITLE    = "Products"
    ICON     = "📦"
    COLUMNS  = [("id","ID",220),("name","Name",155),("barcode","Barcode",140),
                ("price","Price ($)",90),("stock","Stock",70),
                ("supplier_name","Supplier",165),("description","Desc",170)]

    def __init__(self, parent, *args, **kw):
        self._supplier_map: dict[str, str] = {}
        super().__init__(parent, *args, **kw)

    def refresh(self, _silent: bool = False):
        try:
            suppliers = api_get("/suppliers")
            self._supplier_map = {s["id"]: s["name"] for s in suppliers}
        except Exception:
            pass
        super().refresh(_silent=_silent)

    def get_row_values(self, doc):
        sid = doc.get("supplier_id", "")
        sname = self._supplier_map.get(sid, sid)
        return [doc.get("id",""), doc.get("name",""), doc.get("barcode",""),
                doc.get("price",""), doc.get("stock",""),
                sname, doc.get("description","")]

    def _get_supplier_choices(self):
        try:
            suppliers = api_get("/suppliers")
            return [("", "— None —")] + [
                (s["id"], f"{s['name']}  ({s['id'][:8]}…)")
                for s in suppliers
            ]
        except Exception:
            return []

    def _fields(self, doc=None):
        d = doc or {}
        supplier_choices = self._get_supplier_choices()
        fields = [("name","Name",True,d.get("name")),
                  ("price","Price",True,d.get("price")),
                  ("stock","Stock (qty)",False,d.get("stock",0))]
        if supplier_choices:
            fields.append(("supplier_id","Supplier",False,d.get("supplier_id"),supplier_choices))
        else:
            fields.append(("supplier_id","Supplier ID",False,d.get("supplier_id")))
        fields.append(("description","Description",False,d.get("description")))
        return fields

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

    def open_update_all_dialog(self):
        base = self._fields()
        fields = [(k, l, False, None) + ((f[4],) if len(f) > 4 else ())
                  for f in base for k, l, _, _ in [f[:4]]]
        def submit(data):
            if not data:
                messagebox.showinfo("No changes", "Fill in at least one field."); return
            try:
                if "price" in data: data["price"] = float(data["price"])
                if "stock" in data: data["stock"] = int(data["stock"])
                r = api_put(f"{self.ENDPOINT}/bulk-update", data)
                messagebox.showinfo("Update All", r.get("message","Done")); self.refresh()
            except ValueError: messagebox.showerror("Error","Price/Stock must be numbers.")
            except Exception as exc: messagebox.showerror("Error", _api_error(exc))
        FormDialog(self, f"Update All Products — fill only fields to change", fields, submit)


# ─────────────────────────────────────────────────────────────────────────────
# Customers
# ─────────────────────────────────────────────────────────────────────────────

class CustomersFrame(CRUDFrame):
    ENDPOINT = "/customers"
    TITLE    = "Customers"
    ICON     = "👤"
    COLUMNS  = [("id","ID",220),("name","Name",160),("email","Email",185),
                ("phone","Phone",130),("address","Address",220)]

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

    def open_update_all_dialog(self):
        fields = [(k, l, False, None) for k, l, _, _ in self._fields()]
        def submit(data):
            if not data:
                messagebox.showinfo("No changes", "Fill in at least one field."); return
            try:
                r = api_put(f"{self.ENDPOINT}/bulk-update", data)
                messagebox.showinfo("Update All", r.get("message","Done")); self.refresh()
            except Exception as exc: messagebox.showerror("Error", _api_error(exc))
        FormDialog(self, f"Update All Customers — fill only fields to change", fields, submit)


# ─────────────────────────────────────────────────────────────────────────────
# Invoices
# ─────────────────────────────────────────────────────────────────────────────

class InvoicesFrame(CRUDFrame):
    ENDPOINT = "/invoices"
    TITLE    = "Invoices"
    ICON     = "📄"
    COLUMNS  = [("id","ID",220),("customer_name","Customer",170),
                ("subtotal","Subtotal",100),("tax","Tax",80),("total","Total",100),
                ("status","Status",90),("created_at","Created",170)]

    def __init__(self, parent, *args, **kw):
        self._customer_map: dict[str, str] = {}
        super().__init__(parent, *args, **kw)

    def refresh(self, _silent: bool = False):
        try:
            customers = api_get("/customers")
            self._customer_map = {c["id"]: c["name"] for c in customers}
        except Exception:
            pass
        super().refresh(_silent=_silent)

    def get_row_values(self, doc):
        cid = doc.get("customer_id", "")
        cname = self._customer_map.get(cid, cid)
        return [doc.get("id",""), cname,
                doc.get("subtotal",""), doc.get("tax",""), doc.get("total",""),
                doc.get("status",""),
                doc.get("created_at","")[:19].replace("T"," ")
                if doc.get("created_at") else ""]

    def _get_customer_choices(self):
        try:
            customers = api_get("/customers")
            return [(c["id"], f"{c['name']}  ({c['id'][:8]}\u2026)") for c in customers]
        except Exception:
            return []

    def _fields(self, doc=None):
        d = doc or {}
        customer_choices = self._get_customer_choices()
        fields = []
        if customer_choices:
            fields.append(("customer_id","Customer",True,d.get("customer_id"),customer_choices))
        else:
            fields.append(("customer_id","Customer ID",True,d.get("customer_id")))
        fields += [("subtotal","Subtotal",True,d.get("subtotal")),
                   ("tax","Tax",False,d.get("tax",0)),
                   ("total","Total",True,d.get("total")),
                   ("status","Status",False,d.get("status","draft"))]
        return fields

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

    def open_update_all_dialog(self):
        base = self._fields()
        fields = [(f[0], f[1], False, None) + ((f[4],) if len(f) > 4 else ())
                  for f in base]
        def submit(data):
            if not data:
                messagebox.showinfo("No changes", "Fill in at least one field."); return
            try:
                if "subtotal" in data: data["subtotal"]=float(data["subtotal"])
                if "total"    in data: data["total"]=float(data["total"])
                if "tax"      in data: data["tax"]=float(data["tax"])
                r = api_put(f"{self.ENDPOINT}/bulk-update", data)
                messagebox.showinfo("Update All", r.get("message","Done")); self.refresh()
            except ValueError: messagebox.showerror("Error","Numbers required for subtotal/tax/total.")
            except Exception as exc: messagebox.showerror("Error", _api_error(exc))
        FormDialog(self, f"Update All Invoices — fill only fields to change", fields, submit)

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
    COLUMNS  = [("id","ID",220),("invoice_label","Invoice",190),
                ("product_name","Product",170),("quantity","Qty",65),
                ("unit_price","Unit Price $",100),("line_total","Line Total $",105)]

    def __init__(self, parent, *args, **kw):
        self._invoice_map: dict[str, str] = {}
        self._product_map: dict[str, str] = {}
        super().__init__(parent, *args, **kw)

    def refresh(self, _silent: bool = False):
        try:
            invoices = api_get("/invoices")
            self._invoice_map = {inv["id"]: f"#{inv['id'][:8]}\u2026 ${inv.get('total','')}" for inv in invoices}
        except Exception:
            pass
        try:
            products = api_get("/products")
            self._product_map = {p["id"]: p["name"] for p in products}
        except Exception:
            pass
        super().refresh(_silent=_silent)

    def get_row_values(self, doc):
        inv_id = doc.get("invoice_id", "")
        prod_id = doc.get("product_id", "")
        return [doc.get("id",""),
                self._invoice_map.get(inv_id, inv_id),
                self._product_map.get(prod_id, prod_id),
                doc.get("quantity",""),
                doc.get("unit_price",""), doc.get("line_total","")]

    def _get_invoice_choices(self):
        try:
            invoices = api_get("/invoices")
            return [(inv["id"], f"#{inv['id'][:8]}\u2026  ${inv.get('total','')}  [{inv.get('status','')}]")
                    for inv in invoices]
        except Exception:
            return []

    def _get_product_choices(self):
        try:
            products = api_get("/products")
            return [(p["id"], f"{p['name']}  (Stock:{p.get('stock','?')})")
                    for p in products]
        except Exception:
            return []

    def _fields(self, doc=None):
        d = doc or {}
        invoice_choices = self._get_invoice_choices()
        product_choices = self._get_product_choices()
        fields = []
        if invoice_choices:
            fields.append(("invoice_id","Invoice",True,d.get("invoice_id"),invoice_choices))
        else:
            fields.append(("invoice_id","Invoice ID",True,d.get("invoice_id")))
        if product_choices:
            fields.append(("product_id","Product",True,d.get("product_id"),product_choices))
        else:
            fields.append(("product_id","Product ID",True,d.get("product_id")))
        fields += [("quantity","Quantity",True,d.get("quantity")),
                   ("unit_price","Unit Price",True,d.get("unit_price"))]
        return fields

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

    def open_update_all_dialog(self):
        base = self._fields()
        fields = [(f[0], f[1], False, None) + ((f[4],) if len(f) > 4 else ())
                  for f in base]
        def submit(data):
            if not data:
                messagebox.showinfo("No changes", "Fill in at least one field."); return
            try:
                if "quantity"   in data: data["quantity"]=int(data["quantity"])
                if "unit_price" in data: data["unit_price"]=float(data["unit_price"])
                r = api_put(f"{self.ENDPOINT}/bulk-update", data)
                messagebox.showinfo("Update All", r.get("message","Done")); self.refresh()
            except ValueError: messagebox.showerror("Error","Quantity=int, Unit Price=number.")
            except Exception as exc: messagebox.showerror("Error", _api_error(exc))
        FormDialog(self, f"Update All Invoice Items — fill only fields to change", fields, submit)


# ─────────────────────────────────────────────────────────────────────────────
# Dashboard — polished stat cards
# ─────────────────────────────────────────────────────────────────────────────

class DashboardFrame(tk.Frame):
    def __init__(self, parent, *args, **kw):
        super().__init__(parent, bg=BG, *args, **kw)
        self._build()
        self.after(400, self.refresh)
        self.after(5000, self._auto_refresh)

    def _auto_refresh(self):
        try:
            self.refresh()
        except Exception:
            pass
        self.after(5000, self._auto_refresh)

    def _stat_card(self, parent, icon, title, count_var, colour):
        # Outer shadow frame
        shadow = tk.Frame(parent, bg=CARD_SHADOW)
        shadow.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=8, pady=(0, 4))
        card = tk.Frame(shadow, bg=CARD_BG,
                        highlightbackground=colour, highlightthickness=2,
                        padx=22, pady=18)
        card.pack(fill=tk.BOTH, expand=True, padx=(0, 2), pady=(0, 2))
        tk.Label(card, text=icon, bg=CARD_BG, font=FONT_ICON).pack(anchor="w")
        tk.Label(card, textvariable=count_var, bg=CARD_BG, fg=colour,
                 font=FONT_BIG).pack(anchor="w", pady=(4, 0))
        tk.Label(card, text=title, bg=CARD_BG, fg="#6b7280",
                 font=FONT_LBL).pack(anchor="w", pady=(2, 0))

    def _build(self):
        # Title
        hdr = tk.Frame(self, bg=BG)
        hdr.pack(fill=tk.X, padx=26, pady=(24, 6))
        tk.Label(hdr, text="📊  Dashboard", bg=BG, fg="#1e293b",
                 font=(FONT, 20, "bold")).pack(side=tk.LEFT)

        tk.Label(self, text="Live overview of your inventory & billing data",
                 bg=BG, fg="#6b7280",
                 font=FONT_LBL).pack(anchor="w", padx=26, pady=(0, 18))

        # Stat cards row
        row = tk.Frame(self, bg=BG)
        row.pack(fill=tk.X, padx=18, pady=(0, 16))
        self._v_sup   = tk.StringVar(value="...")
        self._v_pro   = tk.StringVar(value="...")
        self._v_cus   = tk.StringVar(value="...")
        self._v_inv   = tk.StringVar(value="...")
        self._v_items = tk.StringVar(value="...")
        self._stat_card(row, "🏭", "Suppliers",     self._v_sup,   "#7c3aed")
        self._stat_card(row, "📦", "Products",      self._v_pro,   "#059669")
        self._stat_card(row, "👤", "Customers",     self._v_cus,   "#2563eb")
        self._stat_card(row, "📄", "Invoices",      self._v_inv,   "#d97706")
        self._stat_card(row, "🔖", "Invoice Items", self._v_items, "#dc2626")

        # Quick tips card
        tip_card = tk.Frame(self, bg=CARD_BG,
                            highlightbackground=CARD_BORDER, highlightthickness=1)
        tip_card.pack(fill=tk.X, padx=26, pady=(0, 10))
        tip_hdr = tk.Frame(tip_card, bg=ACCENT, height=40)
        tip_hdr.pack(fill=tk.X)
        tip_hdr.pack_propagate(False)
        tk.Label(tip_hdr, text="   Quick Tips", bg=ACCENT, fg="#ffffff",
                 font=(FONT, 11, "bold")).pack(side=tk.LEFT, pady=8)

        tip_body = tk.Frame(tip_card, bg=CARD_BG, padx=20, pady=12)
        tip_body.pack(fill=tk.X)
        for t in [
            "Use the sidebar to navigate between sections.",
            "Double-click any row in a table to edit it.",
            "Click a column header to sort ascending / descending.",
            "Use the Search bar to filter records in real time.",
            "The Billing section creates invoices with auto stock deduction.",
        ]:
            row_tip = tk.Frame(tip_body, bg=CARD_BG)
            row_tip.pack(fill=tk.X, pady=3)
            tk.Label(row_tip, text="  •  ", bg=CARD_BG, fg=ACCENT,
                     font=(FONT, 11, "bold")).pack(side=tk.LEFT)
            tk.Label(row_tip, text=t, bg=CARD_BG, fg="#4b5563",
                     font=FONT_LBL, anchor="w").pack(side=tk.LEFT)

        # Refresh button
        ModernButton(self, "  Refresh Stats  ", BTN_GREY, BTN_GREY_H,
                     command=self.refresh).pack(anchor="w", padx=26, pady=12)

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
        super().__init__(parent, bg=BG, *args, **kw)
        self._line_items: list[dict] = []
        self._customers:  list[dict] = []
        self._products:   list[dict] = []
        self._build()
        self.after(400, self._reload)
        self.after(10000, self._auto_reload)

    def _auto_reload(self):
        try:
            self._reload()
        except Exception:
            pass
        self.after(10000, self._auto_reload)

    def _build(self):
        # Title
        tk.Label(self, text="💳  Create Billing Invoice",
                 bg=BG, fg="#1e293b",
                 font=(FONT, 18, "bold")).pack(anchor="w", padx=26, pady=(22, 10))

        # Customer + tax card
        hd = tk.Frame(self, bg=CARD_BG,
                      highlightbackground=CARD_BORDER, highlightthickness=1)
        hd.pack(fill=tk.X, padx=26, pady=(0, 12))
        inner = tk.Frame(hd, bg=CARD_BG)
        inner.pack(fill=tk.X, padx=18, pady=14)
        tk.Label(inner, text="Customer:", bg=CARD_BG, fg="#374151",
                 font=(FONT, 10, "bold")).grid(row=0, column=0,
                                               sticky="w", padx=(0, 10))
        self.customer_var = tk.StringVar()
        self.customer_cb  = ttk.Combobox(inner, textvariable=self.customer_var,
                                          width=44, state="readonly",
                                          font=FONT_ENTRY)
        self.customer_cb.grid(row=0, column=1, padx=(0, 24))
        tk.Label(inner, text="Tax Rate (%):", bg=CARD_BG, fg="#374151",
                 font=(FONT, 10, "bold")).grid(row=0, column=2,
                                               sticky="w", padx=(0, 10))
        self.tax_var = tk.StringVar(value="0")
        tk.Entry(inner, textvariable=self.tax_var, width=8,
                 font=FONT_ENTRY, relief="solid", bd=1,
                 bg="#f8fafd", fg="#1f2937",
                 highlightcolor="#5b8bd4", highlightthickness=1).grid(
            row=0, column=3, ipady=5)
        self.tax_var.trace_add("write", lambda *_: self._update_summary())
        ModernButton(inner, "  Reload  ", BTN_GREY, BTN_GREY_H,
                     command=self._reload).grid(row=0, column=4, padx=(18, 0))

        # Line items card
        li_card = tk.Frame(self, bg=CARD_BG,
                           highlightbackground=CARD_BORDER, highlightthickness=1)
        li_card.pack(fill=tk.BOTH, expand=True, padx=26, pady=(0, 12))

        li_title = tk.Frame(li_card, bg=ACCENT, height=38)
        li_title.pack(fill=tk.X)
        li_title.pack_propagate(False)
        tk.Label(li_title, text="   Line Items", bg=ACCENT, fg="#ffffff",
                 font=(FONT, 11, "bold")).pack(side=tk.LEFT, pady=8)

        add_row = tk.Frame(li_card, bg=CARD_BG)
        add_row.pack(fill=tk.X, padx=16, pady=12)
        tk.Label(add_row, text="Product:", bg=CARD_BG, fg="#374151",
                 font=(FONT, 10, "bold")).pack(side=tk.LEFT)
        self.product_var = tk.StringVar()
        self.product_cb  = ttk.Combobox(add_row, textvariable=self.product_var,
                                         width=48, state="readonly",
                                         font=FONT_ENTRY)
        self.product_cb.pack(side=tk.LEFT, padx=(8, 16))
        tk.Label(add_row, text="Qty:", bg=CARD_BG, fg="#374151",
                 font=(FONT, 10, "bold")).pack(side=tk.LEFT)
        self.qty_var = tk.StringVar(value="1")
        tk.Entry(add_row, textvariable=self.qty_var, width=6,
                 font=FONT_ENTRY, relief="solid", bd=1,
                 bg="#f8fafd").pack(side=tk.LEFT, padx=(6, 14), ipady=5)
        ModernButton(add_row, "  + Add Line  ", BTN_GREEN, BTN_GREEN_H,
                     command=self._add_line).pack(side=tk.LEFT, padx=(0, 8))
        ModernButton(add_row, "  Remove  ", BTN_RED, BTN_RED_H,
                     command=self._remove_line).pack(side=tk.LEFT)

        cols = ("product_id","product_name","quantity","unit_price","line_total")
        self.lines_tree = ttk.Treeview(li_card, columns=cols, show="headings", height=8)
        for key, heading, width in [
            ("product_id",   "Product ID",   190),
            ("product_name", "Product Name", 200),
            ("quantity",     "Qty",           65),
            ("unit_price",   "Unit Price $",  120),
            ("line_total",   "Line Total $",  120),
        ]:
            self.lines_tree.heading(key, text=f"  {heading}", anchor="w")
            self.lines_tree.column(key, width=width, anchor="w")
        vsb = ttk.Scrollbar(li_card, orient=tk.VERTICAL,
                             command=self.lines_tree.yview)
        self.lines_tree.configure(yscrollcommand=vsb.set)
        self.lines_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True,
                              padx=(16, 0), pady=(0, 12))
        vsb.pack(side=tk.RIGHT, fill=tk.Y, pady=(0, 12), padx=(0, 10))

        # Summary footer
        foot = tk.Frame(self, bg=CARD_BG,
                        highlightbackground=CARD_BORDER, highlightthickness=1)
        foot.pack(fill=tk.X, padx=26, pady=(0, 20))
        inner2 = tk.Frame(foot, bg=CARD_BG)
        inner2.pack(fill=tk.X, padx=18, pady=12)
        self.summary_lbl = tk.Label(inner2,
                                     text="Subtotal: —   Tax: —   Total: —",
                                     bg=CARD_BG, fg="#1e293b",
                                     font=(FONT, 13, "bold"))
        self.summary_lbl.pack(side=tk.LEFT)
        ModernButton(inner2, "  💳  Issue Invoice  ", BTN_GREEN, BTN_GREEN_H,
                     command=self._submit).pack(side=tk.RIGHT, padx=(10, 0))
        ModernButton(inner2, "  Clear  ", BTN_RED, BTN_RED_H,
                     command=self._clear).pack(side=tk.RIGHT, padx=(0, 8))

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
                f"{p['name']}  |  Barcode: {p.get('barcode','?')}  |  Stock: {p['stock']}  |  ${p['price']}"
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
            messagebox.showinfo("Invoice Created",
                f"Invoice created successfully!\n\n"
                f"ID:       {inv.get('id','')}\n"
                f"Total:   ${inv.get('total','')}\n"
                f"Status:  {inv.get('status','')}")
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
                                   font=(FONT, 15), width=3, anchor="e")
        self._icon_lbl.pack(side=tk.LEFT, padx=(14, 6))
        self._text_lbl = tk.Label(self, text=label, bg=SB_BG, fg=SB_FG,
                                   font=FONT_NAV, anchor="w")
        self._text_lbl.pack(side=tk.LEFT, fill=tk.X, expand=True, pady=12)
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
                               font=(FONT, 11,
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
        self.geometry("1340x760")
        self.minsize(1100, 620)
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
        style.configure("Treeview",         rowheight=32, font=FONT_LBL)
        style.configure("Treeview.Heading", font=(FONT, 10, "bold"),
                        background=HDR_TBL, foreground="#1e293b")
        style.configure("TCombobox",        font=FONT_ENTRY)
        style.map("Treeview",
                  background=[("selected", ROW_SEL)],
                  foreground=[("selected", "#0f172a")])

    def _build_ui(self):
        # ── Sidebar ───────────────────────────────────────────────────────────
        self._sidebar = tk.Frame(self, bg=SB_BG, width=220)
        self._sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self._sidebar.pack_propagate(False)

        # Logo
        logo_frame = tk.Frame(self._sidebar, bg=SB_BG, height=80)
        logo_frame.pack(fill=tk.X)
        logo_frame.pack_propagate(False)
        tk.Label(logo_frame, text="📦", bg=SB_BG, fg="#ffffff",
                 font=(FONT, 24)).pack(side=tk.LEFT, padx=(18, 8), pady=20)
        tk.Label(logo_frame, text="Inventory &\nBilling Manager", bg=SB_BG, fg="#ffffff",
                 font=FONT_LOGO,
                 justify="left").pack(side=tk.LEFT, pady=20)

        # Divider
        tk.Frame(self._sidebar, bg="#1a2d4a", height=2).pack(fill=tk.X, padx=16, pady=(0, 6))

        # Nav buttons
        self._nav_btns: list[SidebarBtn] = []
        for icon, label, _ in self._PAGES:
            btn = SidebarBtn(
                self._sidebar, icon, label,
                command=lambda i=len(self._nav_btns): self._show_page(i))
            btn.pack(fill=tk.X)
            self._nav_btns.append(btn)

        # Footer
        tk.Frame(self._sidebar, bg=SB_BG).pack(fill=tk.BOTH, expand=True)
        tk.Label(self._sidebar, text=f"v3.0  ·  FastAPI + {DB_BRAND_TEXT}",
                 bg=SB_BG, fg="#3d5578",
                 font=FONT_TINY).pack(side=tk.BOTTOM, pady=10)

        # ── Right panel ───────────────────────────────────────────────────────
        right = tk.Frame(self, bg=BG)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Top header bar
        self._top_bar = tk.Frame(right, bg=HDR_BG, height=54)
        self._top_bar.pack(fill=tk.X)
        self._top_bar.pack_propagate(False)
        self._page_title = tk.Label(self._top_bar, text="",
                                     bg=HDR_BG, fg="white",
                                     font=(FONT, 14, "bold"), anchor="w")
        self._page_title.pack(side=tk.LEFT, padx=24, pady=14)
        tk.Label(self._top_bar, text=f"{DB_BRAND_TEXT}  ·  FastAPI  ·  Tkinter",
                 bg=HDR_BG, fg=HDR_SUB,
                 font=FONT_SMALL, anchor="e").pack(side=tk.RIGHT, padx=22)

        # Page stacker
        self._container = tk.Frame(right, bg=BG)
        self._container.pack(fill=tk.BOTH, expand=True)
        self._container.rowconfigure(0, weight=1)
        self._container.columnconfigure(0, weight=1)

        self._pages: list[tk.Frame] = []
        for _, label, cls in self._PAGES:
            frame = cls(self._container)
            frame.grid(row=0, column=0, sticky="nsew")
            self._pages.append(frame)

        # Status bar
        status = tk.Frame(right, bg="#e4ecf7",
                          highlightbackground=CARD_BORDER,
                          highlightthickness=1, height=28)
        status.pack(fill=tk.X, side=tk.BOTTOM)
        status.pack_propagate(False)
        tk.Label(status,
                 text=f"   API: {API_BASE}   ·   DB: {DATABASE_LABEL}",
                 bg="#e4ecf7", fg="#6b7280", font=FONT_SMALL,
                 anchor="w").pack(side=tk.LEFT, pady=5)
        tk.Label(status, text=f"●  {DB_STATUS_TEXT}",
                 bg="#e4ecf7", fg=DB_STATUS_COLOR,
                 font=(FONT, 9, "bold")).pack(side=tk.RIGHT, padx=18)

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

    # 2. Splash screen
    splash = tk.Tk()
    splash.overrideredirect(True)
    splash.configure(bg=SB_BG)
    splash.geometry("460x220")
    splash.eval("tk::PlaceWindow . center")
    tk.Label(splash, text="📦", bg=SB_BG, fg="white",
             font=(FONT, 40)).pack(pady=(28, 4))
    tk.Label(splash, text="Inventory & Billing Manager",
             bg=SB_BG, fg="white",
             font=(FONT, 14, "bold")).pack()
    tk.Label(splash, text="Starting API server...",
             bg=SB_BG, fg="#5b8bd4",
             font=FONT_LBL).pack(pady=(8, 12))
    pb = ttk.Progressbar(splash, mode="indeterminate", length=300)
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
            "If MongoDB is unavailable, set INVENTORY_DB_MODE=memory and try again.")
        return

    # 3. Launch main window
    App().mainloop()


if __name__ == "__main__":
    main()
