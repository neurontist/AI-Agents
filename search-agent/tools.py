from langchain.tools import tool
from typing import List, Dict
import gspread
import smtplib
from email.message import EmailMessage
import os
import wikipedia as wp

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
EMAIL_APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD")

gc = gspread.service_account("service_account.json")
sheet = gc.open("Contact Details")
worksheet = sheet.sheet1

@tool(description='''Read all rows from the Google Sheet named 'Contact Details' (worksheet.sheet1).\

No inputs. Returns a list of dictionaries where each dictionary represents a row and maps column names to values (e.g. {'Name': 'Emma', 'Email': 'emma@example.com'}).\

Use this tool only to read data from the canonical Google Sheet. Do not invent values — if no row matches a query, return an empty list.''')
def read_records() -> List[Dict]:
    """Fetching all the records from google sheet's worksheet.

    Returns
    -------
    List[Dict]
        List of row dictionaries read from the 'Contact Details' Google Sheet (worksheet.sheet1).
    """
    records = worksheet.get_all_records()
    print("\n-------Records--------\n")
    print(records)
    return records


@tool(description='''Filter a list of record dictionaries by an exact, case-insensitive match on a specified column.

Inputs: records (List[Dict]) - list returned by read_records; name (str) - value to match; column (str) - column name to search (allowed: 'Name', 'Email', 'Phone', 'Role').

Returns a list of matching row dictionaries. Do not fabricate results; return an empty list when no matches are found.''')
def fetch_selected_records(records: List[Dict], name: str, column: str) -> List[Dict] | None:
    """Fetch the records from database related to user query.

    Performs a case-insensitive exact comparison of the provided `name` against the
    value in `column` for each record in `records`.
    """
    selected_records = [r for r in records if r.get(column, "").lower() == name.lower()]
    print("\n-------Selected Records--------\n")
    print(selected_records)
    return selected_records


@tool(description='''Send an email using Gmail SMTP.

Inputs: to (str) - recipient email address, subject (str), body (str).

This tool reads SMTP credentials from environment variables EMAIL_ADDRESS and EMAIL_APP_PASSWORD and will send a real email via smtp.gmail.com. Use this tool only when the user explicitly requests sending an email (do not send unprompted). Returns a confirmation string on success.''')
def send_email(to: str, subject: str, body: str) -> str:
    """Send an email using Gmail SMTP.

    Environment variables required:
    - EMAIL_ADDRESS
    - EMAIL_APP_PASSWORD
    """
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = to
    msg.set_content(body)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(EMAIL_ADDRESS, EMAIL_APP_PASSWORD)
        smtp.send_message(msg)

    return f"Email sent to {to}"

@tool(description='''Search Wikipedia for the given query and return up to two results.

Input: query (str). Returns a list of result dictionaries, each with keys: 'page_content' (summary), 'type' ('Document'), and 'metadata' with 'url'. Skips disambiguation pages. Do not add extra commentary or invent content; return only factual summaries from Wikipedia pages.''')
def retrieve(query: str) -> list:
    print("In retriever")
    """Get up to two search wikipedia results.

    Returns
    -------
    list
        List of result dicts with 'page_content', 'type', and 'metadata'.
    """
    results = []
    for term in wp.search(query, results=10):
        try:
            page = wp.page(term, auto_suggest=False)
            results.append({
                "page_content": page.summary,
                "type": "Document",
                "metadata": {"url": page.url}
            })
        except wp.DisambiguationError:
            pass
        if len(results) >= 2:
            return results
    return results

