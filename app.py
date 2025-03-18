import streamlit as st
import fitz  # PyMuPDF
from PIL import Image
import pytesseract
import io
import re
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="通帳PDFフォーマット変換ボット", page_icon="📄", layout="centered")

st.title("📄 通帳PDFフォーマット変換ボット")
st.caption("アップした通帳PDFから、5列に整形して表示・CSV保存できます。")

uploaded_file = st.file_uploader("📥 通帳PDFをアップロード", type=["pdf"])

def convert_jp_date(jp_date):
    try:
        era, year, month, day = jp_date.split("-")
        year = int(year)
        if era == "05":
            year += 2018  # 令和開始
        elif era == "04":
            year += 1988  # 平成開始
        elif era == "03":
            year += 1925  # 昭和開始
        elif era == "02":
            year += 1911  # 明治開始
        elif era == "01":
            year += 1867  # 大正開始
        else:
            year = 2000 + int(era)
        return f"{year}-{month}-{day}"
    except:
        return jp_date

def extract_text_from_pdf(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    text = ""
    for page in doc:
        pix = page.get_pixmap(dpi=300)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        text += pytesseract.image_to_string(img, lang="jpn")
    return text

def extract_table_data(text):
    # 通帳の取引行データ抽出 (例: "05-01-20  振込  10,000   20,000  50,000")
    pattern = r"(\d{2}-\d{2}-\d{2})\s+(.+?)\s+([\d,]+)?\s*([\d,]+)?\s+([\d,]+)"
    matches = re.findall(pattern, text)
    data = []
    for m in matches:
        row = {
            "日付": convert_jp_date(m[0]),
            "摘要": m[1].strip(),
            "支払金": m[2].replace(",", "") if m[2] else "",
            "預かり金": m[3].replace(",", "") if m[3] else "",
            "残高": m[4].replace(",", "")
        }
        data.append(row)
    return pd.DataFrame(data)

if uploaded_file:
    with st.spinner("⌛ OCRと変換中..."):
        try:
            text = extract_text_from_pdf(uploaded_file)
            df = extract_table_data(text)

            if not df.empty:
                st.success("✅ 変換完了！")
                st.dataframe(df, use_container_width=True)
                csv = df.to_csv(index=False).encode("utf-8-sig")
                st.download_button("📥 CSVとしてダウンロード", csv, "通帳変換結果.csv", "text/csv")
            else:
                st.warning("⚠ テーブルデータが見つかりませんでした。PDFのレイアウトをご確認ください。")

        except Exception as e:
            st.error(f"エラーが発生しました: {e}")
