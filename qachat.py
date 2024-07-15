from dotenv import load_dotenv
import streamlit as st
import os
import google.generativeai as genai
import fitz  # PyMuPDF
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

# Configure Google Generative AI
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Function to load Gemini Pro model and get responses
model = genai.GenerativeModel("gemini-pro")
chat = model.start_chat(history=[])

def extract_text_from_pdf(pdf_file):
    text = ""
    for page in pdf_file:
        text += page.get_text()
    return text

def extract_text_from_txt(txt_file):
    return txt_file.read().decode("utf-8")

def is_question_in_context(question, content):
    return any(word in content.lower() for word in question.lower().split())

def get_gemini_response(question, content):
    if is_question_in_context(question, content):
        prompt = f"Based on the following content, answer the question: \n\n{content}\n\nQuestion: {question}\n\nAnswer:"
        try:
            response = chat.send_message(prompt, stream=True)
            return response
        except ValueError as e:
            st.error(f"Error: {str(e)}")
            return None
    else:
        return ["Mind your own business."]

def fallback_answer(question, content):
    if is_question_in_context(question, content):
        return ["This is the answer from local content."]  # Simple placeholder response
    else:
        return ["Mind your own business."]

# Initialize Streamlit app
st.set_page_config(page_title="Vidya Guru ChatBot", page_icon=":books:", layout="wide")

# Add custom CSS for better UI
st.markdown(
    """
    <style>
    .header-style {
        font-size: 35px;
        color: #4CAF50;
        text-align: center;
        font-weight: bold;
    }
    .chat-history-style {
        font-size: 18px;
        color: #333333;
        background-color: #E8E8E8;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 5px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Page title and header
st.markdown("<div class='header-style'>Vidya Guru ChatBot</div>", unsafe_allow_html=True)

# Initialize session state for chat history and content if it doesn't exist
if 'chat_history' not in st.session_state:
    st.session_state['chat_history'] = []
if 'content' not in st.session_state:
    st.session_state['content'] = ""
if 'last_interaction' not in st.session_state:
    st.session_state['last_interaction'] = datetime.now()

# File uploader
uploaded_file = st.file_uploader("Upload a PDF or TXT file", type=["pdf", "txt"])
if uploaded_file is not None:
    if uploaded_file.type == "application/pdf":
        pdf_document = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        st.session_state['content'] = extract_text_from_pdf(pdf_document)
    elif uploaded_file.type == "text/plain":
        st.session_state['content'] = extract_text_from_txt(uploaded_file)

# Check if one minute has passed since the last interaction
current_time = datetime.now()
time_diff = current_time - st.session_state['last_interaction']
if time_diff < timedelta(minutes=1):
    st.warning(f"Please wait for {60 - time_diff.seconds} seconds before asking another question.")
else:
    # Input field and button
    input = st.text_input("Input: ", key="input", placeholder="Ask a question")
    submit = st.button("Ask the question")

    # Chat loop
    if submit and input:
        if input.strip().lower() == "bye":
            st.session_state['chat_history'].append(("Bot", "Goodbye!"))
        else:
            try:
                # Get response from Gemini Pro model
                response = get_gemini_response(input, st.session_state['content'])
                if response:
                    st.session_state['chat_history'].append(("You", input))
                    if isinstance(response, list):
                        st.session_state['chat_history'].append(("Bot", response[0]))
                    else:
                        for chunk in response:
                            st.session_state['chat_history'].append(("Bot", chunk.text))
            except Exception as e:
                st.session_state['chat_history'].append(("Bot", "I apologize, I encountered an error and couldn't process your request."))
                st.session_state['chat_history'].append(("Bot", f"Error: {str(e)}"))
                # Fallback to local content search
                local_response = fallback_answer(input, st.session_state['content'])
                st.session_state['chat_history'].append(("Bot", local_response[0]))

            # Update last interaction time
            st.session_state['last_interaction'] = datetime.now()

# Display chat history
st.subheader("The Chat History is")
for role, text in st.session_state['chat_history']:
    st.write(f"<div class='chat-history-style'><strong>{role}:</strong> {text}</div>", unsafe_allow_html=True)
