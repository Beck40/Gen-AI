# Generative AI Engineering Portfolio

## Overview

This repository documents my engineering journey in Applied Generative AI.
It contains production-ready agents, RAG pipelines, and data analysis tools built with modern LLM frameworks (LangChain) and open-source models (Llama 3).

My focus is on Deterministic AI: building agents that don't just chat, but reliably execute complex business logic, query databases, and handle structured data.

## Project List

**[Technical Guide](./docs/GenAI%20Financial%20Analyst%20-%20Technical%20Guide.pdf)**

| Project | Type | Tech Stack | Description |
|---------|------|------------|-------------|
| **[Macro Risk Analyst](./code/Macro_Risk_Analyst.ipynb)** | 🤖 SQL Agent | LangChain Llama 3 SQLite | An autonomous agent that performs cross-domain risk analysis by joining Corporate and Retail insolvency datasets. Features Schema Injection and Self-Correction mechanisms to prevent hallucinations. |
| **[Financial Insight Engine](./code/rag_agent.py)** | 📄 RAG Agent | ChromaDB HuggingFace | A citation-aware retrieval system for digesting complex financial reports (PDFs) and extracting strategic outlooks. Features a manual ingestion pipeline for preserving page-level metadata. |

## Technical Concepts & Mathematical Foundations

### 1. The Core Objective: Next-Token Prediction

At its heart, a Generative Large Language Model (LLM) is a probabilistic engine. It doesn't know facts; it calculates the statistical likelihood of the next piece of text.

**The Formula:**

$$P(w) = \prod_{t=1}^{T} P(w_t | w_{1:t-1})$$

**💡 The Intuition (For Non-Technical Audiences):**

Imagine a super-powered autocomplete.

- $w_{1:t-1}$ is the context: *The cat sat on the...*
- $w_t$ is the prediction: The model calculates that *mat* has a 85% probability, while *car* has only a 2% probability.

It repeats this process millions of times to generate fluent paragraphs.
