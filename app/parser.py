import fitz
import base64
from groq import Groq
from app.config import GROQ_API_KEY

# ── Setup ──────────────────────────────────────────────────
groq_client = Groq(api_key=GROQ_API_KEY)
MIN_IMAGE_SIZE = 5000

VISION_PROMPT = """Deskripsikan gambar/grafik/chart/infografis ini secara lengkap dalam Bahasa Indonesia.

Jika DIAGRAM ALUR/FLOWCHART: jelaskan setiap langkah berurutan mengikuti tanda panah dari awal sampai akhir, sebutkan semua label dan tahapan.
Jika CHART/GRAFIK: sebutkan semua angka, label, persentase, dan tren nilainya.
Jika TABEL: sebutkan semua baris dan kolom beserta nilainya.
Jika GAMBAR/DAFTAR: sebutkan semua item dan teks yang tampil."""

MANUAL_PAGE_DESCRIPTIONS = {
    8: """[Infografis Penanganan Pengaduan Nasabah - Halaman 8]
Alur penanganan pengaduan nasabah di Bank Mandiri (mengikuti tanda panah):
1. MENYAMPAIKAN PENGADUAN: Nasabah menyampaikan pengaduan melalui media masa, telepon, email, media sosial, atau surat cabang.
2. VERIFIKASI & INPUT: Bank menerima, memverifikasi, dan menginput pengaduan ke sistem.
3. SISTEM PENGADUAN: Pengaduan masuk ke sistem pengaduan Bank Mandiri.
4. INVESTIGASI: Bank melakukan investigasi dan membuat keputusan.
5. UPDATE HASIL INVESTIGASI KE DALAM: Hasil investigasi diupdate ke dalam sistem.
6. MENGINFOKAN HASIL KEPADA NASABAH: Bank menginformasikan hasil investigasi kepada nasabah.
7. MENERIMA HASIL PENGADUAN: Nasabah menerima hasil pengaduan.""",

    9: """[Daftar Saluran Pengaduan Bank Mandiri - Halaman 9]
Saluran pengaduan yang tersedia:
1. Mandiri Call 14000 (24 jam)
2. Akun X: mandiricare dan @bankmandiri
3. WhatsApp MITA: 0811-8414-000
4. Website: www.bankmandiri.co.id (menu contact us)
5. Akun Facebook: Mandiri Care dan Bank Mandiri
6. Kantor Cabang Bank Mandiri di seluruh Indonesia
7. Email: mandiricare@bankmandiri.co.id
8. Akun Instagram: @bankmandiri
9. Surat resmi yang dikirim langsung atau melalui pos"""
}

# ── Functions ──────────────────────────────────────────────
def describe_image_with_groq(image_bytes: bytes) -> str:
    response = groq_client.chat.completions.create(
        model="llama-3.2-11b-vision-preview",
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{base64.b64encode(image_bytes).decode()}"}
                },
                {"type": "text", "text": VISION_PROMPT}
            ]
        }],
        max_tokens=1024
    )
    return response.choices[0].message.content

def _describe_page_images(doc: fitz.Document, page: fitz.Page, page_num: int) -> list[str]:
    descriptions = []
    for idx, img in enumerate(page.get_images(full=True)):
        image_bytes = doc.extract_image(img[0])["image"]
        if len(image_bytes) < MIN_IMAGE_SIZE:
            continue
        print(f"  -> Describing gambar {idx+1} halaman {page_num}...")
        desc = describe_image_with_groq(image_bytes)
        print(f"     {desc[:80]}...")
        descriptions.append(f"[Gambar {idx+1} di halaman {page_num}]: {desc}")
    return descriptions

def parse_pdf(pdf_path: str) -> list[dict]:
    doc = fitz.open(pdf_path)
    pages_content = []

    for page_num, page in enumerate(doc, start=1):
        if page_num in MANUAL_PAGE_DESCRIPTIONS:
            print(f"  -> Deskripsi manual halaman {page_num}")
            image_descs = [MANUAL_PAGE_DESCRIPTIONS[page_num]]
        else:
            image_descs = _describe_page_images(doc, page, page_num)

        pages_content.append({
            "page": page_num,
            "text": page.get_text("text"),
            "images_description": image_descs
        })

    doc.close()
    return pages_content