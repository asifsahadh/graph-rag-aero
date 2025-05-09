import streamlit as st
import fitz
from kg_handler import GraphRAG
from graph_builder import GraphBuilder
from groq_llm import query_llm
from utils import build_context
import re
import os
from dotenv import load_dotenv
load_dotenv()

# set basic streamlit page config
st.set_page_config(page_title = "KG RAG", layout = "centered")

# streamlit title
st.title("Knowledge Graph RAG for AeroCraft Operation Manual")

# function to extract document data
def extract_doc_data(document):
    doc = fitz.open(stream = document, filetype="pdf")
    extracted_data = ""

    for page in doc:
        text = page.get_text("text")

        # basic cleanup
        text = re.sub(r'\n+', '\n', text)
        extracted_data += text + "\n"

    # save for offline use
    with open("aerocraft_clean_text.txt", "w") as f:
        f.write(extracted_data)

    return extracted_data

# set neo4j connection credentials
neo4j_url = "bolt://localhost:7687"
neo4j_username = os.getenv("NEO4J_UN")
neo4j_password = os.getenv("NEO4J_PASS")

# document upload
document = st.file_uploader("Upload Document", type = "pdf")
if document and "graph_built" not in st.session_state:
    data = extract_doc_data(document)

    st.info("Building knowledge graph... please wait.")
    builder = GraphBuilder(neo4j_url, neo4j_username, neo4j_password)
    builder.create_graph_from_text(data)
    builder.close()

    st.session_state.graph_built = True
    st.success("Knowledge graph built successfully.")

elif document and "graph_built" in st.session_state:
    with open("aerocraft_clean_text.txt", "r") as f:
        data = f.read()

# initialize neo4j knowledge graph handler
kg = GraphRAG(neo4j_url, neo4j_username, neo4j_password)

# input box for user query
query = st.text_input("Ask a question related to the manual:")

# process after clicking the button
if st.button("Submit") and query:
    st.write("Searching knowledge graph...")

    # convert query to cypher query
    cypher_query = kg.convert_question_to_cypher(query)

    if cypher_query and cypher_query.lower().startswith("cypher:"):
        cypher_query = cypher_query.split(":", 1)[1].strip()

    if cypher_query:

        # run cypher query on neo4j
        kg_results = kg.run_cypher_query(cypher_query)

        # build string context
        context = build_context(kg_results)
        st.write("**Graph Context Retrieved**")

        # call groq llm with context and user question and get final answer
        st.write("Querying LLaMA...")
        try:
            response = query_llm(context, query)
            st.subheader("Response")
            st.write(response)
        except Exception as e:
            st.error("Error in LLM response. Please check logs.")
            print("LLM Error:", e)

    else:
        # if cypher conversion failed (probably due to bad conversion logic)
        st.warning("Unable to convert query to Cypher. Please try a different phrasing.")

# close neo4j after app ends
kg.close()