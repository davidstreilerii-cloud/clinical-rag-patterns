"""
Plain retrieval over the example corpus.

Deliberately minimal: chunk, embed, route, search, return passages with their
provenance. There is **no confidence score, no verification receipt, and no gap
signal** here. Those belong to the private system this example is drawn from, and
ARCHITECTURE.md describes what they do and why they are not in this file.

What this does show is the part that is reusable: split the corpus by domain,
route the query to one collection, and carry provenance all the way through to
the answer so every returned passage can be cited back to a source, a retrieval
date, and a stated subset.

Run it:

    python -m example.retrieve "national 30-day readmission rate for heart failure"
"""
from __future__ import annotations

import sys
from pathlib import Path

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

from example.ingest import chunk_id, load_corpus, tag_document
from example.route import DOMAINS, route

CORPUS_DIR = Path(__file__).parent / "corpus"
DB_DIR = Path(__file__).parent / "chroma"

#: A small, fast, permissively-licensed embedding model. The private system uses
#: larger domain-tuned models per collection; the pattern is identical.
MODEL = "sentence-transformers/all-MiniLM-L6-v2"

#: Documents are split on blank lines and packed to roughly this many characters.
#: Chunking policy is a real tuning surface -- too small and a table row loses its
#: header, too large and retrieval returns a whole document for a one-line answer.
TARGET_CHUNK_CHARS = 1400


def _chunk(text: str) -> list[str]:
    """Split on blank lines, then pack paragraphs up to TARGET_CHUNK_CHARS."""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    current = ""
    for para in paragraphs:
        if current and len(current) + len(para) > TARGET_CHUNK_CHARS:
            chunks.append(current)
            current = para
        else:
            current = f"{current}\n\n{para}" if current else para
    if current:
        chunks.append(current)
    return chunks


def build_index() -> chromadb.api.ClientAPI:
    """
    Ingest the corpus into per-domain collections.

    Safe to re-run: ids are deterministic and this upserts, so a second run
    updates in place rather than duplicating. That property is the whole reason
    `chunk_id` exists.
    """
    client = chromadb.PersistentClient(path=str(DB_DIR))
    embed = SentenceTransformerEmbeddingFunction(model_name=MODEL)

    for name in DOMAINS:
        client.get_or_create_collection(name, embedding_function=embed)

    for doc in load_corpus(CORPUS_DIR):
        prov = doc["provenance"]
        # Route on the document's own opening text, which carries the title and
        # scope note. Routing per document rather than per chunk keeps a single
        # document's chunks together in one collection.
        collection_name = route(doc["text"][:1200])
        collection = client.get_collection(collection_name, embedding_function=embed)

        chunks = _chunk(doc["text"])
        collection.upsert(
            ids=[chunk_id(doc, i) for i in range(len(chunks))],
            documents=chunks,
            metadatas=[
                {
                    "source_file": doc["source"],
                    "source_url": prov["source"],
                    "retrieved": prov["retrieved"],
                    "published": prov["published"],
                    # Chroma metadata values must be scalars, so tag lists are
                    # joined. Empty string means "looked, found none".
                    **{
                        f"tag_{k}": ",".join(v)
                        for k, v in tag_document(chunk).items()
                    },
                }
                for chunk in chunks
            ],
        )
    return client


def search(query: str, k: int = 3) -> list[dict]:
    """
    Route the query, search that collection, return passages with provenance.

    Every result carries where it came from and when it was retrieved. A passage
    that cannot be cited is not more useful than no passage -- it is less useful,
    because it looks the same as one that can.
    """
    client = chromadb.PersistentClient(path=str(DB_DIR))
    embed = SentenceTransformerEmbeddingFunction(model_name=MODEL)
    collection_name = route(query)
    collection = client.get_collection(collection_name, embedding_function=embed)

    result = collection.query(query_texts=[query], n_results=k)
    hits = []
    for doc, meta, dist in zip(
        result["documents"][0], result["metadatas"][0], result["distances"][0]
    ):
        hits.append(
            {
                "routed_to": collection_name,
                "text": doc,
                "source_file": meta.get("source_file", ""),
                "source_url": meta.get("source_url", ""),
                "retrieved": meta.get("retrieved", ""),
                "distance": round(dist, 4),
            }
        )
    return hits


def main() -> int:
    query = " ".join(sys.argv[1:]).strip()
    if not query:
        print(__doc__)
        return 2

    build_index()
    hits = search(query)
    print(f'\nQuery:    {query}')
    print(f'Routed to: {hits[0]["routed_to"] if hits else route(query)}\n')
    if not hits:
        print("No passages retrieved.")
        return 1
    for i, hit in enumerate(hits, 1):
        print(f'--- {i}. {hit["source_file"]}  (distance {hit["distance"]})')
        print(f'    source:    {hit["source_url"]}')
        print(f'    retrieved: {hit["retrieved"]}')
        body = " ".join(hit["text"].split())
        print(f'    {body[:280]}...\n')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
