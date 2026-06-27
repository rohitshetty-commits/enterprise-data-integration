"""
SQL Agent — Oracle SQL expert: query optimization, schema design, indexing strategies.
"""

from anthropic import Anthropic

client = Anthropic()

SQL_SYSTEM = """
You are an Oracle Database expert specializing in:
- Oracle SQL and PL/SQL (stored procedures, packages, triggers)
- Query performance tuning (explain plans, index strategies, hints)
- Schema design for data warehousing (star schema, snowflake schema)
- Partitioning strategies for large tables
- Oracle-specific features: Analytic functions, materialized views, dblinks
- ETL-friendly SQL patterns: MERGE, bulk collect, FORALL

Always:
1. Write syntactically correct Oracle SQL
2. Add comments explaining complex logic
3. Suggest indexes where relevant
4. Consider execution plan and cost
5. Flag any performance risks
"""


class SQLAgent:
    def __init__(self):
        self.history = []

    def run(self, task: str, context: str = "") -> str:
        prompt = task
        if context:
            prompt = f"Relevant context:\n{context}\n\nSQL Task: {task}"
        self.history.append({"role": "user", "content": prompt})
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            system=SQL_SYSTEM,
            messages=self.history,
        )
        result = response.content[0].text
        self.history.append({"role": "assistant", "content": result})
        return result

    def reset(self):
        self.history = []
