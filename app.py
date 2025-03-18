import streamlit as st
import pandas as pd
import pytesseract
from pdf2image import convert_from_path
import re

# 和暦変換
def convert_reiwa_date(raw_date):
    try:
        parts = raw_date.split("-")
        year = 2018 + int(parts[0])
        return f"{year:04d}-{int(parts[1]):02d}-{int(parts[2]):02d}"
    except:
        return raw_date

# テキスト整形
def parse_bank_text(text):
    lines = text.strip().split("\n")
    records = []
    for line in lines:
        match = re.match(r"(\d{2}-\d{2}-\d{2})\s+(.*?)\s+([\d,]+)?\s+([\d,]+)?\s+([\d,]+)", line)
        if match:
            date = convert_reiwa_date(match.group(1))
            summary = match.group(2).strip()
            withdrawal = match.group(3).replace(',', '') if match.group(3) else ""
            deposit = match.group(4).replace(',', '') if match.group(4) else ""
            balance = match.group(5).replace(',', '')
            records.append([date, summary, withdrawal, deposit, balance])
    return pd.DataFrame(records, columns=["日付", "摘要", "支払金", "預かり金", "残高"])

# OCR処理
def extract_text_from_pdf(uploaded_file):
    images = convert_from_path(uploaded_file)
    text = ""
    for image in images:
        text += pytesseract.image_to_string(image, lang='jpn')
    return text

# Streamlitアプリ本体
st.set_page_config(page_title="通帳PDFフォーマット変換ボット", layout="centered")
st.title("📄 通帳PDFフォーマット変換ボット")
st.markdown("アップした通帳PDFから、5列に整形して表示・CSV保存できます。")

uploaded_file = st.file_uploader("📤 通帳PDFをアップロード", type="pdf")

if uploaded_file:
    with st.spinner("⌛ OCR処理中..."):
        text = extract_text_from_pdf(uploaded_file)
        df = parse_bank_text(text)

    if not df.empty:
        st.success("✅ テキスト抽出 & 整形完了！")
        st.dataframe(df, use_container_width=True)

        # CSV出力
        csv = df.to_csv(index=False).encode("utf-8-sig")
        st.download_button("⬇️ CSVをダウンロード", data=csv, file_name="bank_data.csv", mime="text/csv")
    else:
        st.warning("⚠️ 認識できませんでした。PDFレイアウトをご確認ください。")
