import io
from typing import List, Dict, Tuple

from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, LETTER, landscape, portrait
from reportlab.lib.utils import ImageReader

# ---- Boyut sözlüğü ----
PageSize = {"A4": A4, "Letter": LETTER}

def mm_to_pt(mm: float) -> float:
    """mm -> point (1 inç = 72 pt, 25.4 mm)"""
    return mm * 72.0 / 25.4

def _resolve_page_size(page_size_name: str, orient_name: str, img_w: int, img_h: int) -> Tuple[float, float]:
    """
    page_size_name: "A4" | "Letter"
    orient_name: "Otomatik" | "Dikey" | "Yatay"
    img_w, img_h: rotate sonrası piksel boyutları
    """
    base = PageSize.get(page_size_name, A4)
    if orient_name == "Dikey":
        w, h = portrait(base)
    elif orient_name == "Yatay":
        w, h = landscape(base)
    else:  # Otomatik
        if img_w >= img_h:
            w, h = landscape(base)
        else:
            w, h = portrait(base)
    return w, h

def _prepare_image(pil_img: Image.Image) -> Image.Image:
    """PDF'e uygun hale getir: RGBA/LA ise arka planı beyaz yap ve RGB'ye çevir."""
    if pil_img.mode in ("RGBA", "LA"):
        bg = Image.new("RGB", pil_img.size, (255, 255, 255))
        if pil_img.mode == "RGBA":
            bg.paste(pil_img, mask=pil_img.split()[3])
        else:
            tmp = pil_img.convert("RGBA")
            bg.paste(tmp, mask=tmp.split()[3])
        return bg
    elif pil_img.mode not in ("RGB", "L"):
        return pil_img.convert("RGB")
    else:
        return pil_img

def build_pdf(
    images: List[Dict],
    page_size: str = "A4",
    default_orientation: str = "Otomatik",  # Otomatik | Dikey | Yatay
    margins_mm: Dict[str, float] = None
) -> bytes:
    """
    images: [{ id, name, data(bytes), order:int, rotation:int, orientation_override:str }]
    """
    if margins_mm is None:
        margins_mm = {"left": 10.0, "right": 10.0, "top": 10.0, "bottom": 10.0}

    left_pt = mm_to_pt(margins_mm.get("left", 10.0))
    right_pt = mm_to_pt(margins_mm.get("right", 10.0))
    top_pt = mm_to_pt(margins_mm.get("top", 10.0))
    bottom_pt = mm_to_pt(margins_mm.get("bottom", 10.0))

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer)  # Sayfa boyutunu her sayfa setPageSize ile ayarlıyoruz.

    for item in images:
        pil = Image.open(io.BytesIO(item["data"]))
        rotation = int(item.get("rotation", 0)) % 360
        if rotation in (90, 180, 270):
            pil = pil.rotate(-rotation, expand=True, resample=Image.BICUBIC)

        pil = _prepare_image(pil)
        img_w_px, img_h_px = pil.size

        # Yönlendirme
        orient_choice = item.get("orientation_override", "Varsayılan")
        if orient_choice == "Varsayılan":
            orient_choice = default_orientation

        page_w, page_h = _resolve_page_size(page_size, orient_choice, img_w_px, img_h_px)
        c.setPageSize((page_w, page_h))

        # Çizilebilir alan
        avail_w = max(1.0, page_w - left_pt - right_pt)
        avail_h = max(1.0, page_h - top_pt - bottom_pt)

        # Ölçek
        scale = min(avail_w / img_w_px, avail_h / img_h_px)
        draw_w = img_w_px * scale
        draw_h = img_h_px * scale

        # Orta hizalama
        x = left_pt + (avail_w - draw_w) / 2.0
        y = bottom_pt + (avail_h - draw_h) / 2.0
        # Çiz
        img_reader = ImageReader(pil)
        c.drawImage(img_reader, x, y, width=draw_w, height=draw_h, preserveAspectRatio=True, mask='auto')
        c.showPage()

    c.save()
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
