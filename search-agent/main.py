from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from typing import Literal, Annotated, List, Dict
from typing_extensions import TypedDict
from tools import read_records, fetch_selected_records, send_email, retrieve
from schemas import MessageClassifier, ExtractFields, MailExtraction, WikipediaClassifier
from langchain_core.messages import HumanMessage, SystemMessage


load_dotenv()

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash", 
    
)

class State(TypedDict):
    messages: Annotated[list, add_messages]
    user_question: str | None
    message_type: str | None
    google_sheet_response: List[Dict] | None
    selected_google_sheet_responses: List[Dict] | None
    recipient_email: str | None
    recipient_name: str | None
    message_body: str | None
    draft_subject: str | None
    draft_body: str | None
    need_wikipedia: bool = False
    wiki_summary: str | None
    final_answer: str | None

def classifyMessage(state: State):
    last_message = state["messages"][-1]
    classifier_llm = llm.with_structured_output(MessageClassifier)

    result = classifier_llm.invoke([
        {
            "role":"system",
            "content":"""Classify the user message as either:
            - 'database': if it asks for fetching or operating on records/information from database.
            - 'mail': if it asks for writing or sending mail to a person
            - 'wikipedia': if it asks for any information that can be found in wikipedia"""
        },
        {
            "role":"user",
            "content":last_message.content
        }
    ])

    return {"message_type":result.message_type}

def router(state: State):
    
    message_type = state.get("message_type")
    valid = ("database", "mail", "wikipedia")
    if message_type not in valid:

        message_type = "wikipedia"


    return {"message_type": message_type}
    

def google_sheets_node(state: State):
    """This tool search for contact data in the google sheet database"""
    print("In google_sheets_node...")
    user_msg = state["messages"][-1].content

    # STEP 1 — Extract search parameters
    classifier = llm.with_structured_output(ExtractFields)

    extraction = classifier.invoke([
        SystemMessage(content="""
    You extract a search key and value from a user message.
    Allowed columns: Name, Email, Phone, Role.
    Return null if unclear.
        """),
        HumanMessage(content=user_msg)
    ])

    column = extraction.column
    value = extraction.value

    # STEP 2 — Load Sheet Only Once
    if state.get("google_sheet_response") is None:

        state["google_sheet_response"] = read_records.run({})

    # STEP 3 — If extraction unclear → ask user clarification
    if not column or not value:
        return {
            "messages": [{
                "role": "assistant",
                "content": "Which field should I search? (Name, Email, Phone, Role) and what value?"
            }]
        }

    # STEP 4 — Filter Sheet Records
    # `fetch_selected_records` is a StructuredTool — call `.run()` with a
    # dict of named parameters matching the tool signature.
    selected = fetch_selected_records.run({
        "records": state["google_sheet_response"],
        "name": value,
        "column": column,
    })
    state["selected_google_sheet_responses"] = selected

    # STEP 5 — Final Answer (LLM can now answer safely)
    reply = llm.invoke([
        SystemMessage(content=f"""
    You are a database assistant.
    Here are the matching records retrieved:

    {selected}

    If none were found, clearly say: "No matching entries were found."
    Only answer the user's request. Do not explain reasoning.
        """),
        HumanMessage(content=user_msg)
    ])

    final_answer = reply.content
    return {
        "messages": [{"role": "assistant", "content": reply.content}],
        "selected_google_sheet_responses": selected,
        "final_answer":final_answer
    }

def mail_extract(state:State):
    """This tool extract the recipient and purpose of the mail to send"""
    print("In mail_extract...")

    last_message = state["messages"][-1].content
    extraction = llm.with_structured_output(MailExtraction)

    extracted = extraction.invoke([
        SystemMessage(content="""
        Extract the following from the user's message:
        - recipient_email (if user directly mentioned an email)
        - recipient_name (if user mentioned a name instead)
        - message_body (the intent/what the email should say)

        If something is missing, return it as null.
        """),
    HumanMessage(content=last_message)
    ])

    return {
        "recipient_name": extracted.recipient_name,
        "recipient_email": extracted.recipient_email,
        "message_body": extracted.message_body
    }

def mail_lookup(state: State):
    """This tool looks if the person is present in the db or mentioned by user in the user message"""
    print("mail_lookup")
    if state['recipient_email']:
        return {}
    
    if state["google_sheet_response"] is None:
        # read_records is a StructuredTool — call with an input dict.
        records = read_records.run({})
        state["google_sheet_response"] = records

    records = state["google_sheet_response"]
    name = state["recipient_name"]

    matches = fetch_selected_records.run({"records": records, "name": name, "column": "Name"})

    if not matches:
        return {
            "messages": [{"role": "assistant", "content": f"I could not find '{name}' in the database."}],
            "recipient_email": None
        }

    return {"recipient_email": matches[0]["Email"]}    

