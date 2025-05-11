from langchain_google_genai import ChatGoogleGenerativeAI,GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.prompts import PromptTemplate
from langchain.docstore.document import Document
from dotenv import find_dotenv,load_dotenv
import os
import streamlit as st
import ast 

load_dotenv(find_dotenv())

GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY")

llm_model = "gemini-1.5-pro"
llm = ChatGoogleGenerativeAI(model=llm_model,temperature=0.7,google_api_key=GOOGLE_API_KEY)

embeddings = GoogleGenerativeAIEmbeddings(
        model="models/embedding-001",
        google_api_key=GOOGLE_API_KEY
    )

# llm generate similar words
def generate_similar_words(word):
    template = """
You are a dictionary assistant. Given a single word, return exactly 10 random but meaningfully similar words.

### Word: "{word}"

### Requirements:
- All words must be single words (no phrases).
- Words should be semantically related or commonly associated with the input word.
- Return the words strictly in Python list format like: ["word1", "word2", ..., "word10"]
- Do not include any explanation or extra text.

### Output:
"""

    prompt_template = PromptTemplate(template=template,
                                     input_variables=["word"],
                                     
                                    )
    format_prompt = prompt_template.format(word=word)
    response = llm.invoke(format_prompt)

    word_list = ast.literal_eval(response.content)

    return word_list

# embedd the query as well as the llm response 
def embed_n_store(word):
    word_list = generate_similar_words(word)
    document = [Document(page_content=single_word) for single_word in word_list]
    db = FAISS.from_documents(documents=document,embedding=embeddings)
    return db


st.title("Hey, Ask me something & I will give out similar things")
user_input = st.text_input("Enter a word")
button = st.button("Find Similar Things")

if 'session' not in st.session_state:
     st.session_state.session = True

if st.session_state.session:
    if button:
            with st.spinner("Getting the words"):
                db = embed_n_store(user_input)
                results = db.similarity_search(user_input, k=3)
                st.header("Top Matches")
                for r in results:
                    st.write(r.page_content)

else:
    st.write("Enter a word")


