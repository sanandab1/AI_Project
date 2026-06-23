import streamlit as st
import requests

st.title("AI Loan Approval System")

with st.form("loan_form"):
    applicant_id = st.text_input("Applicant ID")
    income = st.number_input("Income")
    credit_score = st.number_input("Credit Score")
    loan_amount = st.number_input("Loan Amount")
    liabilities = st.number_input("Liabilities")

    submit = st.form_submit_button("Submit")

if submit:
    payload = {
        "applicant_id": applicant_id,
        "age": 30,
        "income": income,
        "employment_type": "Salaried",
        "credit_score": credit_score,
        "loan_amount": loan_amount,
        "tenure": 24,
        "liabilities": liabilities,
        "location": "India"
    }

    response = requests.post(
        "http://localhost:8000/loan/process",
        json=payload
    )

    st.write(response.json())