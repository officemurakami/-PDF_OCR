import streamlit as st
import pytesseract
from pdf2image import convert_from_path
import pandas as pd
import re
import cv2
import numpy as np
from PIL import Image
import io

# OCR設定
tesseract_cmd = '/usr/bin/tesseract'  # Tesseractのパス
pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

# 画像の前処理関数
def preprocess_image(image):
    # グレースケール化
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # ノイズ除去
    gray = cv2.medianBlur(gray, 3)
    # 二値化
    _, binary = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    return binary

# PDFからテキストを抽出する関数
def extract_text_from_pdf(pdf_file):
    images = convert_from_path(pdf_file)
    text = ""
    for image in images:
        # OpenCV形式に変換
        open_cv_image = np.array(image)
        open_cv_image = open_cv_image[:, :, ::-1].copy()
        # 前処理
        processed_image = preprocess_image(open_cv_image)
        # OCR
        text += pytesseract.image_to_string(processed_image, lang='jpn')
    return text

# テキストをデータフレームに変換する関数
def text_to_dataframe(text):
    lines = text.split('\n')
    data = []
    for line in lines:
        # 正規表現で日付、摘要、支払金、預かり金、残高を抽出
        match = re.match(r'(\d{2}-\d{2}-\d{2})\s+(.+?)\s+([\d,]+)?\s+([\d,]+)?\s+([\d,]+)', line)
        if match:
            date, summary, withdrawal, deposit, balance = match.groups()
            # 和暦を西暦に変換
            date = convert_japanese_date_to_gregorian(date)
            # カンマを除去し数値に変換
            withdrawal = int(withdrawal.replace(',', '')) if withdrawal else 0
            deposit = int(deposit.replace(',', '')) if deposit else 0
            balance = int(balance.replace(',', ''))
            data.append([date, summary, withdrawal, deposit, balance])
    df = pd.DataFrame(data, columns=['日付', '摘要', '支払金', '預かり金', '残高'])
    return df

# 和暦の日付を西暦に変換する関数
def convert_japanese_date_to_gregorian(date_str):
    era, year, month, day = map(int, date_str.split('-'))
    if era == 1:  # 令和
        year += 2018
    elif era == 2:  # 平成
        year += 1988
    elif era == 3:  # 昭和
        year += 1925
    else:
        raise ValueError("対応していない元号です")
    return f"{year:04d}-{month:02d}-{day:02d}"

# Streamlitアプリの設定
st.title('通帳PDF OCR変換アプリ')
st.write('通帳のPDFファイルをアップロードすると、日付、摘要、支払金、預かり金、残高の形式で表示します。')

# ファイルアップロード
uploaded_file = st.file_uploader("PDFファイルを選択してください", type="pdf")

if uploaded_file is not None:
    # PDFからテキストを抽出
    text = extract_text_from_pdf(uploaded_file)
    # テキストをデータフレームに変換
    df = text_to_dataframe(text)
    # データフレームを表示
    st.write(df)
    # データフレームをCSVとしてダウンロード
    csv = df.to_csv(index=False).encode('utf-8-sig')
    st.download_button("CSVをダウンロード", csv, "output.csv", "text/csv")
