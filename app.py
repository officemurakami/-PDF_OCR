import streamlit as st
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
from pdf2image import convert_from_path
import pandas as pd
import re
import os

# Tesseractのパスを指定（Windows環境の場合）
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# ストリームリットのUI設定
st.set_page_config(page_title="通帳PDFフォーマット変換ボット", page_icon="📄", layout="centered")
st.title("📄 通帳PDFフォーマット変換ボット")
st.caption("アップした通帳PDFから、5列に整形して表示・CSV保存できます。")

# アップロード
uploaded_file = st.file_uploader("📥 通帳PDFをアップロード", type="pdf")

def extract_text_from_pdf(pdf_file):
    images = convert_from_path(pdf_file)
    text_all = ""
    for img in images:
        text_all += pytesseract.image_to_string(img, lang='jpn')
    return text_all

def convert_text_to_table(text):
    lines = text.split('\n')
    data = []
    for line in lines:
        # 数字が複数含まれる行を抽出（残高、預かり、支払いを含む想定）
        numbers = re.findall(r"[0-9,]+", line)
        if len(numbers) >= 2:
            # 西暦変換（例：6-6-28 → 2024-06-28）
            date_match = re.search(r"[0-9]{1,2}-[0-9]{1,2}-[0-9]{1,2}", line)
            if date_match:
                era_year = int(line.split('-')[0])
                year = 2018 + era_year  # 05年→2023, 06年→2024 など
                month = line.split('-')[1].zfill(2)
                day = line.split('-')[2].zfill(2)
                date = f"{year}-{month}-{day}"
            else:
                date = ""

            # 数字を末尾から支払・預かり・残高と想定
            支払, 預かり, 残高 = "", "", ""
            if len(numbers) >= 3:
                支払 = numbers[-3] if "※" in line else ""
                預かり = numbers[-2] if "※" in line else ""
                残高 = numbers[-1]
            elif len(numbers) == 2:
                支払 = numbers[0] if "※" in line else ""
                残高 = numbers[1]

            # 摘要抽出（振込、引出、現金など）
            summary_match = re.search(r"(振込|現金|引出|ｶｰﾄﾞ|ATM|ﾌﾘｶﾞﾅ)", line)
            摘要 = summary_match.group(1) if summary_match else ""

            data.append([date, 摘要, 支払, 預かり, 残高])
    df = pd.DataFrame(data, columns=["日付", "摘要", "支払金額", "預かり金額", "残高"])
    return df

if uploaded_file:
    with st.spinner("⌛ テキストを抽出中..."):
        text = extract_text_from_pdf(uploaded_file)
        df = convert_text_to_table(text)

    st.markdown("### 📋 抽出結果プレビュー")
    st.dataframe(df, use_container_width=True)

    # CSVダウンロード
    csv = df.to_csv(index=False, encoding="utf-8-sig")
    st.download_button("📥 CSVとしてダウンロード", data=csv, file_name="converted.csv", mime="text/csv")
