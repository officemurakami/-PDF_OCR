import streamlit as st
from pdf2image import convert_from_bytes
import pytesseract
from PIL import Image
import pandas as pd
import io
import re
from datetime import datetime

st.set_page_config(page_title="通帳PDFフォーマット変換ボット", page_icon="📄", layout="wide")
st.title("📄 通帳PDFフォーマット変換ボット")
st.write("アップした通帳PDFから、5列に整形して表示・CSV保存できます。")

uploaded_file = st.file_uploader("📥 通帳PDFをアップロード", type=["pdf"])

def convert_date(japanese_date):
    try:
        wareki, y, m, d = japanese_date.split("-")
        year = 1926 + int(y) if wareki == "6" else 1989 + int(y) if wareki == "H" else 2000 + int(y)
        return f"{year:04d}-{int(m):02d}-{int(d):02d}"
    except:
        return japanese_date

def extract_text_from_pdf(pdf_file):
    images = convert_from_bytes(pdf_file.read())
    text = ""
    for img in images:
        text += pytesseract.image_to_string(img, lang="jpn")
    return text

def parse_text_to_df(text):
    rows = []
    for line in text.split("\n"):
        match = re.search(r"(\d{1,2}-\d{1,2}-\d{1,2})\s+(.*?)\s+(\d{1,3}(,\d{3})*)?\s*(\d{1,3}(,\d{3})*)?\s*(\d{1,3}(,\d{3})*)?", line)
        if match:
            date = convert_date(match.group(1))
            desc = match.group(2)
            withdraw = match.group(3) or ""
            deposit = match.group(5) or ""
            balance = match.group(7) or ""
            rows.append([date, desc, withdraw.replace(",", ""), deposit.replace(",", ""), balance.replace(",", "")])
    return pd.DataFrame(rows, columns=["日付", "摘要", "支払金", "預かり金", "残高"])

if uploaded_file:
    try:
        text = extract_text_from_pdf(uploaded_file)
        df = parse_text_to_df(text)
        st.dataframe(df)
        csv = df.to_csv(index=False).encode("utf-8-sig")
        st.download_button("💾 CSVとしてダウンロード", csv, "tsucho_data.csv", "text/csv")
    except Exception as e:
        st.error(f"エラーが発生しました: {e}")
