import io
import uuid
from typing import List, Dict

import streamlit as st
from PIL import Image

from utils.pdf_utils import build_pdf, mm_to_pt  # mm_to_pt ileride gerekirse kullanılabilir

# -------------------------
# Streamlit Konfigürasyon
# -------------------------
st.set_page_config(
    page_title="Görsellerden PDF Oluşturucu",
    page_icon="📄",
    layout="wide"
)

# -------------------------
# Yardımcı: Session State
# -------------------------
def init_state():
    if "images" not in st.session_state:
        st.session_state.images = []  # list of dict: {id, name, data(bytes), order, rotation, orientation_override}
    if "global_settings" not in st.session_state:
        st.session_state.global_settings = {
            "page_size": "A4",
            "default_orientation": "Otomatik",  # Otomatik | Dikey | Yatay
            "margins_mm": {"left": 10.0, "right": 10.0, "top": 10.0, "bottom": 10.0}
        }

init_state()

# -------------------------
# Thumbnail Cache
# -------------------------
@st.cache_data(show_spinner=False)
def load_thumbnail(image_bytes: bytes, max_side: int = 600):
    img = Image.open(io.BytesIO(image_bytes))
    img = img.copy()  # PIL lazy load sorunlarını önlemek için
    img.thumbnail((max_side, max_side))
    return img

# -------------------------
# Başlık
# -------------------------
st.title("📄 Görsellerden PDF Oluşturucu")
st.caption(
    "PNG / JPG / JPEG yükle • Sırala • Yatay/Dikey konumlandır • Kenar boşluklarını ayarla • PDF indir"
)

# -------------------------
# Sidebar: Global Ayarlar
# -------------------------
with st.sidebar:
    st.header("⚙️ Global Ayarlar")

    page_size = st.selectbox(
        "Sayfa Boyutu",
        options=["A4", "Letter"],
        index=["A4", "Letter"].index(st.session_state.global_settings["page_size"]),
        help="Tüm sayfalar için temel boyut."
    )
    st.session_state.global_settings["page_size"] = page_size

    default_orientation = st.selectbox(
        "Varsayılan Yönlendirme",
        options=["Otomatik", "Dikey", "Yatay
