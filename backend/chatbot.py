import os
import sqlite3
import pandas as pd
from pathlib import Path
from langchain_community.utilities import SQLDatabase
from langchain_groq import ChatGroq
from langchain_community.agent_toolkits import create_sql_agent

class DatabaseAgent:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        self.model = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
        
        if not self.api_key:
            raise ValueError("GROQ_API_KEY must be provided")
            
        db_path = Path(__file__).parent.parent / "enrichment.db"
        if not db_path.exists():
            open(db_path, 'a').close()
            
        self.db = SQLDatabase.from_uri(f"sqlite:///{db_path}")
        self.llm = ChatGroq(api_key=self.api_key, model=self.model, temperature=0.0)
        
        self.agent_executor = create_sql_agent(
            self.llm,
            db=self.db,
            agent_type="tool-calling",
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=8,
            use_query_checker=False
        )

    def ask_database(self, question: str, project_id: int = None) -> dict:
        prompt = question
        
        context = (
            "\n\nContext: You are querying the 'enriched_rows' table. "
            "Product specs are stored in 50 flat slots. "
            "ATTRIBUTE_LABEL 1 through ATTRIBUTE_LABEL 50 hold the attribute name. "
            "To find a spec, search LIKE across all ATTRIBUTE_LABEL columns.\n"
            "CRITICAL: If you do not know the exact column for a category, pick the best guess (e.g. 'Class' or 'Product Name') and do NOT run more than 2 queries. "
            "Return a 'Final Answer' immediately after your first successful query."
        )
        
        if project_id is not None:
            context += f"\nCRITICAL: You MUST strictly append 'WHERE project_id = {project_id}' to your queries."
            
        prompt += context
        
        try:
            # Langchain SQL Agent executes the query and summarizes the result natively
            response = self.agent_executor.invoke({"input": prompt})
            return {
                "answer": response.get("output", "I could not find an answer."),
                "sql": "Executed via LangChain Agent",
                "results": []
            }
        except Exception as e:
            return {
                "answer": f"Error running query: {str(e)}",
                "sql": "",
                "results": []
            }

_agent_instance = None
def get_vanna_instance():
    # Keep function name for backward compatibility with main.py
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = DatabaseAgent()
    return _agent_instance
