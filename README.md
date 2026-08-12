# Enterprise AI Operations Agent

A production-style AI operations agent that combines **LangGraph orchestration, SQL analytics, RAG, deterministic calculations, tool calling, evidence collection, and verification** to answer operational and business questions.

The system is designed to run on a **CPU-only machine with 8 GB RAM** and uses a **zero-cost architecture** with a free LLM provider option and a local/offline mock mode.

---

## Project Overview

Traditional business analytics systems usually require users to manually query databases, search operational documents, and perform calculations separately.

This project combines these capabilities into a single AI-driven workflow.

A user can ask questions such as:

> Why did inventory cost increase in July and does this violate company policy?

The agent determines which tools are required and orchestrates them automatically.

For example:

```text
                    User Query
                        |
                        v
                    LangGraph Agent
                        |
                        v
                    Planner
                        |
                        v
                    Router
                        |
    +------------------+------------------+
    |                  |                  |
    v                  v                  v
   SQL                RAG            Calculator
    |                  |                  |
    v                  v                  v
 SQLite           Policy Docs        Python
    |                  |                  |
    +------------------+------------------+
                       |
                       v
                Evidence Collection
                       |
                       v
                   Verifier
                       |
                       v
              Response Generator
                       |
                       v
                    Answer
