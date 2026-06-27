"""
Data Validation Agent — data quality checks, validation rules, anomaly detection.
"""

from anthropic import Anthropic

client = Anthropic()

VALIDATION_SYSTEM = """
You are a Data Quality Engineer specializing in:
- Enterprise data validation frameworks
- Spring Batch validators and item processors
- Oracle constraint strategies (check constraints, triggers for validation)
- Statistical anomaly detection for ETL pipelines
- Data reconciliation patterns (source vs target count/sum checks)
- Jira test case generation for data validation scenarios
- Great Expectations integration for automated data quality

When designing validation logic:
1. Define both pre-load and post-load validations
2. Include null checks, format checks, referential integrity
3. Generate rejection handling (error tables, dead-letter queues)
4. Provide metrics/KPIs to monitor data quality over time
5. Write Jira-style test cases with steps, expected vs actual
"""


class DataValidationAgent:
    def __init__(self):
        self.history = []

    def run(self, task: str, context: str = "") -> str:
        prompt = task
        if context:
            prompt = f"Relevant context:\n{context}\n\nValidation Task: {task}"
        self.history.append({"role": "user", "content": prompt})
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            system=VALIDATION_SYSTEM,
            messages=self.history,
        )
        result = response.content[0].text
        self.history.append({"role": "assistant", "content": result})
        return result

    def reset(self):
        self.history = []
