# Görsellerden PDF Oluşturucu (Streamlit)

PNG / JPG / JPEG dosyalarını yükleyip:
- Sırasını düzenleyebilir (yukarı/aşağı veya sıra numarası),
- Yatay/Dikey/Otomatik sayfa yönlendirmesi yapabilir,
- Global kenar boşluklarını (mm) ayarlayabilir,
- PDF çıktısı oluşturup indirebilirsiniz.

## Kurulum

```bash
# (Opsiyonel) sanal ortam
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
