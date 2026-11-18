# Embeddings, Vector Search, and RAG

An embedding converts text into a numeric vector. A vector represents semantic features, allowing related text to be retrieved even when it does not share the same exact keywords. Cosine similarity compares the direction of two vectors: cosine(A,B) = (A dot B) divided by (the product of their magnitudes). A higher cosine similarity means the directions are more similar.

Retrieval-augmented generation (RAG) has two main phases. During ingestion, the system extracts text, splits it into chunks, attaches metadata, creates document embeddings, and stores vectors and text in a vector database. During question answering, the system embeds the user's query, retrieves the nearest passages, and asks the language model to answer from those passages.

Chunk size and overlap affect retrieval. Very small chunks may lose context; very large chunks may contain unrelated content and increase prompt size. Overlap helps preserve facts that cross chunk boundaries. These settings should be selected by evaluating known questions against expected source documents, not by intuition alone.

Gemini's gemini-embedding-001 model supports task types such as RETRIEVAL_DOCUMENT for indexed passages, RETRIEVAL_QUERY for search queries, and SEMANTIC_SIMILARITY for comparing sentence meanings. These modes should be applied consistently for their intended use.

Chroma is a local vector database. PersistentClient writes database files to a local path and reloads them on restart. Each indexed chunk in this project stores source filename, page number, and chunk index so a response can provide a traceable citation.
