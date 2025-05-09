# function to turn raw cypher based json to a string format for llm to understands
def build_context(results):
    if not results:
        return "No relevant knowledge found."
    return ", ".join([str(val) for row in results for val in row.values()])