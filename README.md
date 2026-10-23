🍬 MithaasPOS — Sweet Shop Billing & ERP Software

MithaasPOS is a lightweight, single-file Flask application designed for sweet shop management, POS counter billing, weighing scale integration, and advance gift box order booking.

✨ Features

⚖️ Live Weighing Scale Simulation: Integrated USB/Bluetooth weighing scale simulator with Tare Weight auto-deduction (e.g., container/box weight subtraction).

🧾 Instant POS Counter Billing: Quick add-to-cart, automatic GST (5% / 12%) calculation, subtotal rollup, and animated checkout.

🎁 Advance Order Booking: Track festival gift box orders, bulk wedding bookings, delivery deadlines, and advance payments.

📦 Custom Packaging Customizer: Choose box sizes (Small, Medium, Large) with automated tare adjustment and decorative ribbon selection.

⏰ Batch Expiry & Stock Monitoring: Visual warnings for sweets near shelf-life expiry or running low on stock.

📊 Real-time Analytics Dashboard: Summary metrics covering daily revenue, order count, and batch alerts.

🖨️ Thermal Receipt & UPI QR Generator: Print-ready thermal invoice preview with automatic QR code generation for payments.

🚀 Quick Start

1. Prerequisites

Make sure you have Python 3.8+ and Flask installed:

pip install flask


2. Clone the Repository

git clone https://github.com/Rg100152/-MithaasPOS.git
cd -MithaasPOS


3. Run the Application

python app.py


4. Access the Dashboard

Open your web browser and navigate to:

http://127.0.0.1:5000


🗄️ Database Architecture

Note: By default, MithaasPOS uses an In-Memory Python Data Structure (SWEETS_DB, COMPLETED_ORDERS, ADVANCE_BOOKINGS) for rapid demo prototyping without requiring external database installation.

If you plan to run this in a production environment, you can attach an SQLite database by executing a schema setup during application initialization:

import sqlite3

def init_db():
    conn = sqlite3.connect("mithaas_pos.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id TEXT PRIMARY KEY,
            customer_name TEXT,
            phone TEXT,
            sweet_type TEXT,
            qty INTEGER,
            delivery_date TEXT,
            advance_paid REAL,
            total_estimated REAL,
            notes TEXT,
            status TEXT,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()


📡 API Endpoints

Method

Endpoint

Description

GET

/

Serves the main POS & ERP Dashboard

GET

/api/sweets

Returns live inventory and batch metadata

POST

/api/checkout

Processes sales, deducts stock, and generates receipts

POST

/api/book

Saves new advance bookings

GET

/api/analytics

Provides real-time revenue and stock alert metrics

🛠️ Built With

Backend: Python / Flask

Frontend: HTML5, Tailwind CSS, JavaScript (ES6)

Styling & Icons: Google Fonts (Plus Jakarta Sans, Playfair Display), Emoji UI

📄 License

This project is open-source and available under the MIT License.
