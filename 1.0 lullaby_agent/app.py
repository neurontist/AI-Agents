# Import necessary libraries
import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import LLMChain, SequentialChain
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv, find_dotenv
import os

# Load environment variables from .env file
_ = load_dotenv(find_dotenv())

# Retrieve Google API key
GOOGLE_API_KEY = os.environ['GEMINI_API_KEY']

# Define the LLM model to use
llm_model = "gemini-1.5-pro"

# Initialize the LLM (Language Learning Model) instance
llm = ChatGoogleGenerativeAI(model=llm_model, google_api_key=GOOGLE_API_KEY)

# Function to generate and translate a lullaby
def generate_lullaby(location, name, language):
    # Prompt template to create a simple English lullaby
    template = """ 
        As a children's book writer, please come up with a simple and short (90 words)
        lullaby based on the location
        {location}
        and the main character {name}
        
        STORY:
    """
    prompt = PromptTemplate(
        template=template,
        input_variables=["location", "name"]
    )

    # Chain to generate the story in English
    eng_chain = LLMChain(llm=llm, prompt=prompt, output_key='story')

    # Prompt template to translate the generated story into a target language
    template_update = """
    Translate the {story} into {language}. Make sure 
    the language is simple and fun. Just give the story in the specified language and nothing else.

    TRANSLATION:
    """
    prompt_translate = PromptTemplate(
        template=template_update,
        input_variables=['story', 'language']
    )

    # Chain to handle the translation task
    translate_chain = LLMChain(llm=llm, prompt=prompt_translate, output_key="translated_story")

    # Sequentially execute the story generation followed by translation
    overall_chain = SequentialChain(
        chains=[eng_chain, translate_chain],
        input_variables=["location", "name", "language"],
        output_variables=["story", "translated_story"]
    )

    # Execute the chain with provided inputs
    response = overall_chain({"location": location, "name": name, "language": language})

    return response

# --- Streamlit UI Section ---

# Set up Streamlit app title and header
st.title('Let AI Write and Translate a Lullaby for You 📖')
st.header('Get Started now...')

# Function to reset input fields
def reset_inputs():
    values = ['place', 'name', 'lang']
    for key in range(len(values)):
        st.session_state[values[key]] = ""

# Input fields for user to enter story details
story_set = st.text_input('Where is the story set?', placeholder='Place', key='place')
main_character = st.text_input('What\'s the main character name?', placeholder='Name', key='name')
translation_lang = st.text_input('Translate the story into...', placeholder='Language', key='lang')

# Buttons for submitting and resetting
submit, reset = st.columns([0.1, 0.7])
with submit:
    submit = st.button('Submit')
with reset:
    st.button('Reset', on_click=reset_inputs)

# Display output when all inputs are filled and submit is clicked
if story_set and main_character and translation_lang:
    if submit:
        with st.spinner(text='Generating Lullaby...'):
            generate = generate_lullaby(location=story_set, name=main_character, language=translation_lang)
        with st.expander("English Version"):
            st.write(generate['story'])
        with st.expander(f"{translation_lang} version"):
            st.write(generate['translated_story'])
        st.success("Lullaby Generated!")
else:
    if submit:
        st.warning("Please give input...")

