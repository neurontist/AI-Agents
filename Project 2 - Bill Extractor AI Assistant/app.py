# 📄 app.py
# 💡 Streamlit Web App: AI-Powered Bill Data Extractor using Gemini LLM

import streamlit as st
from helpers import *  # Contains functions like create_docs (PDF parser + Gemini extractor)

# ------------------------------
# 🎯 App Title
# ------------------------------
st.title("Bill Extractor AI Assistant 🤖")

# ------------------------------
# 📤 PDF File Upload
# ------------------------------
files = st.file_uploader(
    label='Upload your bills in PDF format only',
    accept_multiple_files=True,
    type=['pdf']
)

# ------------------------------
# 🔘 Extract Button
# ------------------------------
extract_button = st.button('Extract bill data...', key='1')

# ------------------------------
# ⚙️ Extraction Logic
# ------------------------------
if extract_button:
    with st.spinner('Extracting text from file...'):
        # Step 1: Call helper to extract text + parse data
        doc = create_docs(files)

        if not doc.empty:
            # Step 2: Normalize complex data (lists/dicts) to strings for display compatibility
            for col in doc.columns:
                doc[col] = doc[col].apply(lambda x: ', '.join(map(str, x)) if isinstance(x, list) else x)

            # Step 3: Display extracted results
            st.write("🔍 Extracted Data Preview:")
            st.write(doc.head())

            # Step 4: Try to auto-detect total amount column
            possible_total_columns = [
                col for col in doc.columns
                if 'total' in col.lower() and 'amount' in col.lower()
            ]

            # Step 5: Display average bill amount if total found
            if possible_total_columns:
                total_col = possible_total_columns[0]
                try:
                    doc[total_col] = pd.to_numeric(doc[total_col], errors='coerce')
                    st.write(f"💰 Average bill amount (from '{total_col}'): ", doc[total_col].mean())
                except Exception as e:
                    st.warning(f"⚠️ Could not convert '{total_col}' to numeric: {e}")
            else:
                st.warning("⚠️ No 'Total Amount' field found in the extracted data.")

            # Step 6: Enable CSV download of parsed data
            convert_to_csv = doc.to_csv(index=False).encode("utf-8")
            st.download_button(
                label='📥 Download data as CSV',
                data=convert_to_csv,
                file_name='Bill_CSV.csv',
                mime='text/csv',
                key="download-csv"
            )

            st.success("✅ Extraction completed successfully!")
        else:
            st.error("❌ No data could be extracted. Please check your PDF files.")
