import os
import streamlit as st
from google.generativeai import configure, GenerativeModel
from PIL import Image
import fitz  # PyMuPDF
import tempfile

# --- Google Gemini Vision APIの設定 ---
API_KEY = os.getenv("GOOGLE_API_KEY")  # 例: os.environ["GOOGLE_API_KEY"] = "..." でColabや環境変数にセット
configure(api_key=API_KEY)
model = GenerativeModel("gemini-pro-vision")

# --- プロンプト定義 ---
PROMPT = """
この画像は銀行の通帳です。「日付, 摘要, 支払金額, 預かり金額, 残高」の形式でCSVに変換してください。

- 和暦は西暦に変換（05年→2023, 06年→2024）
- 支払・預かり金額は「※」が含まれる数字のみを抽出
- 残高は※が無くても数字があれば抽出
- 数字以外（例：店番、カデなど）は全て無視
- 項目がずれないよう、必ず5列で整形してください
"""

# --- PDF → Imageに変換 ---
def convert_pdf_to_images(pdf_file):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(pdf_file.read())
        pdf_path = tmp_file.name
    doc = fitz.open(pdf_path)
    images = []
    for page in doc:
        pix = page.get_pixmap(dpi=300)
        img_path = tempfile.mktemp(suffix=".png")
        pix.save(img_path)
        images.append(Image.open(img_path))
    return images

# --- Streamlit UI ---
st.set_page_config(page_title="通帳PDF Gemini Vision Bot", layout="centered")
st.title("📄 通帳PDFフォーマット整形ボット")

uploaded_file = st.file_uploader("📂 通帳PDFをアップロード", type=["pdf"])

if uploaded_file:
    images = convert_pdf_to_images(uploaded_file)
    full_text = ""

    with st.spinner("⌛ Gemini Visionで読み取り中..."):
        for img in images:
            response = model.generate_content([PROMPT, img])
            full_text += response.text + "\n"

    st.markdown("### 🧾 Gemini Visionが読み取った結果")
    st.code(full_text)

    # CSVとして保存
    st.download_button("📥 CSVとしてダウンロード", full_text, file_name="tsucho.csv", mime="text/csv")
