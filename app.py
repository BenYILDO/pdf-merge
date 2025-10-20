import io
import uuid
from typing import List, Dict

import streamlit as st
from PIL import Image

from utils.pdf_utils import build_pdf  # mm_to_pt gerekmiyor şimdilik

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
        # list of dict: {id, name, data(bytes), order, rotation, orientation_override}
        st.session_state.images = []
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
        options=["Otomatik", "Dikey", "Yatay"],
        index=["Otomatik", "Dikey", "Yatay"].index(st.session_state.global_settings["default_orientation"]),
        help="Her sayfa için varsayılan yönlendirme. Per-görselde üzerine yazabilirsin."
    )
    st.session_state.global_settings["default_orientation"] = default_orientation

    st.markdown("**Kenar Boşlukları (mm)**")
    col_m1, col_m2 = st.columns(2)
    col_m3, col_m4 = st.columns(2)
    left_mm = col_m1.number_input(
        "Sol", min_value=0.0,
        value=float(st.session_state.global_settings["margins_mm"]["left"]), step=1.0
    )
    right_mm = col_m2.number_input(
        "Sağ", min_value=0.0,
        value=float(st.session_state.global_settings["margins_mm"]["right"]), step=1.0
    )
    top_mm = col_m3.number_input(
        "Üst", min_value=0.0,
        value=float(st.session_state.global_settings["margins_mm"]["top"]), step=1.0
    )
    bottom_mm = col_m4.number_input(
        "Alt", min_value=0.0,
        value=float(st.session_state.global_settings["margins_mm"]["bottom"]), step=1.0
    )

    st.session_state.global_settings["margins_mm"] = {
        "left": left_mm, "right": right_mm, "top": top_mm, "bottom": bottom_mm
    }

    st.divider()
    if st.button("🗑️ Tümünü Temizle"):
        st.session_state.images = []
        st.experimental_rerun()

# -------------------------
# Dosya Yükleme
# -------------------------
uploaded_files = st.file_uploader(
    "Görselleri yükle (PNG, JPG, JPEG):",
    type=["png", "jpg", "jpeg"],
    accept_multiple_files=True
)

def add_uploaded_files(files):
    start_order = len(st.session_state.images)
    for i, f in enumerate(files):
        data = f.read()
        name = f.name
        st.session_state.images.append({
            "id": str(uuid.uuid4()),
            "name": name,
            "data": data,
            "order": start_order + i,
            "rotation": 0,  # 0, 90, 180, 270
            "orientation_override": "Varsayılan",  # Varsayılan | Otomatik | Dikey | Yatay
        })

if uploaded_files:
    add_uploaded_files(uploaded_files)

# -------------------------
# Yüklenenler ve Ayarlar
# -------------------------
if len(st.session_state.images) == 0:
    st.info("Henüz görsel yüklenmedi. Üstteki yükleme alanını kullanabilirsin.")
else:
    st.subheader("🖼️ Yüklenen Görseller ve Per-Item Ayarlar")

    # Görselleri order'a göre sırala
    st.session_state.images = sorted(st.session_state.images, key=lambda x: x["order"])

    # Her görsel için kart
    for idx, item in enumerate(st.session_state.images):
        with st.container():
            cols = st.columns([1.1, 2.4, 2.0, 1.5, 1.2])

            # Önizleme
            with cols[0]:
                try:
                    img = load_thumbnail(item["data"], max_side=240)
                    st.image(img, caption=item["name"], use_container_width=True)
                except Exception as e:
                    st.error(f"Görsel açılamadı: {item['name']} ({e})")

            # Sıra düzenleme
            with cols[1]:
                st.markdown("**Sıra**")
                new_order = st.number_input(
                    f"Sıra—{item['id'][:8]}",
                    value=int(item["order"]),
                    min_value=0,
                    max_value=max(0, len(st.session_state.images) - 1),
                    key=f"order_{item['id']}",
                    help="PDF'de sayfa sırasını belirler."
                )
                item["order"] = int(new_order)

                c_up, c_down = st.columns(2)
                if c_up.button("⬆️", key=f"up_{item['id']}"):
                    item["order"] = max(0, item["order"] - 1)
                if c_down.button("⬇️", key=f"down_{item['id']}"):
                    item["order"] = min(len(st.session_state.images) - 1, item["order"] + 1)

            # Döndürme
            with cols[2]:
                st.markdown("**Döndürme (derece)**")
                rotation = st.selectbox(
                    f"Döndür—{item['id'][:8]}",
                    options=[0, 90, 180, 270],
                    index=[0, 90, 180, 270].index(item["rotation"]),
                    key=f"rotation_{item['id']}",
                    help="Görseli 90° katlarıyla döndür."
                )
                item["rotation"] = rotation

                # Silme
                if st.button("🗑️ Bu görseli kaldır", key=f"del_{item['id']}"):
                    st.session_state.images = [
                        im for im in st.session_state.images if im["id"] != item["id"]
                    ]
                    st.experimental_rerun()

            # Yönlendirme (Sayfa yatay/dikey/otomatik)
            with cols[3]:
                st.markdown("**Yönlendirme (Sayfa)**")
                orientation_override = st.selectbox(
                    f"Yön—{item['id'][:8]}",
                    options=["Varsayılan", "Otomatik", "Dikey", "Yatay"],
                    index=["Varsayılan", "Otomatik", "Dikey", "Yatay"].index(item["orientation_override"]),
                    key=f"orientation_{item['id']}",
                    help="Bu sayfa için global ayarı geçersiz kıl."
                )
                item["orientation_override"] = orientation_override

            # Bilgi
            with cols[4]:
                st.markdown("**Özet**")
                st.write(f"**Ad:** {item['name']}")
                st.write(f"**Sıra:** {item['order']}")
                st.write(f"**Rot.:** {item['rotation']}°")
                st.write(f"**Yön:** {item['orientation_override']}")

            # Büyük görsel uyarısı
            size_mb = len(item["data"]) / (1024 * 1024)
            if size_mb > 50:
                st.warning(
                    f"{item['name']} boyutu {size_mb:.1f} MB — çok büyük. PDF oluşturma süresi uzayabilir."
                )

    st.divider()

    # PDF oluşturma
    col_left, _ = st.columns([1, 2])
    with col_left:
        st.markdown("### 📎 PDF Oluştur / İndir")
        out_name = st.text_input("Çıktı dosya adı", value="cikti.pdf")
        make_pdf = st.button("📄 PDF Oluştur")

    if make_pdf:
        with st.spinner("PDF oluşturuluyor, lütfen bekleyin..."):
            try:
                images_payload: List[Dict] = sorted(
                    st.session_state.images, key=lambda x: x["order"]
                )
                pdf_bytes = build_pdf(
                    images=images_payload,
                    page_size=st.session_state.global_settings["page_size"],  # "A4" | "Letter"
                    default_orientation=st.session_state.global_settings["default_orientation"],  # "Otomatik" | "Dikey" | "Yatay"
                    margins_mm=st.session_state.global_settings["margins_mm"]  # dict mm
                )
                st.success("PDF başarıyla oluşturuldu!")
                st.download_button(
                    label="⬇️ PDF'i İndir",
                    data=pdf_bytes,
                    file_name=out_name if out_name.lower().endswith(".pdf") else f"{out_name}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"PDF oluşturulurken hata oluştu: {e}")
