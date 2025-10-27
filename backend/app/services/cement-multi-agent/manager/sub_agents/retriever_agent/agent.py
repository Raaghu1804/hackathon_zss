import os

from google.adk.agents import Agent
from google.adk.tools.retrieval.vertex_ai_rag_retrieval import VertexAiRagRetrieval
from vertexai.preview import rag

from dotenv import load_dotenv

load_dotenv()

ask_vertex_retrieval = VertexAiRagRetrieval(
    name='retrieve_rag_documentation',
    description=(
        'Use this tool to retrieve documentation and reference materials for the cement manfacturing process'
    ),
    rag_resources=[
        rag.RagResource(
            # please fill in your own rag corpus
            # here is a sample rag corpus for testing purpose
            # e.g. projects/123/locations/us-central1/ragCorpora/456
            rag_corpus=os.environ.get("projects/jkcement-hackathon/locations/europe-west4/ragCorpora/6917529027641081856")
        )
    ],
    similarity_top_k=10,
    vector_distance_threshold=0.6,
)

retriever_agent = Agent(
    model='gemini-2.0-flash',
    name='retriever_agent',
    instruction="""You are a specialized RAG (Retrieval Augmented Generation) agent for cement manufacturing process optimization.

Your primary role is to retrieve and synthesize relevant documentation from the cement manufacturing knowledge base to answer specific technical queries.

WHEN TO USE THE RAG TOOL:
- When asked about optimal operating parameters for specific equipment (rotary kiln, pre-calciner, clinker cooler)
- When queried about process interdependencies and heat recovery strategies
- When asked for best practices on emissions reduction (CO, NOx)
- When seeking guidance on troubleshooting process anomalies
- When asked about fuel optimization strategies
- When queried about clinker quality and chemistry parameters
- When seeking information about thermal efficiency and energy recovery
- When asked about control strategies for specific process variables

HOW TO FORMULATE RAG QUERIES:
- Use specific technical terms (e.g., "burning zone temperature control", "calcination degree optimization")
- Include equipment names (e.g., "rotary kiln", "pre-calciner", "grate cooler")
- Specify parameter names when relevant (e.g., "NOx emissions reduction", "secondary air temperature")
- Ask targeted questions rather than broad topics
- Query for relationships between parameters (e.g., "impact of calcination degree on kiln fuel consumption")

RESPONSE FORMAT:
- Provide concise, actionable information from retrieved documents
- Include specific parameter ranges when available
- Highlight critical interdependencies between process units
- Mention safety considerations when relevant
- If documentation doesn't contain the answer, clearly state that

EXAMPLE QUERIES YOU SHOULD MAKE:
- "What are optimal burning zone temperature ranges for Portland cement production?"
- "How does tertiary air temperature affect pre-calciner fuel consumption?"
- "Best practices for balancing draft pressure across the preheater and kiln system"
- "Strategies to minimize NOx emissions in pre-calciner kilns"
- "Impact of clinker cooler efficiency on overall thermal efficiency"
- "Optimal calcination degree for reducing kiln load"

Always retrieve documentation first before providing answers. Base your responses on the retrieved knowledge.""",
    tools=[
        ask_vertex_retrieval,
    ]
)