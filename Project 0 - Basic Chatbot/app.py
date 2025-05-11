from langchain_google_genai import ChatGoogleGenerativeAI
import streamlit as st
import os
from dotenv import load_dotenv , find_dotenv
from langchain.schema import (SystemMessage , AIMessage , HumanMessage)


load_dotenv(find_dotenv())
GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY")

llm_model = "gemini-1.5-pro"

st.header("Hey I'm your GPT!")

if 'Messagestate' not in st.session_state:
    st.session_state.Messagestate = [
        SystemMessage(content="You are a helpful assistant")
    ]

def load_message(question):
    st.session_state.Messagestate.append(HumanMessage(content=question))
    assistant_answer = llm(st.session_state.Messagestate)
    st.session_state.Messagestate.append(AIMessage(content=assistant_answer.content))
    return assistant_answer.content


query = st.text_input("You ",key="user_input")


llm = ChatGoogleGenerativeAI(model=llm_model,temperature=0.7,google_api_key=GOOGLE_API_KEY)

button = st.button("Generate")

if button:
    question = query
    response = load_message(question=question)
    st.write(response)