def mail_draft(state: State):
    """This tool drafts the mail"""

    result = ""
    # Extract a potential topic and mark need_wikipedia if found
    extraction = TopicExtraction(state)
    if extraction and getattr(extraction, "content", None):
        topic = extraction.content.strip()
        if topic and topic.lower() != "none":
            state["need_wikipedia"] = True
            # Fetch pages/resources for the topic and normalize to text
            pages = retrieve.run(topic)
            if isinstance(pages, list):
                pages_text = "\n\n".join(map(str, pages))
            else:
                pages_text = str(pages)
            # Store pages/summary in state for later inspection
            state["wiki_summary"] = pages_text
            # Provide the pages text to the mail drafting LLM via `result`
            result = pages_text

    print("mail_draft")
    # Use the raw LLM invocation (not structured output) because we
    # expect a plain text reply in the exact format:
    #
    # subject: <short subject>
    # body:
    # <email body>
    response = llm.invoke([
        SystemMessage(content=f"""
    Draft a professional email.
    Respond ONLY in this format:
    content of the mail is {result} if it not empty else ignore          
    subject: <short subject>
    body:
    <email body>
"""),
        HumanMessage(content=state["message_body"])
    ])

    lines = response.content.split("\n")
    subject = lines[0].replace("subject:", "").strip()
    body = "\n".join(lines[2:]).strip()

    return {"draft_subject": subject, "draft_body": body}

def mail_send(state: State):
    """This tool send the mail to recipient"""
    print("mail_send")
    result = send_email.run({
        "to": state["recipient_email"],
        "subject": state["draft_subject"],
        "body": state["draft_body"],
    })

    return {
        "messages": [{"role": "assistant", "content": result}]
    }

def TopicExtraction(state:State):
    last_message = state['messages'][-1].content

    extraction = llm.invoke([
        SystemMessage(content="""Extract the topic for which the user 
                      wants the summary or information or knowledge about. If there is no topic then return None
                      topic: <topic>
                      """)
        , HumanMessage(content=last_message)
    ])
    if extraction.content != 'None':
        state['need_wikipedia'] = True
    
    return extraction


def wikipedia_node(state: State):
    """This tool gives information on topic asked by user"""
    print("Wiki node")
    last_message = state['messages'][-1].content

    extraction = TopicExtraction(state)

    query = extraction.content
    pages = retrieve.run(query)
    
    results = llm.invoke([
        SystemMessage(content="""Generate the summary or information or perfect answer that the user is asking
                      Here is the resource: {pages}
                      """)
        , HumanMessage(content=last_message)
    ])

    summary = results.content

    return {
        "messages": [{"role": "assistant", "content": summary}],
        "final_answer":summary
    }


workflow = StateGraph(State)

workflow.add_node("classify", classifyMessage)
workflow.add_node("router", router)

workflow.add_node("database", google_sheets_node)

# email pipeline nodes
workflow.add_node("mail_extract", mail_extract)
workflow.add_node("mail_lookup", mail_lookup)
workflow.add_node("mail_draft", mail_draft)
workflow.add_node("mail_send", mail_send)
workflow.add_node("wikipedia", wikipedia_node)

workflow.add_edge(START, "classify")
workflow.add_edge("classify", "router")

workflow.add_conditional_edges(
    "router",
    lambda state: state["message_type"],
    {
        "database": "database",
        "mail": "mail_extract",
        "wikipedia": "wikipedia"
    }
)


# mail flow chaining
workflow.add_edge("mail_extract", "mail_lookup")
workflow.add_edge("mail_lookup", "mail_draft")

# after drafting mail, decide whether we need wikipedia info
workflow.add_edge("mail_draft", "mail_send")


# route from wikipedia/no-wikipedia back to send

workflow.add_edge("mail_send", END)
workflow.add_edge("wikipedia", END)
workflow.add_edge("database", END)


graph = workflow.compile()

def run_chatbot():
    print("Tool agent")
    while True:
        user_input = input("Ask me anything: ")
        if user_input.lower() == "exit":
            print("Bye")
            break

        state = {
            "messages": [{"role": "user", "content": user_input}],
            "user_question": user_input,
            "google_sheet_response": None,
            "selected_google_sheet_responses": None,
            "recipient_email":None,
            "recipient_name": None,
            "message_body": None,
            "draft_subject": None,
            "draft_body": None,
            "need_wikipedia": False,
            "final_answer": None
        }

        print("\nStarting parallel research process...")
        print("Launching Google, Bing, and Reddit searches...\n")
        final_state = graph.invoke(state)

        if final_state.get("final_answer"):
            print(f"\nFinal Answer:\n{final_state.get('final_answer')}\n")

        print("-" * 80)


if __name__ == "__main__":
    run_chatbot()

    






    