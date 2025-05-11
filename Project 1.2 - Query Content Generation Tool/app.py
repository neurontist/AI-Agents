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

    if age_grp == 'kid':
        examples = [
    {"query": "Why can't I ride a rainbow?", "answer": "Because rainbows are made of light and giggles, not roads! 🌈✨"},
    {"query": "Do cats know I'm their boss?", "answer": "Cats think *they* are your boss, silly! 🐱👑"},
    {"query": "Can I marry my teddy bear?", "answer": "Of course! Teddy already said yes in bear language! 🧸💖"},
    {"query": "If I eat a watermelon seed, will a tree grow in my tummy?", "answer": "Nope! Your tummy is too cozy for trees, only giggles grow there! 🍉😂"},
    {"query": "Why can't I have a pet unicorn?", "answer": "Unicorns are shy and hide in cotton candy clouds! 🦄☁️"},
    {"query": "Can I fly if I jump really high?", "answer": "Almost! You just need fairy wings and a sprinkle of pixie dust! 🧚‍♀️✨"},
    {"query": "Do stars go to sleep?", "answer": "Yes, they close one little sparkle eye at a time! 🌟😴"},
    {"query": "Is the moon made of cheese?", "answer": "Only in mouse dreams! 🧀🌕"},
    {"query": "Can I teach my goldfish to dance?", "answer": "Of course! Just play tiny fishy music! 🎶🐠"},
    {"query": "Will my doll come alive at night?", "answer": "Maybe! But only to tidy up your toys and sneak back before morning! 🎀🤫"}
    ]
    elif age_grp == 'adult':
        examples = [
    {"query": "Why do Mondays feel longer than the rest of the week?", "answer": "Because time slows down when you're not emotionally prepared. ☕😅"},
    {"query": "Can coffee solve all my problems?", "answer": "Not all, but it can delay them until you're caffeinated enough to care. ☕✨"},
    {"query": "Why do I remember embarrassing moments from 10 years ago?", "answer": "Because your brain has a dedicated cringe storage unit. 🧠📦"},
    {"query": "Is it too late to switch careers at 30?", "answer": "Not at all. Some of the best plot twists happen in the middle of the book. 📖🌟"},
    {"query": "Can I survive adulthood without Googling everything?", "answer": "Sure, but you'd have to actually read the manual. 😬📚"},
    {"query": "Why do I always forget my passwords?", "answer": "Because your brain replaced them with song lyrics from 2007. 🎶🔑"},
    {"query": "Is adulting a scam?", "answer": "Yes. The only reward is being allowed to buy your own cereal. 🛒🥣"},
    {"query": "Why do I talk to myself when no one’s around?", "answer": "Because you give great advice and even better sarcasm. 😎🗣️"},
    {"query": "Can plants feel neglected when I forget to water them?", "answer": "Yes, and they’ve been gossiping about it with the succulents. 🌱😔"},
    {"query": "Why does time go faster the older I get?", "answer": "Because you've upgraded to life’s premium speed tier. ⏩📆"}
    ]
    else:
        examples = [
    {"query": "Why do my joints predict the weather better than the forecast?", "answer": "Because experience is the best meteorologist. 🌦️🦴"},
    {"query": "Can I still learn something new at 70?", "answer": "Absolutely. The brain loves surprises, even in its golden years. 🎓🧠"},
    {"query": "Why do memories feel more vivid than last week’s news?", "answer": "Because memories are like old friends — always welcome. 🕰️❤️"},
    {"query": "Is it okay to nap twice a day?", "answer": "Not only okay — it's an art form perfected over decades. 😴🎨"},
    {"query": "Do grandkids keep you young?", "answer": "Yes, and slightly exhausted, but mostly young. 👵💕👶"},
    {"query": "Why does music from my youth sound better?", "answer": "Because it played when your heart was still dancing. 🎶💃"},
    {"query": "Can I still fall in love again?", "answer": "Love doesn’t retire. It just gets better at telling stories. 💌🕊️"},
    {"query": "Why do I talk to birds in the garden?", "answer": "Because they've always listened better than most people. 🐦🌼"},
    {"query": "Should I start painting now?", "answer": "Yes — the brush doesn’t care when you pick it up, only that you do. 🎨🖌️"},
    {"query": "Why does silence feel so comforting now?", "answer": "Because you've earned the peace that comes with it. 🤍🪷"}
    ]

    if option =='Create a tweet':
        option = 'tweet'
    elif option == 'Write a sales copy':
        option = 'sales copy'
    else:
        option = 'product description'
    prefix = """
        Assume you are a {age_grp}. Create a {option}, following the below instructions.
        #INSTRUCTIONS
        - the {option} be should of {length} words strictly
"""
    suffix = """
        query: {query}
        Response:
"""
    
    examples_prompt = """
    Question: {query},
    Answer: {answer}
    """

    template = PromptTemplate(
        template=examples_prompt,
        input_variables=["query","answer"]
    )

    few_shot_prompt_template = FewShotPromptTemplate(
    examples=examples,
    example_prompt=template,
    prefix=prefix,
    suffix=suffix,
    input_variables=["age_grp","option","length"],
    example_separator="\n\n"
)

    format_prompt = few_shot_prompt_template.format(query=query,age_grp=age_grp,length=length,option=option)
    human_message = HumanMessage(content=format_prompt)
    response = llm([human_message])
    return response.content

    

if 'set' not in st.session_state:
    st.session_state.set = [
        SystemMessage("You are a helpful assistant!")
    ]

st.title("Hey, Let's get your content generated with humoristic sense")

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