import streamlit as st
import fitz  # PyMuPDF
from PIL import Image
import io
import google.generativeai as genai

# Gemini APIキーを設定（環境変数からも可）
genai.configure(api_key="YOUR_API_KEY")

# Geminiモデル設定（Vision対応）
model = genai.GenerativeModel(model_name="gemini-pro-vision")

generation_config = {
    "temperature": 0.4,
    "top_p": 1,
    "top_k": 32,
    "max_output_tokens": 2048,
}

# プロンプト文
prompt = """
この画像は銀行の通帳です。「日付, 摘要, 支払金額, 預かり金額, 残高」の形式でCSVに変換してください。

和暦は西暦に変換（05年→2023, 06年→2024）

支払・預かり金額は「※」が含まれる数字のみを抽出

残高は※が無くても数字があれば抽出

数字以外（例：店番、カデなど）は全て無視

項目がずれないよう、必ず5列で整形してください
"""

# PDFを画像に変換
def pdf_to_images(pdf_bytes):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    images = []
    for page in doc:
        pix = page.get_pixmap(dpi=300)  # 高DPI推奨
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        images.append(img)
    return images

# Streamlit UI
st.title("通帳PDF → CSV変換Bot（Gemini Vision）")

uploaded_file = st.file_uploader("通帳PDFをアップロード", type=["pdf"])

if uploaded_file is not None:
    with st.spinner("画像変換中..."):
        images = pdf_to_images(uploaded_file.read())

    all_results = []

    for i, image in enumerate(images):
        st.image(image, caption=f"ページ {i+1}", use_column_width=True)

        with st.spinner(f"ページ {i+1} を解析中..."):
            response = model.generate_content(
                [prompt, image],
                generation_config=generation_config,
            )
            result_text = response.text.strip()
            all_results.append(result_text)

        st.text_area(f"ページ {i+1} の結果", result_text, height=200)

    final_output = "\n".join(all_results)
    st.download_button("CSVをダウンロード", final_output, file_name="通帳変換結果.csv", mime="text/csv")
