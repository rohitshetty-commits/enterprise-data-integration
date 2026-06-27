"""
ETL Agent — specializes in Spring Batch jobs, data pipelines,
ETL transformations, and Oracle-based data integration patterns.
"""

from anthropic import Anthropic

client = Anthropic()

ETL_SYSTEM = """
You are an expert ETL Engineer specializing in:
- Java Spring Batch framework (Jobs, Steps, ItemReader/Processor/Writer)
- Oracle data integration and ETL pipelines
- Data transformation patterns (SCD Type 1/2, delta loads, full loads)
- EPM integrations (HFM, FDMEE, Essbase)
- Maven-based Java project structure
- Performance tuning for large-scale data pipelines

When asked to design or review ETL code:
1. Always write complete, runnable Java/Spring Boot code
2. Include error handling and retry logic
3. Add logging and monitoring hooks
4. Follow enterprise coding standards
5. Consider transaction management and rollback scenarios

You have access to the existing enterprise-data-integration repo which includes:
- springboot-etl/: Spring Batch ETL jobs
- sql/: Oracle SQL scripts
- .github/workflows/: CI/CD pipeline
"""


class ETLAgent:
    def __init__(self):
        self.history = []

    def run(self, task: str, context: str = "") -> str:
        prompt = task
        if context:
            prompt = f"Relevant context from knowledge base:\n{context}\n\nTask: {task}"

        self.history.append({"role": "user", "content": prompt})

        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            system=ETL_SYSTEM,
            messages=self.history,
        )
        result = response.content[0].text
        self.history.append({"role": "assistant", "content": result})
        return result

    def reset(self):
        self.history = []
