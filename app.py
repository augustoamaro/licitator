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
    api_key = st.secrets["openai"]["openai_key"]
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}',
    }

    instructions = """
    Você é um assistente de licitações chamado BidsIA. Serve para analisar Editais que estarão em PDF. A análise deve ser fiel aos documentos, não invente nada, a linguagem é exclusivamente em português e sempre que o usuário digitar "relatório", você consulta o material enviado nunca, nunca consulte a internet, somente os arquivos enviados e responder as perguntas abaixo:
    1. **Nome do Órgão**;
    2. **Qual é o Pregão Eletrônico e o Edital?**
    2.1. **Sempre traga os números de identificação**;
    2.2. **liste-os um embaixo do outro**;
    3. **Qual site ou portal será a disputa da licitação/pregão**;
    4. **Qual lei LEI o edital se enquadra (8.666/93 ou 14.133/21)**
    4.1. **O Edital vai se basear em uma das duas leis acima (8.666/93 ou 14.133/21), esta informação tem no edital**;
    5. **Qual objeto (objetivo) deste pregão?**;
    6. **Qual o valor total (global) da licitação**;
    6.1. **Quando falar em valor global pode estar na licitação também como valor estimado**;
    7. **Qual o modo do pregão (modo de disputa)**;
    8. **Qual proposta? Ao responder essa pergunta, organize em listas**;
    9. **Qual critérios de julgamento?**;
    10. **Liste as habilitações (habilidades) necessárias ou documento de habilitação ou documentos exigidos para participar do Pregão**;
    10.1. **Mostre toda documentação exigida. Quando for apresentar as habilitações, liste elas por tópicos, um embaixo do outro para melhor entendimento e explique cada habilitação necessária. Quando falar em habilidades, procure todos os documentos/habilidades, também chamados de comprovantes e alvarás para participar da licitação**;
    10.2. **Seja completo e não resuma**;
    11. **Em que data será permitido o cadastro? A inscrição**;
    12. **Qual data e hora que será a disputa da licitação?**
    12.1. **Quando falo em data e hora do pregão pode ser também: Horário e Data do Pregão, Momento e Data da Licitação, Dia e Hora do Leilão, Data e Horário da Concorrência, Programação da Disputa do Pregão, Agenda da Licitação, Horário e Dia da Adjudicação, Marcador Temporal da Disputa do Pregão**;
    13. **Duração do Contrato**:
    13.1. **Duração do Contrato, o mesmo que: Período de Contrato, Vigência do Contrato, Tempo de Vínculo, Prazo do Contrato, Extensão do Contrato, Período de Validade do Contrato, Termo do Contrato, Tempo de Compromisso, Período de Acordo**;
    14. **Existe alguma especificação quanto as casas decimais após a vírgula (se aceita 0,01 ou 0,0001 ou negativo, ou 0,00) para a formação de preço dentro da disputa?**
    14.1. **Nunca invente uma resposta, se não achar menções referentes as casas decimais utilizadas escreva na resposta "Não existe menções as casas decimais utilizadas, sugiro entrar em contato com a prefeitura para maiores esclarecimentos"**.
    15. **Sugestão de Agência: (RM, FACTO, GLOBAL, VOARE, ESTAU e PORTAL)**:
    15.1. **Deve sugerir a Agência RM quando o Edital for necessário que a agência tenha IATA próprio e atestados companhias próprio (se o edital exige IATA e não dá a opção de consolidadora, só pode sugerir a Agência RM)**;
    15.2. **A Agência RM possui filial em DF/MA/RJ/RN, se o órgão for de algum desses lugares, sugira Agência RM**;
    15.3. **Sugira a Agência RM, quando o valor global da licitação for maior ou igual a R$ 3.000.000,00 (Três milhões de reais), se o valor global for menor não for menor que R$ 3.000.000,00 não indique a Agência RM**;
    15.4. **Sugira a Agência Voar se o edital for de Tocantins (os editais de TO, sempre sugira a Agência Voar)**;
    15.5. **Sugira a Agência Facto se o edital for de São Paulo, sempre SP sugerir Agência Facto**;
    15.6. **Quando o Edital for de Santa Catarina sugira as agências: Global, Estau, Portal**;
    15.6.1 **Quando o valor Global for maior que R$ 1.000.000 sugira a Agência Estau**;
    15.6.2 **Quando o valor Global for menor que R$ 1.000.000 sugira a Agência Portal**;
    15.7. **Se o critério de julgamento é maior desconto no bilhete sugira Agência Facto, Agência Estau, Agência Portal ou Agência Global**.
    """

    data = {
        "model": "gpt-4o",
        "messages": [
            {"role": "system", "content": instructions},
            {"role": "user", "content": f"Context: {context}\n\nPergunta: {question}"}
        ]
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
st.title("Assistente de PDFs")
st.write("Faça upload de PDFs e faça perguntas sobre o conteúdo.")

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
    st.session_state.messages.append({"role": "user", "content": user_message})

    with st.spinner("O assistente está pensando..."):
        response = ask_chatgpt(user_message, context)

    st.session_state.messages.append(
        {"role": "assistant", "content": response})
    st.session_state.user_input = ""


# Exibir mensagens
for message in st.session_state.messages:
    if message["role"] == "user":
        st.write(f"**Usuário:** {message['content']}")
    else:
        st.write(f"**Assistente:** {message['content']}")

# Campo de entrada de mensagem
st.text_input("Digite sua pergunta:", key="user_input", on_change=send_message)


# import streamlit as st
# from PyPDF2 import PdfReader
# import requests
# import google.generativeai as genai

# # Configurar a API do Google Generative AI
# google_api_key = st.secrets["gemini"]["google_api_key"]
# genai.configure(api_key=google_api_key)

# # Função para extrair texto de um PDF


# def extract_text_from_pdf(pdf_file):
#     pdf_reader = PdfReader(pdf_file)
#     text = ""
#     for page in pdf_reader.pages:
#         text += page.extract_text()
#     return text


# def ask_google_ai(question, context):
#     generation_config = {
#         "candidate_count": 1,
#         "temperature": 0.5,
#     }
#     prompt = f"Contexto: {context}\n\nPergunta: {question}"
#     response = genai.GenerativeModel(
#         model_name="gemini-1.5-pro-latest", generation_config=generation_config)

#     if response and 'candidates' in response and len(response['candidates']) > 0:
#         return response['candidates'][0]['output']
#     else:
#         return "Nenhuma resposta válida foi retornada pela API."


# # Interface do Streamlit
# st.title("Assistente de PDFs")
# st.write("Faça upload de PDFs e faça perguntas sobre o conteúdo.")

# # Upload de PDFs
# uploaded_files = st.file_uploader(
#     "Upload de PDFs", type=["pdf"], accept_multiple_files=True)

# context = ""

# if uploaded_files:
#     for uploaded_file in uploaded_files:
#         text = extract_text_from_pdf(uploaded_file)
#         context += text

# if "messages" not in st.session_state:
#     st.session_state.messages = []

# # Função para enviar mensagem


# def send_message():
#     user_message = st.session_state.user_input
#     st.session_state.messages.append({"role": "user", "content": user_message})

#     with st.spinner("O assistente está pensando..."):
#         response = ask_google_ai(user_message, context)

#     st.session_state.messages.append(
#         {"role": "assistant", "content": response})
#     st.session_state.user_input = ""


# # Exibir mensagens
# for message in st.session_state.messages:
#     if message["role"] == "user":
#         st.write(f"**Usuário:** {message['content']}")
#     else:
#         st.write(f"**Assistente:** {message['content']}")

# # Campo de entrada de mensagem
# st.text_input("Digite sua pergunta:", key="user_input", on_change=send_message)
