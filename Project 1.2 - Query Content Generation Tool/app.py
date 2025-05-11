from dotenv import load_dotenv,find_dotenv
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate,FewShotPromptTemplate
from langchain.schema import SystemMessage,HumanMessage
import streamlit as st

_ = load_dotenv(find_dotenv())

GOOGLE_API_KEY = os.environ['GEMINI_API_KEY']

model = "gemini-1.5-flash"

llm = ChatGoogleGenerativeAI(model=model,api_key=GOOGLE_API_KEY)

def create_answer(length,age_grp,query,option):
    # prompt
    if option =='Create a tweet':
        option = 'tweet'
    elif option == 'Write a sales copy':
        option = 'sales copy'
    else:
        option = 'product description'
    prompt = """
Assume you are a {age_grp}. Create a {option}, following the below instructions.
#INSTRUCTIONS
- the {option} be should of {length} words strictly

query: {query}
Response:
"""
    # prompttemplate
    prompt_template = PromptTemplate.from_template(
        template=prompt
    )
    format_prompt = prompt_template.format(length=length,age_grp=age_grp,query=query,option=option)

    response = llm([HumanMessage(content=format_prompt)])
    return response.content
    

if 'set' not in st.session_state:
    st.session_state.set = [
        SystemMessage("You are a helpful assistant!")
    ]

st.title("Hey, How can I help you?")

user_text = st.text_area("Enter text")
create = st.selectbox("Please select the action to be performed",['Create a tweet','Write a sales copy','Write a product description'])
age_grp = st.selectbox("For which age group?",['kid','adult','senior citizen'])
num_of_words = st.slider('Please enter the number of words',min_value=1,max_value=200)

button = st.button("Generate")

if st.session_state:
    if button:
        st.write(f"Your text: {user_text}")
        st.write(f"Your selected type: {create}")
        st.write(f"Your selected age group: {age_grp}")
        st.write(f"Your selected words: {num_of_words}")
        response = create_answer(num_of_words,age_grp,user_text,create)
        st.write(response)