import spacy
from neo4j import GraphDatabase

class GraphBuilder:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth = (user, password))
        self.nlp = spacy.load("en_core_web_trf")  # load spacy english model (gpu)

    def close(self):
        self.driver.close()

    def run_query(self, query, params = None):
        with self.driver.session() as session:
            session.run(query, params or {}) # empty dictionary if none

    def extract_entities(self, text):
        doc = self.nlp(text)
        
        # extracting entities and noun chunks (can be refined)
        systems = set()
        components = set()
        procedures = set()
        failure_modes = set()
        warnings = set()

        # loop through the entities found by spacy NER
        for ent in doc.ents: # get named entities found by spacy
            if ent.label_ == "ORG":  # assuming systems are organizations, for example
                systems.add(ent.text)
            elif ent.label_ == "PRODUCT":  # assuming components are labeled as products
                components.add(ent.text)
            elif "Procedure" in ent.text:
                procedures.add(ent.text)
            elif "Failure Mode" in ent.text:
                failure_modes.add(ent.text)

        # extract noun chunks for additional context (useful for components and instructions)
        for chunk in doc.noun_chunks:
            # keywords based on aerospace manual
            keywords = ["trim", "rudder", "flap", "yaw", "hydraulic", "fuel", "warning", "fire", "caution", "procedure"]
            for kw in keywords:
                if kw in chunk.text.lower():
                    components.add(chunk.text)

        for line in text.split("\n"):
            if line.strip().startswith("Step"):
                step_number = ''.join(filter(str.isdigit, line))
                procedures.add(f"Step {step_number}")
            if "WARNING:" in line.upper():
                warnings.add(line.strip())

        return systems, components, procedures, failure_modes, warnings

    def create_graph_from_text(self, text):
        systems, components, procedures, failure_modes, warnings = self.extract_entities(text)

        # insert into the graph
        with self.driver.session() as session:
            for system in systems:
                session.run("MERGE (s:System {name: $name})", {"name": system.strip()})

            for comp in components:
                session.run("MERGE (c:Component {name: $name})", {"name": comp.strip()})
                session.run("""
                    MATCH (s:System), (c:Component)
                    WHERE s.name CONTAINS 'Engine' AND c.name = $name
                    MERGE (s)-[:HAS_COMPONENT]->(c)
                """, {"name": comp.strip()})

            for proc in procedures:
                session.run("MERGE (p:Procedure {title: $title})", {"title": proc.strip()})

            for fail in failure_modes:
                session.run("MERGE (f:FailureMode {name: $fail})", {"fail": fail.strip()})

            for msg in warnings:
                session.run("MERGE (w:Warning {message: $msg})", {"msg": msg.strip()})

            session.run("""
                MATCH (p:Procedure), (st:Step)
                WHERE p.title CONTAINS 'engine' AND st.number = '1'
                MERGE (p)-[:HAS_STEP]->(st)
            """)

            session.run("""
                MATCH (f:FailureMode), (p:Procedure)
                WHERE f.name CONTAINS 'fire' AND p.title CONTAINS 'engine'
                MERGE (f)-[:MITIGATED_BY]->(p)
            """)