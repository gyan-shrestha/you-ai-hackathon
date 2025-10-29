# you-ai-hackathon

A lightweight Retrieval-Augmented Generation (RAG) pipeline using **You.com APIs** for document retrieval and **SentenceTransformers** for semantic ranking and question answering.

---

## Features

- Retrieve insurance PDFs using the **You.com Search API**  
- Extract PDF text using the **You.com Contents API**  
- Rank documents using **semantic embeddings** (`all-MiniLM-L6-v2`)  
  - The system performs **hybrid ranking** combining PDF metadata from the You.com Search API and PDF content from the You.com Contents API  
- Generate final answers using the **You.com Express Agent**  

---

## Setup Instructions

1. **Create and activate the Conda environment**

   ```bash
   conda create -n you_rag python=3.10 -y
   conda activate you_rag

2. **Install dependencies**

    ```
    pip install -r requirements.txt

3. **Create a .env file in the project root**

    ```
    echo "YOU_API_KEY=ydc_xxxxxxxxxxxxxxx" > .env

4. **Run the pipeline**

    ```
    python smart_rag.py

**You’ll be prompted for a query, for example:**

    ```
    Enter your question: What is the deductible for Molina Silver HMO 2025 in Florida?