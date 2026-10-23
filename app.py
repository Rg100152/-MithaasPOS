"""
MithaasPOS - Ultimate Sweet Shop Billing & ERP Software
Single-File Flask Application with SQLite Database
Run: python app.py
Open: http://127.0.0.1:5000
"""

import json
import random
import uuid
import sqlite3
from datetime import datetime, timedelta
from contextlib import contextmanager
from flask import Flask, render_template_string, request, jsonify, session, g

app = Flask(__name__)
app.secret_key = "mithaas_pos_secret_key_festive_2026"

DB_PATH = "mithaas_pos.db"

# ------------------------------------------------------------------
# DATABASE LAYER
# ------------------------------------------------------------------
def get_db():
    """Get request-scoped DB connection."""
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db

@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()

@contextmanager
def db_context():
    """Standalone context manager for non-request contexts."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Create tables and seed initial data if empty."""
    with db_context() as conn:
        c = conn.cursor()

        # ---------- SWEETS TABLE ----------
        c.execute("""
            CREATE TABLE IF NOT EXISTS sweets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                price REAL NOT NULL,
                unit TEXT DEFAULT 'kg',
                stock REAL DEFAULT 0,
                shelf_life_days INTEGER DEFAULT 5,
                mfg_date TEXT,
                expiry_date TEXT,
                batch TEXT,
                img TEXT,
                color TEXT,
                gst_pct REAL DEFAULT 5
            )
        """)

        # ---------- ORDERS TABLE ----------
        c.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_id TEXT UNIQUE NOT NULL,
                customer TEXT DEFAULT 'Walk-in',
                phone TEXT,
                subtotal REAL DEFAULT 0,
                tax REAL DEFAULT 0,
                grand_total REAL DEFAULT 0,
                payment_mode TEXT DEFAULT 'CASH',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ---------- ORDER ITEMS ----------
        c.execute("""
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                sweet_id INTEGER,
                name TEXT NOT NULL,
                weight REAL NOT NULL,
                price REAL NOT NULL,
                gst_pct REAL DEFAULT 5,
                line_total REAL NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
            )
        """)

        # ---------- ADVANCE BOOKINGS ----------
        c.execute("""
            CREATE TABLE IF NOT EXISTS advance_bookings (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                sweet_type TEXT,
                qty INTEGER DEFAULT 1,
                delivery_date TEXT,
                advance_paid REAL DEFAULT 0,
                total_estimated REAL DEFAULT 0,
                notes TEXT,
                status TEXT DEFAULT 'Confirmed',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ---------- SEED SWEETS (only if empty) ----------
        c.execute("SELECT COUNT(*) as cnt FROM sweets")
        if c.fetchone()["cnt"] == 0:
            now = datetime.now()
            seeds = [
                ("Kaju Katli", "Dry Fruit", 850, "kg", 18.5, 20,
                 (now - timedelta(days=2)).strftime("%Y-%m-%d"),
                 (now + timedelta(days=18)).strftime("%Y-%m-%d"),
                 "KK-2026-A1",
                 "https://images.unsplash.com/photo-1601050690597-df0568f70950?auto=format&fit=crop&w=600&q=80",
                 "#f5c518", 5),
                ("Kesar Rasgulla", "Fresh Sweets", 340, "kg", 12.0, 2,
                 now.strftime("%Y-%m-%d"),
                 (now + timedelta(days=2)).strftime("%Y-%m-%d"),
                 "RG-2026-F1",
                 "https://images.unsplash.com/photo-1541781774459-bb2af2f05b55?auto=format&fit=crop&w=600&q=80",
                 "#ffffff", 5),
                ("Shahi Gulab Jamun", "Fresh Sweets", 380, "kg", 25.0, 3,
                 now.strftime("%Y-%m-%d"),
                 (now + timedelta(days=3)).strftime("%Y-%m-%d"),
                 "GJ-2026-F2",
                 "https://images.unsplash.com/photo-1589301760014-d929f3979dbc?auto=format&fit=crop&w=600&q=80",
                 "#8b4513", 5),
                ("Motichoor Ladoo", "Fresh Sweets", 440, "kg", 4.5, 7,
                 (now - timedelta(days=1)).strftime("%Y-%m-%d"),
                 (now + timedelta(days=6)).strftime("%Y-%m-%d"),
                 "ML-2026-B3",
                 "https://images.unsplash.com/photo-1599488615731-7e5c2823ff28?auto=format&fit=crop&w=600&q=80",
                 "#ff8c00", 5),
                ("Desi Ghee Jalebi", "Fresh Sweets", 320, "kg", 15.0, 1,
                 now.strftime("%Y-%m-%d"),
                 (now + timedelta(days=1)).strftime("%Y-%m-%d"),
                 "JB-2026-EX",
                 "https://images.unsplash.com/photo-1589301760014-d929f3979dbc?auto=format&fit=crop&w=600&q=80",
                 "#ffd700", 5),
                ("Mathura Peda", "Milk Sweets", 480, "kg", 19.0, 6,
                 (now - timedelta(days=1)).strftime("%Y-%m-%d"),
                 (now + timedelta(days=5)).strftime("%Y-%m-%d"),
                 "PD-2026-M1",
                 "https://images.unsplash.com/photo-1541781774459-bb2af2f05b55?auto=format&fit=crop&w=600&q=80",
                 "#f0c040", 5),
                ("Kesar Malai Barfi", "Milk Sweets", 640, "kg", 5.0, 5,
                 now.strftime("%Y-%m-%d"),
                 (now + timedelta(days=5)).strftime("%Y-%m-%d"),
                 "MB-2026-M2",
                 "https://images.unsplash.com/photo-1601050690597-df0568f70950?auto=format&fit=crop&w=600&q=80",
                 "#e8e8e8", 5),
                ("Flaky Soan Papdi", "Dry Fruit", 360, "kg", 2.5, 30,
                 (now - timedelta(days=5)).strftime("%Y-%m-%d"),
                 (now + timedelta(days=25)).strftime("%Y-%m-%d"),
                 "SP-2026-D1",
                 "https://images.unsplash.com/photo-1599488615731-7e5c2823ff28?auto=format&fit=crop&w=600&q=80",
                 "#f5deb3", 5),
                ("Royal Rabri", "Milk Sweets", 520, "kg", 6.0, 1,
                 now.strftime("%Y-%m-%d"),
                 now.strftime("%Y-%m-%d"),
                 "RB-2026-EX",
                 "https://images.unsplash.com/photo-1541781774459-bb2af2f05b55?auto=format&fit=crop&w=600&q=80",
                 "#fff8dc", 5),
                ("Festive Assorted Gift Box", "Gift Boxes", 1250, "box", 35, 15,
                 now.strftime("%Y-%m-%d"),
                 (now + timedelta(days=15)).strftime("%Y-%m-%d"),
                 "GB-2026-X1",
                 "https://images.unsplash.com/photo-1601050690597-df0568f70950?auto=format&fit=crop&w=600&q=80",
                 "#d4af37", 12),
                ("Special Shahi Dry Fruit Hamper", "Gift Boxes", 2100, "box", 14, 45,
                 now.strftime("%Y-%m-%d"),
                 (now + timedelta(days=45)).strftime("%Y-%m-%d"),
                 "DFH-2026-VVIP",
                 "https://images.unsplash.com/photo-1599488615731-7e5c2823ff28?auto=format&fit=crop&w=600&q=80",
                 "#800020", 12),
                ("Special Samosa & Namkeen", "Namkeen", 220, "kg", 30.0, 3,
                 now.strftime("%Y-%m-%d"),
                 (now + timedelta(days=3)).strftime("%Y-%m-%d"),
                 "NK-2026-S1",
                 "https://images.unsplash.com/photo-1601050690597-df0568f70950?auto=format&fit=crop&w=600&q=80",
                 "#cd853f", 12),
            ]
            c.executemany("""
                INSERT INTO sweets
                (name, category, price, unit, stock, shelf_life_days,
                 mfg_date, expiry_date, batch, img, color, gst_pct)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
            """, seeds)

        # ---------- SEED SAMPLE ORDER ----------
        c.execute("SELECT COUNT(*) as cnt FROM orders")
        if c.fetchone()["cnt"] == 0:
            c.execute("""
                INSERT INTO orders (invoice_id, customer, phone, subtotal, tax, grand_total, payment_mode, created_at)
                VALUES (?,?,?,?,?,?,?,?)
            """, ("MITH-10024", "Rajesh Sharma", "+91 98230 11223",
                  1070, 53.5, 1123.5, "UPI / GPay",
                  (datetime.now() - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S")))
            order_id = c.lastrowid
            c.executemany("""
                INSERT INTO order_items (order_id, sweet_id, name, weight, price, gst_pct, line_total)
                VALUES (?,?,?,?,?,?,?)
            """, [
                (order_id, 1, "Kaju Katli", 1.0, 850, 5, 850),
                (order_id, 4, "Motichoor Ladoo", 0.5, 440, 5, 220),
            ])

        # ---------- SEED ADVANCE BOOKINGS ----------
        c.execute("SELECT COUNT(*) as cnt FROM advance_bookings")
        if c.fetchone()["cnt"] == 0:
            c.executemany("""
                INSERT INTO advance_bookings
                (id, name, phone, sweet_type, qty, delivery_date,
                 advance_paid, total_estimated, notes, status, created_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """, [
                ("ORD-BK-8841", "Sunil Varma", "+91 98765 43210",
                 "Diwali Special Assorted Gift Box", 50,
                 (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d"),
                 5000, 25000, "Premium Red Satin Ribbon Packaging",
                 "In-Prep",
                 (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M")),
                ("ORD-BK-9120", "Ananya Roy (Wedding)", "+91 91234 56789",
                 "Custom Kaju Katli + Dry Fruit Box", 120,
                 (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
                 15000, 60000, "Gold foil embossed box with family name tag",
                 "Confirmed",
                 datetime.now().strftime("%Y-%m-%d %H:%M")),
            ])


def rows_to_dicts(rows):
    return [dict(r) for r in rows]


# ------------------------------------------------------------------
# TEMPLATE (unchanged from your original — only JS fetch paths same)
# ------------------------------------------------------------------
LANDING_HTML = r"""
<!DOCTYPE html>
<html lang="hi">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MithaasPOS — Sweet Shop POS, Weighing Scale & ERP Software</title>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=Playfair+Display:ital,wght@0,600;0,800;1,600&display=swap" rel="stylesheet">
<script src="https://cdn.tailwindcss.com"></script>
<script>
  tailwind.config = {
    theme: {
      extend: {
        colors: {
          saffron: '#E67E22', saffronGold: '#F39C12',
          pista: '#27AE60', pistaDark: '#1E8449',
          charcoal: '#1A1A1A', creamGold: '#FFFDF7',
          cardBg: '#FFFFFF', danger: '#E74C3C', amber: '#F1C40F'
        },
        fontFamily: {
          sans: ['"Plus Jakarta Sans"', 'sans-serif'],
          serif: ['"Playfair Display"', 'serif']
        }
      }
    }
  }
</script>
<style>
  body { background-color: #FFFDF7; color: #1A1A1A; font-family: 'Plus Jakarta Sans', sans-serif; overflow-x: hidden; }
  .glass-nav { background: rgba(255, 253, 247, 0.92); backdrop-filter: blur(12px); border-bottom: 1px solid rgba(230, 126, 34, 0.15); }
  .hero-gradient { background: radial-gradient(circle at 85% 15%, #FFEAD2 0%, #FFFDF7 60%); }
  .fly-item { position: fixed; z-index: 9999; pointer-events: none; transition: all 0.75s cubic-bezier(0.18, 0.89, 0.32, 1.28); border-radius: 50%; object-fit: cover; }
  @keyframes pulseGlow { 0%, 100% { opacity: 1; transform: scale(1); } 50% { opacity: 0.6; transform: scale(1.08); } }
  .pulse-glow { animation: pulseGlow 1.8s infinite ease-in-out; }
  .confetti-particle { position: fixed; width: 10px; height: 10px; z-index: 10000; pointer-events: none; border-radius: 2px; }
  ::-webkit-scrollbar { width: 6px; height: 6px; }
  ::-webkit-scrollbar-track { background: #f1f1f1; border-radius: 10px; }
  ::-webkit-scrollbar-thumb { background: #E67E22; border-radius: 10px; }
  .receipt-font { font-family: 'Courier New', Courier, monospace; }
</style>
</head>
<body class="min-h-screen flex flex-col justify-between">

<!-- NAV -->
<nav class="sticky top-0 z-50 glass-nav py-3 px-4 md:px-8">
  <div class="max-w-7xl mx-auto flex items-center justify-between">
    <div class="flex items-center gap-3">
      <div class="w-10 h-10 rounded-2xl bg-gradient-to-tr from-saffron to-saffronGold flex items-center justify-center text-white text-xl font-black shadow-lg shadow-saffron/30">🍬</div>
      <div>
        <span class="font-serif text-2xl font-extrabold tracking-tight text-saffron">Mithaas<span class="text-pista">POS</span></span>
        <span class="block text-[10px] uppercase font-bold tracking-widest text-gray-400 -mt-1">Sweet Shop ERP v3.5</span>
      </div>
    </div>
    <div class="hidden lg:flex items-center gap-6 bg-white/80 border border-amber-200/60 rounded-full px-5 py-1.5 shadow-sm">
      <div class="flex items-center gap-2">
        <span class="w-2.5 h-2.5 rounded-full bg-pista animate-pulse"></span>
        <span class="text-xs font-semibold text-gray-500">Today Sales:</span>
        <span class="text-sm font-bold text-gray-800" id="navTodaySales">₹24,850</span>
      </div>
      <div class="h-4 w-[1px] bg-gray-200"></div>
      <div class="flex items-center gap-2">
        <span class="text-xs font-semibold text-gray-500">Low Stock:</span>
        <span class="text-xs font-bold text-white bg-amber-500 px-2 py-0.5 rounded-full" id="navLowStockCount">0 Items</span>
      </div>
      <div class="h-4 w-[1px] bg-gray-200"></div>
      <div class="flex items-center gap-2">
        <span class="text-xs font-semibold text-gray-500">Expiry Alert:</span>
        <span class="text-xs font-bold text-white bg-danger px-2 py-0.5 rounded-full animate-bounce" id="navExpiryCount">0 Items</span>
      </div>
    </div>
    <div class="flex items-center gap-3">
      <button onclick="scrollToSection('pos')" class="bg-gradient-to-r from-saffron to-saffronGold text-white font-bold text-xs md:text-sm px-4 md:px-6 py-2.5 rounded-xl shadow-md hover:shadow-saffron/40 hover:-translate-y-0.5 transition-all">⚡ Open Live POS</button>
      <button onclick="scrollToSection('booking')" class="bg-gradient-to-r from-pista to-pistaDark text-white font-bold text-xs md:text-sm px-4 md:px-5 py-2.5 rounded-xl shadow-md hover:shadow-pista/40 hover:-translate-y-0.5 transition-all">🎁 Advance Booking</button>
    </div>
  </div>
</nav>

<!-- HERO -->
<section class="hero-gradient pt-8 pb-16 px-4 md:px-8">
  <div class="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-10 items-center">
    <div class="lg:col-span-6 space-y-6">
      <div class="inline-flex items-center gap-2 bg-saffron/10 border border-saffron/30 text-saffron px-3 py-1.5 rounded-full text-xs font-bold uppercase tracking-wider">
        <span>✨ India's #1 Sweet Shop Automation Platform</span>
      </div>
      <h1 class="font-serif text-4xl sm:text-5xl lg:text-6xl font-extrabold text-charcoal leading-tight">
        मिठाइयों की बिक्री, वजन और <span class="text-saffron">एडवांस बुकिंग</span> — अब एक ही जगह!
      </h1>
      <p class="text-gray-600 text-base sm:text-lg leading-relaxed">
        Live Bluetooth/USB Weighing Scale Sync, Tare Weight Auto-Deduction, Batch Expiry Warning Alerts, Festival Gift Box Customization and Instant UPI Payment QR Billing.
      </p>
      <div class="flex flex-wrap items-center gap-4 pt-2">
        <button onclick="scrollToSection('pos')" class="bg-saffron hover:bg-saffron/90 text-white font-bold text-base px-7 py-3.5 rounded-2xl shadow-xl shadow-saffron/30 transition-all">🍬 Start Billing Demo</button>
        <button onclick="openAnalyticsModal()" class="bg-white hover:bg-gray-50 border border-gray-300 text-gray-800 font-bold text-base px-6 py-3.5 rounded-2xl shadow-sm transition-all">📊 Live Analytics Dashboard</button>
      </div>
      <div class="grid grid-cols-3 gap-3 pt-4 border-t border-gray-200/80">
        <div><h4 class="text-xl font-bold text-saffron">100%</h4><p class="text-xs text-gray-500 font-medium">Auto Scale Sync</p></div>
        <div><h4 class="text-xl font-bold text-pista">0%</h4><p class="text-xs text-gray-500 font-medium">Wastage Expiry Alert</p></div>
        <div><h4 class="text-xl font-bold text-saffronGold">2 Sec</h4><p class="text-xs text-gray-500 font-medium">Thermal Invoice Print</p></div>
      </div>
    </div>
    <div class="lg:col-span-6 relative">
      <div class="relative z-10 bg-white p-4 rounded-3xl shadow-2xl border border-amber-100">
        <div class="flex items-center justify-between border-b pb-3 mb-3">
          <div class="flex items-center gap-2">
            <span class="w-3 h-3 rounded-full bg-red-400"></span>
            <span class="w-3 h-3 rounded-full bg-yellow-400"></span>
            <span class="w-3 h-3 rounded-full bg-green-400"></span>
            <span class="text-xs text-gray-400 font-mono ml-2">MithaasPOS Counter View</span>
          </div>
          <span class="text-xs font-bold bg-pista/10 text-pista px-2 py-0.5 rounded">SQLite Connected</span>
        </div>
        <img src="https://images.unsplash.com/photo-1556742049-0a670f4a45a1?auto=format&fit=crop&w=1000&q=80" alt="POS" class="rounded-2xl w-full h-72 object-cover">
        <div class="grid grid-cols-2 gap-3 mt-3">
          <div class="bg-creamGold p-3 rounded-xl border border-amber-200 flex items-center gap-3">
            <span class="text-2xl">⚖️</span>
            <div><p class="text-[10px] text-gray-500 uppercase font-bold">Weighing Machine</p><p class="text-sm font-extrabold text-saffron">0.750 Kg Ready</p></div>
          </div>
          <div class="bg-creamGold p-3 rounded-xl border border-amber-200 flex items-center gap-3">
            <span class="text-2xl">🖨️</span>
            <div><p class="text-[10px] text-gray-500 uppercase font-bold">Thermal Printer</p><p class="text-sm font-extrabold text-pista">2" ESC/POS Online</p></div>
          </div>
        </div>
      </div>
      <div class="absolute -top-10 -right-10 w-64 h-64 bg-saffron/20 rounded-full blur-3xl pointer-events-none"></div>
      <div class="absolute -bottom-10 -left-10 w-64 h-64 bg-pista/20 rounded-full blur-3xl pointer-events-none"></div>
    </div>
  </div>
</section>

<!-- POS -->
<section id="pos" class="py-10 px-4 md:px-8 max-w-7xl mx-auto">
  <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
    <div>
      <h2 class="font-serif text-3xl font-bold text-charcoal">🍬 Counter POS & Live Billing</h2>
      <p class="text-sm text-gray-500">Select sweets, adjust scale weight, customize box packing, and bill instantly.</p>
    </div>
    <div class="flex items-center gap-2 overflow-x-auto pb-2 md:pb-0" id="categoryTabs">
      <button onclick="filterCategory('All', event)" class="cat-btn active bg-saffron text-white text-xs font-bold px-4 py-2 rounded-xl">All Sweets</button>
      <button onclick="filterCategory('Fresh Sweets', event)" class="cat-btn bg-white hover:bg-gray-100 text-gray-700 text-xs font-bold px-4 py-2 rounded-xl border border-gray-200">Fresh Sweets</button>
      <button onclick="filterCategory('Milk Sweets', event)" class="cat-btn bg-white hover:bg-gray-100 text-gray-700 text-xs font-bold px-4 py-2 rounded-xl border border-gray-200">Milk Sweets</button>
      <button onclick="filterCategory('Dry Fruit', event)" class="cat-btn bg-white hover:bg-gray-100 text-gray-700 text-xs font-bold px-4 py-2 rounded-xl border border-gray-200">Dry Fruit</button>
      <button onclick="filterCategory('Gift Boxes', event)" class="cat-btn bg-white hover:bg-gray-100 text-gray-700 text-xs font-bold px-4 py-2 rounded-xl border border-gray-200">Gift Boxes</button>
      <button onclick="filterCategory('Namkeen', event)" class="cat-btn bg-white hover:bg-gray-100 text-gray-700 text-xs font-bold px-4 py-2 rounded-xl border border-gray-200">Namkeen</button>
    </div>
  </div>

  <div class="grid grid-cols-1 lg:grid-cols-12 gap-8">
    <div class="lg:col-span-7 xl:col-span-8 space-y-4">
      <div class="bg-white p-4 rounded-2xl border border-gray-200/80 shadow-sm flex flex-col sm:flex-row items-center gap-3 justify-between">
        <div class="relative w-full sm:w-80">
          <input type="text" id="searchInput" oninput="handleSearch(this.value)" placeholder="🔍 Search Kaju Katli, Rasgulla, Batch..." class="w-full bg-gray-50 border border-gray-200 rounded-xl px-4 py-2.5 text-sm font-medium focus:outline-none focus:border-saffron focus:bg-white transition-all">
        </div>
        <div class="flex items-center gap-2 w-full sm:w-auto justify-end">
          <button onclick="toggleStockFilter()" id="stockFilterBtn" class="text-xs font-bold bg-amber-100 text-amber-800 border border-amber-300 px-3 py-2 rounded-xl flex items-center gap-1.5 hover:bg-amber-200 transition-all">
            <span>⚠️ Low Stock Only</span>
          </button>
          <button onclick="openBoxCustomizerModal()" class="text-xs font-bold bg-pista/10 text-pista border border-pista/30 px-3 py-2 rounded-xl flex items-center gap-1.5 hover:bg-pista/20 transition-all">
            <span>🎁 Custom Gift Box</span>
          </button>
        </div>
      </div>
      <div class="grid grid-cols-2 sm:grid-cols-3 xl:grid-cols-4 gap-4" id="sweetsGrid"></div>
    </div>

    <div class="lg:col-span-5 xl:col-span-4">
      <div class="bg-charcoal text-white rounded-3xl p-5 shadow-2xl sticky top-24 border border-gray-800 flex flex-col justify-between min-h-[620px]">
        <div>
          <div class="flex items-center justify-between border-b border-gray-800 pb-3 mb-4">
            <div class="flex items-center gap-2">
              <span class="text-xl">🧾</span>
              <div>
                <h3 class="font-bold text-base text-white">Current Order Bill</h3>
                <p class="text-[11px] text-gray-400">Invoice: <span id="cartInvoiceId" class="text-amber-400 font-mono">Loading...</span></p>
              </div>
            </div>
            <button onclick="clearCart()" class="text-xs text-red-400 hover:text-red-300 font-semibold bg-red-950/50 border border-red-800/50 px-2.5 py-1 rounded-lg">Clear All</button>
          </div>

          <div class="bg-gray-900 border border-amber-500/30 rounded-2xl p-4 mb-4">
            <div class="flex items-center justify-between text-xs text-gray-400 mb-1">
              <span class="flex items-center gap-1 text-saffronGold font-bold">
                <span class="w-2 h-2 rounded-full bg-saffron animate-ping"></span> Live Weighing Scale Sync
              </span>
              <span class="text-[10px] bg-gray-800 text-pista px-2 py-0.5 rounded font-mono">USB SCALE CONNECTED</span>
            </div>
            <div class="flex items-baseline justify-between py-1">
              <div class="text-3xl font-extrabold font-mono text-amber-400 tracking-wider" id="liveWeightDisplay">0.000 <span class="text-xs font-sans text-gray-400">Kg</span></div>
              <div class="text-right">
                <span class="text-[10px] text-gray-400 block uppercase">Tare Weight</span>
                <span class="text-xs font-mono font-bold text-gray-300" id="tareWeightDisplay">0.050 Kg</span>
              </div>
            </div>
            <div class="mt-2 pt-2 border-t border-gray-800 flex items-center gap-3">
              <input type="range" id="scaleSlider" min="0.1" max="5.0" step="0.05" value="0.5" oninput="updateSimulatedWeight(this.value)" class="w-full accent-saffron h-1.5 bg-gray-800 rounded-lg cursor-pointer">
              <button onclick="autoTare()" class="text-[10px] bg-gray-800 hover:bg-gray-700 text-saffronGold border border-amber-500/30 font-bold px-2 py-1 rounded-md whitespace-nowrap">AUTO TARE</button>
            </div>
          </div>

          <div class="space-y-2.5 max-h-[220px] overflow-y-auto pr-1" id="cartItemsContainer">
            <div class="text-center py-8 text-gray-500 text-xs"><span class="text-3xl block mb-2">🛒</span>Cart is currently empty.<br>Click on any sweet to add!</div>
          </div>
        </div>

        <div class="pt-4 border-t border-gray-800 space-y-3 mt-4">
          <div class="space-y-1.5 text-xs text-gray-400">
            <div class="flex justify-between"><span>Subtotal:</span><span class="font-mono text-gray-200" id="cartSubtotal">₹0.00</span></div>
            <div class="flex justify-between"><span>GST (5% / 12%):</span><span class="font-mono text-gray-200" id="cartTax">₹0.00</span></div>
            <div class="flex justify-between text-base font-extrabold text-white pt-1 border-t border-gray-800">
              <span class="text-saffronGold">Grand Total:</span>
              <span class="font-mono text-2xl text-saffronGold" id="cartGrandTotal">₹0</span>
            </div>
          </div>
          <div class="grid grid-cols-2 gap-2 pt-1">
            <button onclick="processCheckout('UPI')" class="bg-gradient-to-r from-pista to-pistaDark text-white font-bold py-3 px-3 rounded-xl shadow-lg hover:brightness-110 transition-all text-xs flex flex-col items-center gap-0.5">
              <span>💳 Pay via UPI / QR</span><span class="text-[9px] opacity-80">Instant Confetti + Thermal</span>
            </button>
            <button onclick="processCheckout('CASH')" class="bg-gradient-to-r from-saffron to-saffronGold text-white font-bold py-3 px-3 rounded-xl shadow-lg hover:brightness-110 transition-all text-xs flex flex-col items-center gap-0.5">
              <span>💵 Cash Payment</span><span class="text-[9px] opacity-80">Print Receipt Immediately</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</section>

<!-- BOOKING -->
<section id="booking" class="py-16 bg-creamGold border-t border-amber-200/60 px-4 md:px-8">
  <div class="max-w-7xl mx-auto">
    <div class="text-center max-w-2xl mx-auto mb-12">
      <span class="text-xs font-bold uppercase tracking-widest text-saffron bg-saffron/10 px-3 py-1 rounded-full">Diwali & Wedding Season ERP</span>
      <h2 class="font-serif text-3xl sm:text-4xl font-extrabold text-charcoal mt-2">🎁 Advance Order Booking System</h2>
      <p class="text-gray-600 text-sm mt-1">Book bulk sweet hampers, wedding gift boxes, and track delivery deadlines seamlessly.</p>
    </div>
    <div class="grid grid-cols-1 lg:grid-cols-12 gap-10">
      <div class="lg:col-span-5 bg-white p-6 sm:p-8 rounded-3xl border border-gray-200 shadow-xl">
        <h3 class="font-bold text-lg text-charcoal mb-4">📝 New Advance Booking</h3>
        <form id="advanceBookingForm" onsubmit="handleBookingSubmit(event)" class="space-y-4">
          <div>
            <label class="block text-xs font-bold text-gray-700 mb-1">Customer Name *</label>
            <input type="text" id="bkName" required placeholder="e.g. Ramesh Chandra" class="w-full bg-gray-50 border border-gray-300 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-saffron">
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div><label class="block text-xs font-bold text-gray-700 mb-1">Mobile Number *</label><input type="tel" id="bkPhone" required placeholder="+91 98765 43210" class="w-full bg-gray-50 border border-gray-300 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-saffron"></div>
            <div><label class="block text-xs font-bold text-gray-700 mb-1">Delivery Date *</label><input type="date" id="bkDate" required class="w-full bg-gray-50 border border-gray-300 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-saffron"></div>
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="block text-xs font-bold text-gray-700 mb-1">Sweet / Gift Box *</label>
              <select id="bkSweet" class="w-full bg-gray-50 border border-gray-300 rounded-xl px-3 py-2.5 text-sm focus:outline-none focus:border-saffron">
                <option>Diwali Special Assorted Gift Box</option>
                <option>Royal Kaju Katli Premium Box</option>
                <option>Kesar Rasgulla Tin Pack (12 Pcs)</option>
                <option>Wedding Custom Mixed Sweet Box</option>
              </select>
            </div>
            <div><label class="block text-xs font-bold text-gray-700 mb-1">Quantity (Boxes/Kg)</label><input type="number" id="bkQty" value="20" min="1" class="w-full bg-gray-50 border border-gray-300 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-saffron"></div>
          </div>
          <div class="grid grid-cols-2 gap-3">
            <div><label class="block text-xs font-bold text-gray-700 mb-1">Estimated Total (₹)</label><input type="number" id="bkTotal" placeholder="10000" class="w-full bg-gray-50 border border-gray-300 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-saffron"></div>
            <div><label class="block text-xs font-bold text-gray-700 mb-1">Advance Received (₹) *</label><input type="number" id="bkAdvance" required placeholder="2000" class="w-full bg-gray-50 border border-gray-300 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:border-saffron"></div>
          </div>
          <div><label class="block text-xs font-bold text-gray-700 mb-1">Packaging Instructions / Note</label><textarea id="bkNotes" rows="2" placeholder="e.g. Red Satin Ribbon, Family Name Sticker" class="w-full bg-gray-50 border border-gray-300 rounded-xl px-4 py-2 text-sm focus:outline-none focus:border-saffron"></textarea></div>
          <button type="submit" class="w-full bg-gradient-to-r from-saffron to-saffronGold text-white font-bold py-3.5 rounded-2xl shadow-lg hover:brightness-105 transition-all text-sm">📅 Confirm & Save Advance Order</button>
        </form>
      </div>
      <div class="lg:col-span-7 bg-white p-6 sm:p-8 rounded-3xl border border-gray-200 shadow-xl flex flex-col justify-between">
        <div>
          <div class="flex items-center justify-between mb-6">
            <h3 class="font-bold text-lg text-charcoal">📋 Active Bookings Tracker</h3>
            <span class="text-xs font-bold bg-pista/10 text-pista px-3 py-1 rounded-full" id="activeBookingBadge">0 Active</span>
          </div>
          <div class="space-y-4" id="bookingsTimelineContainer"></div>
        </div>
        <div class="mt-6 pt-4 border-t border-gray-100 flex items-center justify-between text-xs text-gray-500">
          <span>💡 Tip: Advance bookings auto-alert staff 1 day before delivery.</span>
        </div>
      </div>
    </div>
  </div>
</section>

<!-- RECEIPT MODAL -->
<div id="receiptModal" class="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm hidden flex items-center justify-center p-4">
  <div class="bg-white rounded-3xl max-w-md w-full p-6 shadow-2xl relative border border-gray-200 max-h-[90vh] overflow-y-auto">
    <button onclick="closeReceiptModal()" class="absolute top-4 right-4 text-gray-400 hover:text-gray-600 font-bold text-xl">✕</button>
    <div class="text-center border-b border-dashed pb-4 mb-4">
      <div class="text-3xl mb-1">🥮</div>
      <h3 class="font-serif font-extrabold text-xl text-charcoal">MITHAAS SWEETS & BAKERY</h3>
      <p class="text-xs text-gray-500">102, Shahi Marg, Near Krishna Temple, Mathura</p>
      <p class="text-[11px] text-gray-400">GSTIN: 09AABCU9603R1ZM • Ph: +91 98112 00000</p>
    </div>
    <div class="bg-gray-50 p-4 rounded-xl border border-gray-200 receipt-font text-xs space-y-2 mb-4" id="thermalPrintContent"></div>
    <div class="bg-amber-50 p-3 rounded-xl border border-amber-200 text-center mb-4">
      <p class="text-[11px] font-bold text-amber-900 mb-1">Scan & Pay via PhonePe / GPay / Paytm</p>
      <img src="https://api.qrserver.com/v1/create-qr-code/?size=130x130&data=upi://pay?pa=mithaas@upi&pn=MithaasSweets&cu=INR" alt="UPI QR" class="w-28 h-28 mx-auto rounded-lg shadow-sm border border-white">
      <p class="text-[10px] text-amber-700 mt-1">UPI ID: mithaas@upi</p>
    </div>
    <div class="grid grid-cols-2 gap-3">
      <button onclick="triggerPrintReceipt()" class="bg-saffron text-white font-bold py-2.5 rounded-xl text-xs flex items-center justify-center gap-1.5 hover:bg-saffron/90">🖨️ Print Receipt</button>
      <button onclick="closeReceiptModal()" class="bg-gray-200 text-gray-800 font-bold py-2.5 rounded-xl text-xs hover:bg-gray-300">Done & Next Order</button>
    </div>
  </div>
</div>

<!-- BOX CUSTOMIZER MODAL -->
<div id="boxCustomizerModal" class="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm hidden flex items-center justify-center p-4">
  <div class="bg-white rounded-3xl max-w-lg w-full p-6 shadow-2xl relative border border-gray-200">
    <button onclick="closeBoxCustomizerModal()" class="absolute top-4 right-4 text-gray-400 hover:text-gray-600 font-bold text-xl">✕</button>
    <div class="flex items-center gap-3 mb-4">
      <span class="text-3xl">🎁</span>
      <div><h3 class="font-serif font-bold text-xl text-charcoal">Gift Box Packaging Customizer</h3><p class="text-xs text-gray-500">Configure tare weight and decorative ribbons.</p></div>
    </div>
    <div class="space-y-4 text-xs">
      <div>
        <label class="block font-bold text-gray-700 mb-1">Select Empty Box Size (Auto Tare Deduct):</label>
        <div class="grid grid-cols-3 gap-2">
          <button onclick="selectBoxTare('Small Box (250g)', 0.035, 20, event)" class="tare-btn border-2 border-gray-200 p-2.5 rounded-xl text-center font-bold text-gray-700">Small Box<br><span class="text-[10px] text-gray-500">Tare: 35g</span></button>
          <button onclick="selectBoxTare('Medium Box (500g)', 0.050, 35, event)" class="tare-btn border-2 border-saffron bg-saffron/10 p-2.5 rounded-xl text-center font-bold text-saffron">Medium Box<br><span class="text-[10px] text-gray-500">Tare: 50g</span></button>
          <button onclick="selectBoxTare('Large Box (1Kg)', 0.090, 60, event)" class="tare-btn border-2 border-gray-200 p-2.5 rounded-xl text-center font-bold text-gray-700">Large Box<br><span class="text-[10px] text-gray-500">Tare: 90g</span></button>
        </div>
      </div>
      <div class="bg-amber-50 p-3 rounded-xl border border-amber-200 text-amber-900">
        <p class="font-bold">Scale Sync Status:</p>
        <p class="text-[11px]">Box tare weight auto-subtracted so customer pays ONLY for net sweet weight.</p>
      </div>
      <button onclick="applyBoxCustomization()" class="w-full bg-pista text-white font-bold py-3 rounded-xl text-xs hover:brightness-105">✓ Apply Tare Settings to POS Scale</button>
    </div>
  </div>
</div>

<!-- ANALYTICS MODAL -->
<div id="analyticsModal" class="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm hidden flex items-center justify-center p-4">
  <div class="bg-white rounded-3xl max-w-3xl w-full p-6 sm:p-8 shadow-2xl relative border border-gray-200 max-h-[90vh] overflow-y-auto">
    <button onclick="closeAnalyticsModal()" class="absolute top-4 right-4 text-gray-400 hover:text-gray-600 font-bold text-xl">✕</button>
    <div class="flex items-center gap-3 mb-6">
      <span class="text-3xl">📊</span>
      <div><h3 class="font-serif font-bold text-2xl text-charcoal">Real-time Store Analytics</h3><p class="text-xs text-gray-500">Live sales, top selling sweets, inventory alerts.</p></div>
    </div>
    <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
      <div class="bg-saffron/10 border border-saffron/30 p-4 rounded-2xl"><span class="text-xs font-bold text-saffron uppercase">Total Sales Today</span><h4 class="text-2xl font-extrabold text-charcoal mt-1" id="dashTotalSales">₹0</h4></div>
      <div class="bg-pista/10 border border-pista/30 p-4 rounded-2xl"><span class="text-xs font-bold text-pista uppercase">Completed Orders</span><h4 class="text-2xl font-extrabold text-charcoal mt-1" id="dashOrderCount">0 Bills</h4></div>
      <div class="bg-amber-100 border border-amber-300 p-4 rounded-2xl"><span class="text-xs font-bold text-amber-900 uppercase">Stock Alerts</span><h4 class="text-2xl font-extrabold text-charcoal mt-1" id="dashAlertCount">0 Sweets</h4></div>
    </div>
    <div class="bg-gray-50 rounded-2xl p-4 border border-gray-200">
      <h4 class="font-bold text-sm text-charcoal mb-3 flex items-center justify-between"><span>⏰ Shelf Life & Batch Expiry Warnings</span><span class="text-xs text-gray-400">Live Auto-Monitoring</span></h4>
      <div class="space-y-2 text-xs" id="analyticsExpiryList"></div>
    </div>
  </div>
</div>

<footer class="bg-charcoal text-gray-400 py-10 px-4 md:px-8 border-t border-gray-800 text-xs">
  <div class="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
    <div class="flex items-center gap-2"><span class="text-saffron font-bold text-base">MithaasPOS</span><span>— Crafted with 🧡 for Sweet Shops across India</span></div>
    <div><span>© 2026 Mithaas POS Software Inc. • Powered by SQLite</span></div>
  </div>
</footer>

<script id="sweetsData" type="application/json">{{ sweets_json | safe }}</script>
<script id="bookingsData" type="application/json">{{ bookings_json | safe }}</script>
<script id="nextInvoiceData" type="application/json">{{ next_invoice | safe }}</script>

<script>
/* ============ GLOBAL STATE ============ */
let SWEETS = JSON.parse(document.getElementById('sweetsData').textContent);
const BOOKINGS = JSON.parse(document.getElementById('bookingsData').textContent);
const NEXT_INVOICE = JSON.parse(document.getElementById('nextInvoiceData').textContent);

let cart = [];
let currentScaleWeight = 0.500;
let currentTareWeight = 0.050;
let activeBoxTitle = "Medium Box (500g)";
let filterCat = "All";
let lowStockOnly = false;
let currentInvoiceId = NEXT_INVOICE;

window.addEventListener('DOMContentLoaded', () => {
  document.getElementById('cartInvoiceId').textContent = currentInvoiceId;
  renderSweetsGrid();
  renderCart();
  renderBookingsTimeline();
  updateLiveScaleDisplay();
  refreshNavStats();
});

/* ============ NAV STATS ============ */
function refreshNavStats() {
  const low = SWEETS.filter(s => s.stock <= 5).length;
  const exp = SWEETS.filter(s => s.shelf_life_days <= 2).length;
  document.getElementById('navLowStockCount').textContent = low + ' Items';
  document.getElementById('navExpiryCount').textContent = exp + ' Items';
  document.querySelectorAll('[id="navLowStockCount"]').forEach(el => el.textContent = low + ' Items');
}

/* ============ RENDER GRID ============ */
function renderSweetsGrid() {
  const container = document.getElementById('sweetsGrid');
  let list = SWEETS;
  if (filterCat !== "All") list = list.filter(s => s.category === filterCat);
  if (lowStockOnly) list = list.filter(s => s.stock <= 5.0);

  if (list.length === 0) {
    container.innerHTML = `<div class="col-span-full text-center py-12 bg-white rounded-2xl border border-gray-200"><span class="text-4xl block mb-2">🔍</span><p class="text-sm font-bold text-gray-600">No sweets found.</p></div>`;
    return;
  }

  container.innerHTML = list.map(s => {
    const isLowStock = s.stock <= 5.0;
    const isExpiringSoon = s.shelf_life_days <= 2;
    return `
      <div class="bg-white rounded-2xl p-3 border border-gray-200 hover:border-saffron/60 shadow-sm hover:shadow-md transition-all group relative flex flex-col justify-between">
        <div class="relative overflow-hidden rounded-xl h-28 mb-2">
          <img src="${s.img}" alt="${s.name}" class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300" onerror="this.src='https://via.placeholder.com/300x200/E67E22/FFFFFF?text=${encodeURIComponent(s.name)}'">
          <div class="absolute top-1.5 left-1.5 flex flex-col gap-1">
            ${isExpiringSoon ? '<span class="bg-danger text-white text-[9px] font-black px-2 py-0.5 rounded-full pulse-glow">EXPIRY ALERT</span>' : ''}
            ${isLowStock ? '<span class="bg-amber-500 text-white text-[9px] font-black px-2 py-0.5 rounded-full">LOW STOCK</span>' : ''}
          </div>
          <span class="absolute bottom-1.5 right-1.5 bg-black/70 backdrop-blur-md text-white text-[10px] font-mono px-2 py-0.5 rounded-md">Batch: ${s.batch}</span>
        </div>
        <div>
          <h4 class="font-bold text-xs text-charcoal group-hover:text-saffron transition-colors line-clamp-1">${s.name}</h4>
          <p class="text-[10px] text-gray-500 font-medium">Shelf Life: <span class="text-gray-700 font-bold">${s.shelf_life_days} Days</span></p>
          <div class="flex items-baseline justify-between mt-2 pt-2 border-t border-gray-100">
            <div><span class="text-sm font-extrabold text-saffron">₹${s.price}</span><span class="text-[10px] text-gray-400">/${s.unit}</span></div>
            <span class="text-[10px] font-mono text-gray-500 font-bold">Stock: ${s.stock}${s.unit}</span>
          </div>
        </div>
        <button onclick="addToCart(${s.id}, event)" class="mt-2.5 w-full bg-saffron/10 hover:bg-saffron text-saffron hover:text-white font-bold text-xs py-2 rounded-xl border border-saffron/30 transition-all">+ Add to Scale Bill</button>
      </div>`;
  }).join('');
}

/* ============ FILTERS ============ */
function filterCategory(cat, evt) {
  filterCat = cat;
  document.querySelectorAll('.cat-btn').forEach(btn => {
    btn.classList.remove('active', 'bg-saffron', 'text-white');
    btn.classList.add('bg-white', 'text-gray-700');
  });
  if (evt && evt.target) {
    evt.target.classList.add('active', 'bg-saffron', 'text-white');
    evt.target.classList.remove('bg-white', 'text-gray-700');
  }
  renderSweetsGrid();
}

function handleSearch(query) {
  query = query.toLowerCase();
  if (query === '') { renderSweetsGrid(); return; }
  const list = SWEETS.filter(s =>
    s.name.toLowerCase().includes(query) ||
    s.batch.toLowerCase().includes(query) ||
    s.category.toLowerCase().includes(query)
  );
  const container = document.getElementById('sweetsGrid');
  if (list.length === 0) {
    container.innerHTML = `<div class="col-span-full text-center py-8 text-gray-500 text-xs">No matching sweets.</div>`;
    return;
  }
  container.innerHTML = list.map(s => `
    <div class="bg-white rounded-2xl p-3 border border-gray-200 flex flex-col justify-between">
      <div class="relative overflow-hidden rounded-xl h-28 mb-2"><img src="${s.img}" class="w-full h-full object-cover"></div>
      <div><h4 class="font-bold text-xs">${s.name}</h4><span class="text-sm font-extrabold text-saffron">₹${s.price}/${s.unit}</span></div>
      <button onclick="addToCart(${s.id}, event)" class="mt-2 w-full bg-saffron text-white text-xs font-bold py-2 rounded-xl">+ Add</button>
    </div>`).join('');
}

function toggleStockFilter() {
  lowStockOnly = !lowStockOnly;
  const btn = document.getElementById('stockFilterBtn');
  if (lowStockOnly) { btn.classList.add('bg-amber-500', 'text-white'); btn.classList.remove('bg-amber-100', 'text-amber-800'); }
  else { btn.classList.remove('bg-amber-500', 'text-white'); btn.classList.add('bg-amber-100', 'text-amber-800'); }
  renderSweetsGrid();
}

/* ============ CART ============ */
function addToCart(sweetId, event) {
  const sweet = SWEETS.find(s => s.id === sweetId);
  if (!sweet) return;
  if (sweet.stock <= 0) { alert("Out of stock!"); return; }

  if (event) {
    const rect = event.currentTarget.getBoundingClientRect();
    const cartEl = document.getElementById('cartItemsContainer').getBoundingClientRect();
    const flyImg = document.createElement('img');
    flyImg.src = sweet.img;
    flyImg.className = 'fly-item w-12 h-12 shadow-2xl border-2 border-saffron';
    flyImg.style.left = (rect.left + 20) + 'px';
    flyImg.style.top = (rect.top + 20) + 'px';
    document.body.appendChild(flyImg);
    requestAnimationFrame(() => {
      flyImg.style.left = (cartEl.left + 40) + 'px';
      flyImg.style.top = (cartEl.top + 20) + 'px';
      flyImg.style.opacity = '0';
      flyImg.style.transform = 'scale(0.2)';
    });
    setTimeout(() => flyImg.remove(), 750);
  }

  const netWeight = Math.max(0.100, currentScaleWeight - currentTareWeight);
  const existing = cart.find(c => c.id === sweetId);
  if (existing) existing.weight = parseFloat((existing.weight + netWeight).toFixed(3));
  else cart.push({ ...sweet, weight: parseFloat(netWeight.toFixed(3)), packaging: activeBoxTitle });
  renderCart();
}

function updateCartWeight(sweetId, newWeight) {
  const item = cart.find(c => c.id === sweetId);
  if (!item) return;
  item.weight = parseFloat(parseFloat(newWeight).toFixed(3));
  if (item.weight <= 0) cart = cart.filter(c => c.id !== sweetId);
  renderCart();
}
function removeFromCart(id) { cart = cart.filter(c => c.id !== id); renderCart(); }
function clearCart() { cart = []; renderCart(); }

function renderCart() {
  const container = document.getElementById('cartItemsContainer');
  if (cart.length === 0) {
    container.innerHTML = `<div class="text-center py-10 text-gray-500 text-xs"><span class="text-3xl block mb-2">🛒</span>Cart is empty.<br>Select sweets to bill!</div>`;
    document.getElementById('cartSubtotal').textContent = '₹0.00';
    document.getElementById('cartTax').textContent = '₹0.00';
    document.getElementById('cartGrandTotal').textContent = '₹0';
    return;
  }
  let subtotal = 0, totalTax = 0;
  container.innerHTML = cart.map(c => {
    const itemTotal = c.price * c.weight;
    const itemTax = itemTotal * (c.gst_pct / 100);
    subtotal += itemTotal; totalTax += itemTax;
    return `
      <div class="bg-gray-900 border border-gray-800 rounded-xl p-2.5 flex items-center justify-between text-xs">
        <div class="flex items-center gap-2.5">
          <img src="${c.img}" class="w-10 h-10 rounded-lg object-cover">
          <div><h5 class="font-bold text-gray-200 text-xs">${c.name}</h5><span class="text-[10px] text-saffronGold font-mono">₹${c.price}/${c.unit}</span></div>
        </div>
        <div class="flex items-center gap-3">
          <div class="text-right"><input type="number" step="0.05" value="${c.weight}" onchange="updateCartWeight(${c.id}, this.value)" class="w-16 bg-black border border-gray-700 text-amber-400 font-mono text-center font-bold text-xs rounded py-1"><span class="text-[9px] text-gray-500 block">Kg</span></div>
          <div class="text-right w-14"><span class="font-mono font-bold text-white block">₹${Math.round(itemTotal)}</span></div>
          <button onclick="removeFromCart(${c.id})" class="text-gray-500 hover:text-red-400 font-bold px-1">✕</button>
        </div>
      </div>`;
  }).join('');
  const grandTotal = subtotal + totalTax;
  document.getElementById('cartSubtotal').textContent = `₹${subtotal.toFixed(2)}`;
  document.getElementById('cartTax').textContent = `₹${totalTax.toFixed(2)}`;
  animateValue("cartGrandTotal", 0, Math.round(grandTotal), 300);
}

/* ============ SCALE ============ */
function updateSimulatedWeight(val) { currentScaleWeight = parseFloat(val); updateLiveScaleDisplay(); }
function autoTare() { currentTareWeight = currentScaleWeight; updateLiveScaleDisplay(); }
function updateLiveScaleDisplay() {
  const net = Math.max(0, currentScaleWeight - currentTareWeight);
  document.getElementById('liveWeightDisplay').innerHTML = `${net.toFixed(3)} <span class="text-xs font-sans text-gray-400">Kg</span>`;
  document.getElementById('tareWeightDisplay').textContent = `${currentTareWeight.toFixed(3)} Kg`;
}

/* ============ CHECKOUT (DB PERSISTENT) ============ */
function processCheckout(payMode) {
  if (cart.length === 0) { alert("🛒 Cart is empty!"); return; }

  let subtotal = 0, tax = 0;
  cart.forEach(c => {
    const t = c.price * c.weight;
    subtotal += t;
    tax += t * (c.gst_pct / 100);
  });
  const grandTotal = Math.round(subtotal + tax);

  launchConfetti();

  fetch('/api/checkout', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      invoice_id: currentInvoiceId,
      items: cart,
      payment_mode: payMode,
      subtotal: subtotal,
      tax: tax,
      grand_total: grandTotal
    })
  })
  .then(r => r.json())
  .then(res => {
    if (!res.ok) { alert("❌ " + (res.error || "Checkout failed")); return; }

    // Print receipt content
    const thermal = document.getElementById('thermalPrintContent');
    thermal.innerHTML = `
      <div class="flex justify-between border-b pb-1"><span>INV: ${res.order.invoice_id}</span><span>${new Date().toLocaleTimeString()}</span></div>
      <div class="space-y-1 py-2 border-b border-dashed">
        ${cart.map(i => `<div class="flex justify-between"><span>${i.name} (${i.weight}kg)</span><span>₹${Math.round(i.price * i.weight)}</span></div>`).join('')}
      </div>
      <div class="space-y-1 pt-1">
        <div class="flex justify-between"><span>Subtotal:</span><span>₹${subtotal.toFixed(2)}</span></div>
        <div class="flex justify-between"><span>GST:</span><span>₹${tax.toFixed(2)}</span></div>
        <div class="flex justify-between font-bold text-sm pt-1 border-t"><span>GRAND TOTAL:</span><span>₹${grandTotal}</span></div>
        <div class="flex justify-between text-[10px] text-gray-500"><span>MODE:</span><span>${payMode}</span></div>
      </div>`;
    document.getElementById('receiptModal').classList.remove('hidden');

    // Refresh local stock
    refreshSweetsFromServer();

    // Next invoice id
    currentInvoiceId = res.next_invoice;
    document.getElementById('cartInvoiceId').textContent = currentInvoiceId;
    clearCart();
  })
  .catch(err => alert("❌ Network error: " + err));
}

function closeReceiptModal() { document.getElementById('receiptModal').classList.add('hidden'); }
function triggerPrintReceipt() { window.print(); }

/* ============ REFRESH FROM SERVER ============ */
function refreshSweetsFromServer() {
  fetch('/api/sweets').then(r => r.json()).then(data => {
    SWEETS = data;
    renderSweetsGrid();
    refreshNavStats();
  });
}

/* ============ BOOKING ============ */
function handleBookingSubmit(e) {
  e.preventDefault();
  const payload = {
    name: document.getElementById('bkName').value,
    phone: document.getElementById('bkPhone').value,
    date: document.getElementById('bkDate').value,
    sweet: document.getElementById('bkSweet').value,
    qty: document.getElementById('bkQty').value,
    total: document.getElementById('bkTotal').value || 10000,
    advance: document.getElementById('bkAdvance').value,
    notes: document.getElementById('bkNotes').value
  };
  fetch('/api/book', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  }).then(r => r.json()).then(res => {
    if (res.ok) {
      launchConfetti();
      BOOKINGS.unshift(res.order);
      renderBookingsTimeline();
      document.getElementById('advanceBookingForm').reset();
      alert(`🎉 Booking #${res.order.id} Confirmed!`);
    } else alert('❌ ' + (res.error || 'Booking failed'));
  });
}

function renderBookingsTimeline() {
  const container = document.getElementById('bookingsTimelineContainer');
  document.getElementById('activeBookingBadge').textContent = `${BOOKINGS.length} Active`;
  if (BOOKINGS.length === 0) { container.innerHTML = '<p class="text-xs text-gray-400 text-center py-8">No active bookings yet.</p>'; return; }
  container.innerHTML = BOOKINGS.map(b => `
    <div class="bg-gray-50 p-4 rounded-2xl border border-gray-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
      <div class="space-y-1">
        <div class="flex items-center gap-2"><span class="font-bold text-xs text-saffron font-mono">${b.id}</span><span class="bg-pista/10 text-pista text-[10px] font-bold px-2 py-0.5 rounded">${b.status}</span></div>
        <h5 class="font-bold text-sm text-charcoal">${b.name} (${b.phone})</h5>
        <p class="text-xs text-gray-600">${b.sweet_type} • <b class="text-gray-800">${b.qty} Boxes</b></p>
        <p class="text-[11px] text-gray-400">Notes: ${b.notes || 'None'}</p>
      </div>
      <div class="text-right sm:border-l sm:pl-4 sm:border-gray-200">
        <span class="text-[10px] text-gray-400 block uppercase">Delivery Date</span>
        <span class="font-bold text-xs text-charcoal block">${b.delivery_date}</span>
        <span class="text-xs font-bold text-pista block mt-1">Advance: ₹${b.advance_paid}</span>
      </div>
    </div>`).join('');
}

/* ============ MODALS ============ */
function openBoxCustomizerModal() { document.getElementById('boxCustomizerModal').classList.remove('hidden'); }
function closeBoxCustomizerModal() { document.getElementById('boxCustomizerModal').classList.add('hidden'); }
function selectBoxTare(title, tareKg, price, evt) {
  activeBoxTitle = title; currentTareWeight = tareKg; updateLiveScaleDisplay();
  document.querySelectorAll('.tare-btn').forEach(b => { b.classList.remove('border-saffron', 'bg-saffron/10', 'text-saffron'); b.classList.add('border-gray-200', 'text-gray-700'); });
  evt.target.classList.add('border-saffron', 'bg-saffron/10', 'text-saffron');
}
function applyBoxCustomization() { closeBoxCustomizerModal(); }

function openAnalyticsModal() {
  fetch('/api/analytics').then(r => r.json()).then(data => {
    document.getElementById('dashTotalSales').textContent = `₹${Number(data.total_revenue).toLocaleString('en-IN')}`;
    document.getElementById('dashOrderCount').textContent = `${data.order_count} Bills`;
    document.getElementById('dashAlertCount').textContent = `${data.low_stock_count} Sweets`;
    const list = document.getElementById('analyticsExpiryList');
    list.innerHTML = data.expiring_items.length ? data.expiring_items.map(i => `
      <div class="flex items-center justify-between p-2 bg-white rounded-xl border border-gray-200">
        <div class="flex items-center gap-2"><span class="text-lg">⚠️</span>
          <div><b class="text-gray-800 block">${i.name}</b><span class="text-[10px] text-gray-400">Batch: ${i.batch} • Mfg: ${i.mfg_date}</span></div>
        </div>
        <span class="bg-red-100 text-red-700 font-bold px-2 py-0.5 rounded text-[10px]">Expires in ${i.shelf_life_days} Days</span>
      </div>`).join('') : '<p class="text-xs text-gray-400 text-center py-4">✅ No expiring items.</p>';
    document.getElementById('analyticsModal').classList.remove('hidden');
  });
}
function closeAnalyticsModal() { document.getElementById('analyticsModal').classList.add('hidden'); }

/* ============ UTILS ============ */
function launchConfetti() {
  const colors = ['#E67E22', '#F39C12', '#27AE60', '#E74C3C', '#3498DB'];
  for (let i = 0; i < 60; i++) {
    const c = document.createElement('div');
    c.className = 'confetti-particle';
    c.style.left = Math.random() * 100 + 'vw';
    c.style.top = '-10px';
    c.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
    c.style.transform = `scale(${Math.random() * 0.8 + 0.4})`;
    document.body.appendChild(c);
    c.animate([
      { transform: 'translateY(0) rotate(0deg)', opacity: 1 },
      { transform: `translateY(100vh) rotate(${Math.random() * 720}deg)`, opacity: 0 }
    ], { duration: Math.random() * 2000 + 1500, easing: 'cubic-bezier(0.25, 0.46, 0.45, 0.94)' })
    .onfinish = () => c.remove();
  }
}
function animateValue(id, start, end, duration) {
  const obj = document.getElementById(id);
  let ts = null;
  const step = (t) => {
    if (!ts) ts = t;
    const p = Math.min((t - ts) / duration, 1);
    obj.innerHTML = '₹' + Math.floor(p * (end - start) + start).toLocaleString('en-IN');
    if (p < 1) requestAnimationFrame(step);
  };
  requestAnimationFrame(step);
}
function scrollToSection(id) { document.getElementById(id).scrollIntoView({ behavior: 'smooth' }); }
</script>
</body>
</html>
"""


# ------------------------------------------------------------------
# ROUTES
# ------------------------------------------------------------------
@app.route("/")
def home():
    """Serves the dashboard, pulling live data from SQLite."""
    with db_context() as conn:
        sweets = rows_to_dicts(conn.execute("SELECT * FROM sweets ORDER BY id").fetchall())
        bookings = rows_to_dicts(conn.execute(
            "SELECT * FROM advance_bookings ORDER BY created_at DESC").fetchall())

        # Generate next invoice id
        last = conn.execute("SELECT invoice_id FROM orders ORDER BY id DESC LIMIT 1").fetchone()
        if last:
            try:
                num = int(last["invoice_id"].split("-")[1]) + 1
            except (ValueError, IndexError):
                num = 10025
        else:
            num = 10025
        next_invoice = f"MITH-{num}"

    return render_template_string(
        LANDING_HTML,
        sweets_json=json.dumps(sweets),
        bookings_json=json.dumps(bookings),
        next_invoice=json.dumps(next_invoice)
    )


@app.route("/api/sweets", methods=["GET"])
def api_sweets():
    with db_context() as conn:
        sweets = rows_to_dicts(conn.execute("SELECT * FROM sweets ORDER BY id").fetchall())
    return jsonify(sweets)


@app.route("/api/checkout", methods=["POST"])
def api_checkout():
    """Save order + line items to SQLite, deduct stock atomically."""
    data = request.get_json(force=True)
    items = data.get("items", [])
    if not items:
        return jsonify(ok=False, error="Cart is empty"), 400

    invoice_id = data.get("invoice_id") or f"MITH-{random.randint(10000, 99999)}"
    pay_mode = data.get("payment_mode", "CASH")
    subtotal = float(data.get("subtotal", 0))
    tax = float(data.get("tax", 0))
    grand_total = float(data.get("grand_total", 0))

    try:
        with db_context() as conn:
            c = conn.cursor()

            # 1) Insert order
            c.execute("""
                INSERT INTO orders (invoice_id, customer, phone, subtotal, tax, grand_total, payment_mode)
                VALUES (?,?,?,?,?,?,?)
            """, (invoice_id, "Walk-in Customer", "", subtotal, tax, grand_total, pay_mode))
            order_pk = c.lastrowid

            # 2) Insert line items + deduct stock
            for it in items:
                line_total = it["price"] * it["weight"]
                c.execute("""
                    INSERT INTO order_items
                    (order_id, sweet_id, name, weight, price, gst_pct, line_total)
                    VALUES (?,?,?,?,?,?,?)
                """, (order_pk, it["id"], it["name"], it["weight"],
                      it["price"], it.get("gst_pct", 5), line_total))

                c.execute("""
                    UPDATE sweets SET stock = MAX(0, ROUND(stock - ?, 3)) WHERE id = ?
                """, (it["weight"], it["id"]))

            # 3) Next invoice id
            c.execute("SELECT invoice_id FROM orders ORDER BY id DESC LIMIT 1")
            last = c.fetchone()
            try:
                next_num = int(last["invoice_id"].split("-")[1]) + 1
            except (ValueError, IndexError):
                next_num = 10026
            next_invoice = f"MITH-{next_num}"

        return jsonify(ok=True, order={
            "id": order_pk,
            "invoice_id": invoice_id,
            "grand_total": grand_total,
            "payment_mode": pay_mode
        }, next_invoice=next_invoice)

    except sqlite3.IntegrityError as e:
        return jsonify(ok=False, error=f"Duplicate invoice or constraint: {e}"), 400
    except Exception as e:
        return jsonify(ok=False, error=str(e)), 500


@app.route("/api/book", methods=["POST"])
def api_book():
    """Save a new advance booking to SQLite."""
    data = request.get_json(force=True)
    name = data.get("name", "").strip()
    phone = data.get("phone", "").strip()
    if not name or not phone:
        return jsonify(ok=False, error="Name & phone required"), 400

    order_id = f"ORD-BK-{random.randint(1000, 9999)}"
    record = {
        "id": order_id,
        "name": name,
        "phone": phone,
        "sweet_type": data.get("sweet", ""),
        "qty": int(data.get("qty", 1)),
        "delivery_date": data.get("date", ""),
        "advance_paid": float(data.get("advance", 0)),
        "total_estimated": float(data.get("total", 0)),
        "notes": data.get("notes", ""),
        "status": "Confirmed",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    try:
        with db_context() as conn:
            conn.execute("""
                INSERT INTO advance_bookings
                (id, name, phone, sweet_type, qty, delivery_date,
                 advance_paid, total_estimated, notes, status, created_at)
                VALUES (:id,:name,:phone,:sweet_type,:qty,:delivery_date,
                        :advance_paid,:total_estimated,:notes,:status,:created_at)
            """, record)
        return jsonify(ok=True, order=record)
    except Exception as e:
        return jsonify(ok=False, error=str(e)), 500


@app.route("/api/analytics", methods=["GET"])
def api_analytics():
    """Compute store KPIs from SQLite."""
    with db_context() as conn:
        # Today's sales
        today = datetime.now().strftime("%Y-%m-%d")
        row = conn.execute("""
            SELECT COALESCE(SUM(grand_total), 0) AS total,
                   COUNT(*) AS cnt
            FROM orders WHERE DATE(created_at) = ?
        """, (today,)).fetchone()
        total_revenue = row["total"]
        order_count = row["cnt"]

        low_stock = conn.execute("SELECT COUNT(*) c FROM sweets WHERE stock <= 5").fetchone()["c"]
        expiring = rows_to_dicts(conn.execute(
            "SELECT * FROM sweets WHERE shelf_life_days <= 3 ORDER BY shelf_life_days"
        ).fetchall())

    return jsonify({
        "total_revenue": total_revenue,
        "order_count": order_count,
        "low_stock_count": low_stock,
        "expiring_items": expiring
    })


@app.route("/api/orders", methods=["GET"])
def api_orders():
    """View all past orders (for admin)."""
    with db_context() as conn:
        orders = rows_to_dicts(conn.execute(
            "SELECT * FROM orders ORDER BY id DESC LIMIT 50").fetchall())
        for o in orders:
            o["items"] = rows_to_dicts(conn.execute(
                "SELECT * FROM order_items WHERE order_id = ?", (o["id"],)).fetchall())
    return jsonify(orders)


# ------------------------------------------------------------------
# BOOT
# ------------------------------------------------------------------
if __name__ == "__main__":
    init_db()
    print("\n" + "="*65)
    print("  🍬 MithaasPOS — SQLite-backed Sweet Shop ERP")
    print("  Server:  http://127.0.0.1:5000")
    print("  DB File: " + DB_PATH)
    print("="*65 + "\n")
    app.run(debug=True, host="0.0.0.0", port=5000)
