# 📄 invoice_parser.py
# 🔍 AI-Powered PDF Invoice Parser using Google Gemini and LangChain

from langchain_google_genai import GoogleGenerativeAI
from langchain.prompts import PromptTemplate
from pypdf import PdfReader
import pandas as pd
import re
import os
from dotenv import find_dotenv, load_dotenv

# Load environment variables from .env file (specifically the GEMINI_API_KEY)
_ = load_dotenv(find_dotenv())
GOOGLE_API_KEY = os.environ['GEMINI_API_KEY']

# Define the Gemini LLM model to use
llm_model = "gemini-1.5-flash"

# ----------------------------------------------------------------------------------------
# 📘 Step 1: Extract full text content from a PDF document
# ----------------------------------------------------------------------------------------
def get_pdf_text(pdf_doc):
    """
    Extracts and concatenates text from each page of a given PDF.

    Args:
        pdf_doc (file-like object): The uploaded PDF file.

    Returns:
        str: Full extracted text from the PDF.
    """
    text = ""
    pdf_read = PdfReader(pdf_doc)
    for page in pdf_read.pages:
        text += page.extract_text()
    return text

# ----------------------------------------------------------------------------------------
# 🧠 Step 2: Use Google Gemini to extract structured fields from PDF text
# ----------------------------------------------------------------------------------------
def extracted_data(pages_data):
    """
    Uses Gemini to intelligently extract invoice fields as a flat dictionary string.

    Args:
        pages_data (str): The full text of the invoice PDF.

    Returns:
        str: Flat dictionary in string format with extracted invoice data.
    """

    template = """
You are an intelligent invoice parser. Extract all relevant structured data from the given invoice text.

Fields may include:
- invoice_number
- billed_to
- from
- date (or issue_date)
- payment terms
- total_amount / total
- items (multiple)
- and many more

🧠 Instructions:
- Your output must be a single flat Python dictionary in string format and not a nested dictionary.
- Normalize all field names using snake_case.
- Do not match the field names word-to-word use it's word meaning to place values in column (e.g. `total` , `total amount` these field mean the same, like wise `quantity`, `item quantity` mean the same, like wise `item`, `items` mean the same) 
- Do not merge multiple values into a single dictionary.
- Use consistent keys across all entries (e.g., `item`, `description`, `quantity`, `unit_price`, `total`).
- Omit fields that are not present — no nulls or placeholders.
- Return **only** the valid Python dictionary string. No additional text.
- for fields which are completely different make a new field for them
- if invoice contains multiple items like ('item': 'Backpack', 'quantity': 1, 'unit_price': 1200.0, 'total': 1200.0 'item': 'Water Bottle', 'quantity': 1, 'unit_price': 300.0, 'total': 300.0)
  separate the fields as ('item':['Backpack','Water Bottle'],'quantity':[1,1],'total':[1200.0,600.0] and many more)

Text:
{pages}

Output:
"""

    # Create the prompt with LangChain's PromptTemplate
    prompt_template = PromptTemplate(template=template, input_variables=["pages"])

    # Initialize the Gemini LLM
    llm = GoogleGenerativeAI(model=llm_model, api_key=GOOGLE_API_KEY, temperature=0.4)

    # Get LLM response with formatted invoice prompt
    response = llm(prompt_template.format(pages=pages_data))
    return response

# ----------------------------------------------------------------------------------------
# 📊 Step 3: Build structured data from multiple invoice PDFs
# ----------------------------------------------------------------------------------------
def create_docs(user_pdf_list):
    """
    Iterates over PDF files, extracts text and structured invoice data, and compiles it into a DataFrame.

    Args:
        user_pdf_list (list): List of file-like PDF documents.

    Returns:
        pd.DataFrame: Structured data extracted from all uploaded PDFs.
    """

    all_data = []

    for filename in user_pdf_list:
        # Step 1: Extract raw text from PDF
        extracted_text = get_pdf_text(filename)

        # Step 2: Parse structured invoice data using LLM
        llm_data = extracted_data(extracted_text)

        # Use regex to extract dictionary block from LLM response
        pattern = r'{(.+)}'
        match = re.search(pattern, llm_data, re.DOTALL)

        if match:
            try:
                # Safely evaluate the dictionary string into a Python dict
                data_dict = eval('{' + match.group(1) + '}')
                print(data_dict)  # Optional: Debug print
                all_data.append(data_dict)
            except Exception as e:
                print(f"❌ Error parsing dictionary: {e}")
        else:
            print("⚠️ No valid dictionary found in response.")

    # Return a DataFrame with all the extracted records
    if all_data:
        return pd.DataFrame(all_data)
    else:
        return pd.DataFrame()
