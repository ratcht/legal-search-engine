from flask import Flask, session
from files.api.openai import query, num_tokens, create_embedding
from files.obj.searchobj import SearchObj, parse_search_history
from files.obj.searchtype import SearchType
from files.util import ComplexEncoder, filter_list
import logging
import json
import os
from files.api.pinecone import rank_strings_pinecone
from files.obj.searchtype import SearchType
from files.api.datastore import get_datastore_entry
import pandas as pd
import pinecone
import logging

# process embeddings
def create_df(chunks: list, title: str, EMBEDDING_MODEL: str, batch_size = 1000) -> pd.DataFrame:
  embeddings = []
  for batch_start in range(0, len(chunks), batch_size):
    batch_end = batch_start + batch_size
    batch = chunks[batch_start:batch_end]
    print(f"Batch {batch_start} to {batch_end-1}")

    response = create_embedding(EMBEDDING_MODEL, batch)
    
    batch_embeddings = [e["embedding"] for e in response["data"]]
    embeddings.extend(batch_embeddings)

  titles = [title for i in range(len(embeddings))]
  df = pd.DataFrame({"text": chunks, "embedding": embeddings, "title": titles})
  return df


def create_query(query: str, type: SearchType, pinecone_index: pinecone.Index, EMBEDDING_MODEL: str, GPT_MODEL: str, GPT_PROMPT: str, token_budget: int):
  """Return a message for GPT, with relevant source texts pulled from a dataframe."""
  metadata, ids, relatedness = rank_strings_pinecone(query, pinecone_index, EMBEDDING_MODEL, top_n=15)
  logging.info("Finished ranking strings")

  chunks = []

  metadata_type_filtered = [metadata_group for metadata_group in metadata if metadata_group["type"] == type.value]
  logging.info("Type filtered")

  introduction = GPT_PROMPT
  question = f"\n\nQuestion: {query}"
  message = introduction
  excerpts = []

  titles = []
  for metadata_group, id in zip(metadata_type_filtered,ids):
    title = metadata_group["title"]
    titles.append(title)
    next_article = f'\n\Document Title: {title}. Excerpt:\n"""\n{get_datastore_entry("Chunk", id)["Text"]}\n"""'
    logging.info("=======NEXT ARTICLE=========")
    logging.info(next_article)

    if (num_tokens(message + next_article + question, model=GPT_MODEL) > token_budget):
      break
    else:
      message += next_article
      excerpts.append(next_article)

  return message + question, titles, excerpts

def search(prompt: str, type: SearchType, pinecone_index: pinecone.Index, GPT_MODEL: str, EMBEDDING_MODEL: str, GPT_PROMPT:str):
  try:
    message, titles, excerpts = create_query(prompt, type, pinecone_index, EMBEDDING_MODEL=EMBEDDING_MODEL, GPT_MODEL=GPT_MODEL, GPT_PROMPT=GPT_PROMPT, token_budget=16000-4000)
  except Exception as e:
    raise Exception(f"From create_query()... {e}")

  # filter titles
  filtered_titles = filter_list(titles)
  stripped_titles = [os.path.splitext(filtered_title)[0] for filtered_title in filtered_titles]

  try:
    response = query(message, GPT_MODEL)
  except Exception as e:
    raise Exception(f"From query()... {e}")
  
  return response, stripped_titles, excerpts


def update_search_history(search_obj: SearchObj):
  # update search history
  search_history = parse_search_history(
    json.loads(session["search"])
  )
  search_history.append(search_obj)
  session["search"] = json.dumps(search_history, cls=ComplexEncoder)
