"""LLM backends for NeuroXpert-RAG.

We keep this as a thin layer so the rest of the codebase:
  - does not depend on a specific model provider
  - can be swapped between local backends (Ollama, llama.cpp) or APIs

Current backend: Ollama (local HTTP server).
"""
