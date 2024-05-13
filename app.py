import streamlit as st
from PyPDF2 import PdfReader
import requests

# Função para extrair texto de um PDF


def extract_text_from_pdf(pdf_file):
    pdf_reader = PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

# Função para fazer uma pergunta à API do ChatGPT


def ask_chatgpt(question, context):
    api_key = st.secrets["openai"]["api_key"]
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}',
    }
    data = {
        "model": "gpt-4",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": context},
            {"role": "user", "content": question}
        ]
    }
    response = requests.post(
        'https://api.openai.com/v1/chat/completions', headers=headers, json=data)
    return response.json()['choices'][0]['message']['content']


# Interface do Streamlit
st.title("Ferramenta de Análise de PDFs de Licitação")
st.write("Faça upload dos PDFs, defina instruções e faça perguntas para extrair informações.")

# Upload de múltiplos PDFs
uploaded_files = st.file_uploader(
    "Upload dos PDFs", type=["pdf"], accept_multiple_files=True)

if uploaded_files:
    pdf_texts = []
    for uploaded_file in uploaded_files:
        text = extract_text_from_pdf(uploaded_file)
        pdf_texts.append(text)
    combined_text = " ".join(pdf_texts)

    st.text_area("Texto extraído", value=combined_text, height=300)

    question = st.text_input("Faça sua pergunta sobre os PDFs")

    if st.button("Enviar Pergunta"):
        if question:
            response = ask_chatgpt(question, combined_text)
            st.write("Resposta:")
            st.write(response)
        else:
            st.write("Por favor, insira uma pergunta.")
