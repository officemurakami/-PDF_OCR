import streamlit as st
from pdf2image import convert_from_bytes
import pytesseract
from PIL import Image
import pandas as pd
import re
from io import BytesIO

st.set_page_config(page_title="通帳PDF → 5列CSV整形", page_icon="📄", layout="wide")
st.title("📄 通帳PDFフォーマット変換ボット")

st.markdown("""
この画像は銀行の通帳です。  
**「日付, 摘要, 支払金額, 預かり金額, 残高」** の形式でCSVに変換してください。  

- 和暦は西暦に変換（例：05年 → 2023年）  
- 支払・預かり金額は「※」が含まれる数字のみを抽出  
- 残高は「※」がなくても抽出OK  
- 数字以外（例：店番、カデなど）はすべて無視  
- 必ず5列で整形（項目がずれないよう注意）
""")

uploaded_file = st.file_uploader("📥 通帳PDFをアップロード", type=["pdf"])

def convert_date(wareki_date):
    try:
        y, m, d = map(int, wareki_date.split("-"))
        base = {5: 2023, 6: 2024}  # 和暦→西暦変換ルール
        year = base.get(y, 2000 + y)
        return f"{year:04d}-{m:02d}-{d:02d}"
    except:
        return wareki_date

def extract_text_from_pdf(pdf_file):
    images = convert_from_bytes(pdf_file.read())
    text = ""
    for img in images:
        text += pytesseract.image_to_string(img, lang="jpn")
    return text

def parse_text(text):
    rows = []
    for line in text.split("\n"):
        line = line.strip()
        # 日付（例：6-6-28）と「※」のある数字列を含む行のみ対象
        if re.search(r"\d{1,2}-\d{1,2}-\d{1,2}", line) and "※" in line:
            # 日付
            date_match = re.search(r"\d{1,2}-\d{1,2}-\d{1,2}", line)
            date = convert_date(date_match.group()) if date_match else ""
            # 摘要（漢字ひらがなカタカナ）
            desc_match = re.search(r"[^\d\*※]+", line[10:])  # 数字と記号を除く部分
            desc = desc_match.group().strip() if desc_match else ""
            # 支払・預かり金額（※付き数字）
            amounts = re.findall(r"※[,\d]+", line)
            pay = amounts[0].replace("※", "").replace(",", "") if len(amounts) >= 1 else ""
            deposit = amounts[1].replace("※", "").replace(",", "") if len(amounts) >= 2 else ""
            # 残高（最後の数字列）
            balance_match = re.findall(r"\d{1,3}(?:,\d{3})*", line)
            balance = balance_match[-1].replace(",", "") if balance_match else ""
            rows.append([date, desc, pay, deposit, balance])
    return rows

if uploaded_file:
    try:
        text = extract_text_from_pdf(uploaded_file)
        parsed_data = parse_text(text)
        df = pd.DataFrame(parsed_data, columns=["日付", "摘要", "支払金額", "預かり金額", "残高"])
        st.text_area("📄 抽出テキスト（確認用）", text, height=250)
        st.markdown("### 📋 整形されたデータ（5列）")
        st.dataframe(df, use_container_width=True)

        csv = df.to_csv(index=False).encode("utf-8-sig")
        st.download_button("💾 CSVとしてダウンロード", csv, "通帳データ.csv", "text/csv")

    except Exception as e:
        st.error(f"エラーが発生しました: {e}")
