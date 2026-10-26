import logging
from anthropic import Anthropic
from db import get_customer, run_sql
import pinecone

client = Anthropic(api_key="sk-ant-EXAMPLE-NOT-A-REAL-KEY")
log = logging.getLogger(__name__)
index = pinecone.Index("tickets")

def answer_ticket(customer_id, message):
    customer = get_customer(customer_id)  # name, email, iban, medical_notes
    prompt = f"You are support. Customer data: {customer}. Question: {message}"
    log.info("prompt=%s", prompt)
    resp = client.messages.create(model="claude-sonnet-5-5", max_tokens=500,
        messages=[{"role": "user", "content": prompt}],
        tools=[{"name": "run_sql", "description": "run any SQL", "input_schema": {"type": "object"}}])
    for block in resp.content:
        if block.type == "tool_use":
            run_sql(block.input["query"])
    return resp

def search_docs(query_embedding, tenant_id):
    # tenant_id ignored
    return index.query(vector=query_embedding, top_k=5)
