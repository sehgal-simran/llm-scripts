import re
import PyPDF2
import pandas as pd
import argparse
import mysql.connector
import openai
import time
from datetime import datetime
from observo_llm import setup_logging, track_performance

# Initialize logging
logger = setup_logging()

# Initialize argument parser
parser = argparse.ArgumentParser()
parser.add_argument("-i", "--inputFile", help="Path of input file")
parser.add_argument("-o", "--outputFile", help="Path of output file")
args = parser.parse_args()

# Connect to MySQL database
cnx = mysql.connector.connect(user='root', password='1234',
                              host='127.0.0.1',
                              port='3307',
                              database='polarbear')
cursor = cnx.cursor()

# Read PDF and extract text
def extract_text_from_pdf(pdf_path):
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ''.join(page.extract_text() for page in reader.pages if page.extract_text())
    return text

# Parse the text to extract transactions
def parse_transactions(text):
    transactions = []
    pattern = re.compile(r'(\d{2}/\d{2}/\d{4}).+?(\d{2}:\d{2}:\d{2}).+?([A-Z0-9].+?)\s+([\d,]+\.\d{2})( Cr)?')
    for match in pattern.findall(text):
        date, time, description, amount, credit = match
        amount = float(amount.replace(',', ''))
        if credit:
            amount *= -1
        transactions.append({"Date": datetime.strptime(date, '%d/%m/%Y').date(), "Description": description.strip(), "Amount": amount})
    return transactions

# Clean the Description field
def clean_description(description):
    description = description.upper()
    query = "SELECT company_name, keyword FROM company_mapping;"
    cursor.execute(query)
    company_keywords = {keyword: company_name for company_name, keyword in cursor}
    
    for keyword in company_keywords:
        if keyword in description:
            return company_keywords[keyword]
    return description

# Classify transaction using OpenAI
openai.api_key = "your-openai-api-key"
@track_performance(logger, "Transaction Classification")
def classify_transaction(description):
    prompt = f"""
    Classify the following financial transaction into one of the categories: 
    ['Food & Dining', 'Shopping', 'Groceries', 'Bills & Utilities', 'Entertainment', 'Travel', 'Healthcare', 'Other'].
    
    Transaction description: {description}
    
    Category:
    """
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "system", "content": "You are an expert in financial transactions classification."},
                      {"role": "user", "content": prompt}]
        )
        category = response['choices'][0]['message']['content'].strip()
        logger.info(f"Transaction classified: {description} -> {category}")
        return category
    except Exception as e:
        logger.error(f"Error in classification: {str(e)}")
        return "Other"

# Extract text from PDF
pdf_text = extract_text_from_pdf(args.inputFile)

# Parse transactions
transactions = parse_transactions(pdf_text)
filtered_transactions = []

# Process and classify transactions
for transaction in transactions:
    transaction["Description"] = clean_description(transaction["Description"])
    if not (transaction["Description"] == "NETBANKING" and transaction["Amount"] < 0) and (transaction['Amount'] > 20):
        transaction["Category"] = classify_transaction(transaction["Description"])
        filtered_transactions.append(transaction)

# Insert into database
add_transaction = ("INSERT INTO transactions "
                   "(transaction_date, cost, company_name, category)"
                   "VALUES (%(Date)s, %(Amount)s, %(Description)s, %(Category)s)")

cursor.executemany(add_transaction, filtered_transactions)
cnx.commit()

# Save to CSV
df = pd.DataFrame(filtered_transactions)
df.to_csv(args.outputFile, index=False)

logger.info(f"CSV file saved: {args.outputFile}")
cnx.close()