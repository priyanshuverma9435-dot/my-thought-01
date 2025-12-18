import streamlit as st
import requests
import pandas as pd
from PIL import Image
from datetime import datetime

# -------- SAFE BARCODE IMPORT --------
try:
    from pyzbar.pyzbar import decode
    ZBAR_OK = True
except:
    ZBAR_OK = False

# -------- CONFIG --------
st.set_page_config("Universal Scanner & Billing", layout="wide")

if "cart" not in st.session_state:
    st.session_state.cart = []

# -------- FUNCTIONS --------
def scan_code(img):
    if not ZBAR_OK:
        return None
    img = img.convert("RGB")
    res = decode(img)
    return res[0].data.decode("utf-8") if res else None

def fetch_product(barcode):
    if not barcode.isdigit():
        return None
    url = f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"
    r = requests.get(url, timeout=10).json()
    if r.get("status") != 1:
        return None
    p = r["product"]
    return {
        "name": p.get("product_name", "Unknown"),
        "brand": p.get("brands", ""),
        "category": p.get("categories", ""),
        "ingredients": p.get("ingredients_text", ""),
        "price": round((int(barcode[-3:]) % 90) / 2 + 1, 2)
    }

def add_cart(name, price, qty):
    st.session_state.cart.append({
        "Product": name,
        "Qty": qty,
        "Price": price,
        "Total": round(price * qty, 2)
    })

# -------- UI --------
st.title("📷 Universal Barcode Scanner & Billing")

img = st.camera_input("Scan Barcode / QR Code")

product = None
if img:
    if not ZBAR_OK:
        st.error("Barcode scanner not available (libzbar missing)")
    else:
        code = scan_code(Image.open(img))
        if code:
            st.success(f"Scanned: {code}")
            product = fetch_product(code)
            if not product:
                st.warning("Product not found – use manual entry")
        else:
            st.error("No barcode detected")

# -------- PRODUCT DETAILS --------
if product:
    st.subheader("Product Details")
    st.json(product)
    qty = st.number_input("Quantity", 1, 100, 1)
    if st.button("Add to Cart"):
        add_cart(product["name"], product["price"], qty)
        st.success("Added to cart")

# -------- MANUAL ENTRY --------
with st.expander("✍ Manual Product Entry"):
    name = st.text_input("Product Name")
    price = st.number_input("Price", 0.0, 10000.0)
    qty = st.number_input("Quantity", 1, 100, 1)
    if st.button("Add Manual Item"):
        if name and price > 0:
            add_cart(name, price, qty)
            st.success("Added manually")
        else:
            st.error("Enter valid product name & price")

# -------- CART --------
st.subheader("🛒 Cart")

if st.session_state.cart:
    df = pd.DataFrame(st.session_state.cart)
    st.dataframe(df, use_container_width=True)

    subtotal = df["Total"].sum()
    tax = st.slider("Tax %", 0, 28, 5)
    total = subtotal + subtotal * tax / 100

    st.metric("Subtotal", f"${subtotal:.2f}")
    st.metric("Total", f"${total:.2f}")

    if st.button("🧾 Generate Invoice"):
        st.markdown(f"""
        ### Invoice
        Date: {datetime.now().strftime('%d-%m-%Y %H:%M')}
        ```
        {df}
        ```
        Subtotal: ${subtotal:.2f}  
        Tax: {tax}%  
        **Grand Total: ${total:.2f}**
        """)
else:
    st.info("Cart empty")
