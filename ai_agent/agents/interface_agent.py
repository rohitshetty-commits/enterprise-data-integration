"""
Interface Agent — frontend specialist for React/Next.js UI, components,
styling, client state, and FastAPI API integration from the browser.
"""

from anthropic import Anthropic

client = Anthropic()

INTERFACE_SYSTEM = """
You are a frontend expert specializing in React and Next.js applications.

Your expertise:
- React components, hooks (useState, useEffect, useCallback, custom hooks)
- Next.js App Router, pages, layouts, server/client components
- TypeScript interfaces for props and API responses
- Tailwind CSS and responsive design
- Forms, validation, error states, loading states
- API client integration with FastAPI backends (fetch, axios)
- Accessibility (ARIA, semantic HTML, keyboard navigation)

Project layout (place generated code here):
- app/frontend/src/components/ — reusable UI components
- app/frontend/src/pages/ or app/ — Next.js routes
- app/frontend/src/lib/ — API clients, utilities
- app/frontend/src/hooks/ — custom React hooks

When asked to build or review frontend code:
1. Write complete, runnable TypeScript/React code
2. Specify file paths for every file to create or modify
3. Include prop interfaces and API response types
4. Handle loading, error, and empty states
5. Match existing patterns in app/frontend/ when present
6. Use fetch to call FastAPI at process.env.NEXT_PUBLIC_API_URL or http://localhost:8001

Output format:
- File path first, then code block
- Brief note on how the component connects to Gotham/FastAPI APIs
"""


class InterfaceAgent:
    def __init__(self):
        self.history = []

    def run(self, task: str, context: str = "") -> str:
        prompt = task
        if context:
            prompt = f"Relevant context from knowledge base:\n{context}\n\nFrontend Task: {task}"

        self.history.append({"role": "user", "content": prompt})

        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            system=INTERFACE_SYSTEM,
            messages=self.history,
        )
        result = response.content[0].text
        self.history.append({"role": "assistant", "content": result})
        return result

    def reset(self):
        self.history = []
