## Knowledge Graph RAG for AeroCraft Operation Manual  
#### Description of Primary Elements from Code, including Limitations of Model.

1. app.py - 'extract_doc_data' function  
The initial step is uploading of the operations manual. Next, the PyMuPDF (fitz) library extracts the text from the document. This is stored inside a variable. Multiple newlines are converted into a single newline using regex.

2. graph_builder.py - 'extract_entities' function  
Next, the graph building starts. Some entities that are assumed about the operations manual are hardcoded. These include systems, procedures, components, etc. The code attempts to fill these hardcoded categories through multiple methods. One is using spaCy's NER, which maps categories like "ORG" to entities like "systems". Two, simple string matching for terms like "Procedure" and three, aviation keyword detection, which was extracted by passing the manual to an LLM. The keyword "warning" which is quite common in the manual, is identified through pattern matching of uppercase "WARNING:" labels. This was also based on assumption.

3. graph_builder.py - 'create_graph_from_text' function  
Once the entities are identified, the relationships need to be established. The relationship creation is extremely limited and uses very few hardcoded rules. The only patterns used to establish relationships are simple string matching (looking for "Engine" in system names to connect components, matching step numbers to procedures containing "engine", and connecting failure modes containing "fire" to procedures containing "engine"). This can obviously, and has to be expanded for better capturing od relationships. Finally, the built graph is transferred to the DBMS. 

4. functions from 'kg_handler.py' & 'utils.py'  
Now, the user can ask questions based on the manual. The question is converted to cypher query using a function that prompts an LLM to do so. Once extracted, this query is run over the created graph in neo4j. The extracted entities and relationships, if available, are saved into a variable for context.

5. query_llm.py  
Finally, an LLM is prompted with both this context generated from the graph, and the original user query.
