from neo4j import GraphDatabase
from groq import Groq  # official sdk for gtoq
import os

class GraphRAG:
    def __init__(self, neo4j_url, neo4j_username, neo4j_password):
        # initialize neo4j driver
        self.driver = GraphDatabase.driver(neo4j_url, auth=(neo4j_username, neo4j_password))

        # initialize groq client
        self.llm = Groq(api_key = os.getenv("GROQ_API_KEY"))

        # graph schema description
        self.schema_description = '''Schema:
        (:System)-[:HAS_COMPONENT]->(:Component)
        (:Component)-[:HAS_PROCEDURE]->(:Procedure)
        (:Procedure)-[:HAS_STEP]->(:Step)
        (:Procedure)-[:HAS_WARNING]->(:Warning)
        (:System)-[:AFFECTED_BY]->(:FailureMode)
        (:FailureMode)-[:MITIGATED_BY]->(:Procedure)

        Properties:
        System: name, description
        Component: name, description
        Procedure: title, type (e.g., emergency, normal), applicableSystem
        Step: number, instruction
        Warning: message
        FailureMode: name, description'''

    def close(self):
        self.driver.close()

    def run_cypher_query(self, cypher_query):
        with self.driver.session() as session:
            result = session.run(cypher_query)
            return [dict(record) for record in result]

    def convert_question_to_cypher(self, question):
        prompt = f'''You are a Cypher expert for an aircraft operations manual knowledge graph.

        Schema:
        {self.schema_description}

        Convert the following natural language question into a valid Cypher query.
        Do NOT explain the query. Only output the Cypher query.

        Example:
        Question: What are the emergency procedures for an engine fire?
        Cypher: MATCH (p:Procedure) WHERE p.type = 'emergency' AND p.title CONTAINS 'engine fire' RETURN p.title, p.type

        Now convert this question:
        {question}'''

        try:
            response = self.llm.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content.strip() # this was the problem causing part for responses

        except Exception as e:
            print("Error generating Cypher:", e)
            return None