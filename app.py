import streamlit as st
from PyPDF2 import PdfReader
import requests
import mysql.connector
from mysql.connector import Error

# Função para testar a conexão com o banco de dados


# def test_db_connection():
#     try:
#         connection = mysql.connector.connect(
#             host=st.secrets["mysql"]["host"],
#             port=st.secrets["mysql"]["port"],
#             user=st.secrets["mysql"]["user"],
#             password=st.secrets["mysql"]["password"],
#             database=st.secrets["mysql"]["database"]
#         )
#         if connection.is_connected():
#             db_info = connection.get_server_info()
#             st.write(f"Connected to MySQL Server version {db_info}")
#             connection.close()
#     except Error as e:
#         st.write(f"Error while connecting to MySQL: {e}")


# test_db_connection()

# Função de autenticação


def authenticate(username, password):
    try:
        connection = mysql.connector.connect(
            host=st.secrets["mysql"]["host"],
            port=st.secrets["mysql"]["port"],
            user=st.secrets["mysql"]["user"],
            password=st.secrets["mysql"]["password"],
            database=st.secrets["mysql"]["database"]
        )
        cursor = connection.cursor(dictionary=True)
        query = "SELECT * FROM users WHERE username = %s AND password = %s"
        cursor.execute(query, (username, password))
        user = cursor.fetchone()
        cursor.close()
        connection.close()
        if user:
            st.session_state.role = user['role']
            return True
        return False
    except Error as e:
        st.write(f"Error: {e}")
        return False

# Função para obter as instruções e temperatura


def get_instructions():
    try:
        connection = mysql.connector.connect(
            host=st.secrets["mysql"]["host"],
            port=st.secrets["mysql"]["port"],
            user=st.secrets["mysql"]["user"],
            password=st.secrets["mysql"]["password"],
            database=st.secrets["mysql"]["database"]
        )
        cursor = connection.cursor(dictionary=True)
        query = "SELECT * FROM instructions LIMIT 1"
        cursor.execute(query)
        instructions = cursor.fetchone()
        cursor.close()
        connection.close()
        if instructions:
            return instructions['text'], instructions['temperature']
        return "", 0.7
    except Error as e:
        st.write(f"Error: {e}")
        return "", 0.7

# Função para salvar as instruções e temperatura


def save_instructions(text, temperature):
    try:
        connection = mysql.connector.connect(
            host=st.secrets["mysql"]["host"],
            port=st.secrets["mysql"]["port"],
            user=st.secrets["mysql"]["user"],
            password=st.secrets["mysql"]["password"],
            database=st.secrets["mysql"]["database"]
        )
        cursor = connection.cursor()
        query = "REPLACE INTO instructions (id, text, temperature) VALUES (1, %s, %s)"
        cursor.execute(query, (text, temperature))
        connection.commit()
        cursor.close()
        connection.close()
    except Error as e:
        st.write(f"Error: {e}")

# Função para extrair texto de um PDF


def extract_text_from_pdf(pdf_file):
    pdf_reader = PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

# Função para fazer uma pergunta à API do ChatGPT


def ask_chatgpt(question, context, temperature, instructions):
    api_key = st.secrets["openai"]["openai_key"]
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}',
    }

    data = {
        "model": "gpt-4o",
        "messages": [
            {"role": "system", "content": instructions},
            {"role": "user", "content": f"Context: {context}\n\nPergunta: {question}"}
        ],
        "temperature": temperature
    }
    response = requests.post(
        'https://api.openai.com/v1/chat/completions', headers=headers, json=data)

    if response.status_code == 200:
        response_json = response.json()
        if 'choices' in response_json and len(response_json['choices']) > 0:
            return response_json['choices'][0]['message']['content']
        else:
            return "Nenhuma resposta válida foi retornada pela API."
    else:
        return f"Erro ao chamar a API: {response.status_code} - {response.text}"

# Interface do Streamlit


def main():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.role = ""

    if not st.session_state.authenticated:
        st.title("Login")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if authenticate(username, password):
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos")
    else:
        if "instructions" not in st.session_state or "temperature" not in st.session_state:
            instructions, temperature = get_instructions()
            st.session_state.instructions = instructions
            st.session_state.temperature = temperature

        st.sidebar.title("Administração")
        if st.session_state.role == "admin":
            st.sidebar.write("Bem-vindo, Administrador")
            st.sidebar.text_area("Instruções", key="instructions", height=300)
            st.sidebar.slider("Temperatura", 0.0, 1.0,
                              st.session_state.temperature, key="temperature")
            if st.sidebar.button("Salvar Instruções"):
                save_instructions(st.session_state.instructions,
                                  st.session_state.temperature)
                st.success("Instruções salvas com sucesso!")
        else:
            st.sidebar.write("Acesso restrito ao administrador")

        st.title("Assistente de Licitações BidsIA")

        # Upload de PDFs
        uploaded_files = st.file_uploader(
            "Upload de PDFs", type=["pdf"], accept_multiple_files=True)

        context = ""
        if uploaded_files:
            for uploaded_file in uploaded_files:
                text = extract_text_from_pdf(uploaded_file)
                context += text

        if "messages" not in st.session_state:
            st.session_state.messages = []

        # Função para enviar mensagem
        def send_message():
            user_message = st.session_state.user_input
            if user_message:
                st.session_state.messages.append(
                    {"role": "user", "content": user_message})

                with st.spinner("O assistente está pensando..."):
                    response = ask_chatgpt(
                        user_message, context, st.session_state.temperature, st.session_state.instructions)

                st.session_state.messages.append(
                    {"role": "assistant", "content": response})
                st.session_state.user_input = ""

        # Função para limpar mensagens
        def clear_messages():
            st.session_state.messages = []

        # Exibir mensagens
        for message in st.session_state.messages:
            if message["role"] == "user":
                st.write(f"**Usuário:** {message['content']}")
            else:
                st.write(f"**Assistente:** {message['content']}")

        # Campo de entrada de mensagem e botões de enviar e limpar
        st.text_input("Digite sua pergunta:",
                      key="user_input", on_change=send_message)
        col1, col2, col3 = st.columns([1, 6, 1])
        with col1:
            st.button("Enviar", on_click=send_message)
        with col2:
            st.button("Limpar Conversa", on_click=clear_messages)


if __name__ == "__main__":
    main()
