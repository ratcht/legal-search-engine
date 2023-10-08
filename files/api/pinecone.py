import pandas as pd  # for storing text and embeddings data
from files.api.openai import create_embedding, num_tokens
import logging
from werkzeug.utils import secure_filename
import pinecone
from files.obj.searchtype import SearchType

def get_pinecone_index(API_KEY, ENVIRONMENT, INDEX) -> pinecone.Index:
  pinecone.init(
    api_key=API_KEY,
    environment=ENVIRONMENT 
  )
  index = pinecone.Index(INDEX)
  return index



def get_starting_id(pinecone_index: pinecone.Index):
  return pinecone_index.describe_index_stats()['total_vector_count']


def rank_strings_pinecone(
  query: str,
  pinecone_index: pinecone.Index,
  EMBEDDING_MODEL: str,
  type: SearchType,
  top_n: int = 100
  ):

  query_embedding_response = create_embedding(
    EMBEDDING_MODEL,
    query
  )

  query_embedding = query_embedding_response["data"][0]["embedding"]
  print("Created Embedding")

  pinecone_res = pinecone_index.query(query_embedding, top_k=top_n, include_metadata=True, filter={"type": type.value})
  print("Indexed Pinecone")

  relatednesses = []
  id = []
  metadata = []
  for match in pinecone_res['matches']:
    id.append(match['id'])
    metadata.append(match['metadata'])
    relatednesses.append(match['score'])

  return metadata, id, relatednesses

def upload_to_pinecone(df: pd.DataFrame, pinecone_index: pinecone.Index, batch_size: int = 32):

  for batch_start in range(0, len(df.index), batch_size):
    batch_end = batch_start + batch_size
    
    print(f"Batch {batch_start} to {batch_end-1}")

    batch = df[batch_start:batch_end]

    batch_titles = batch['title'].tolist()

    startingID = get_starting_id(pinecone_index)
    batch_ids = [i+startingID for i in range(0,len(batch_titles))]
    batch_ids_string = list(map(str, batch_ids))
    batch_embeddings = batch['embedding'].tolist()
    batch_text = batch['text'].tolist()

    meta = [{'title':title, 'text': text } for title, text in zip(batch_titles, batch_text)]
    
    # prep metadata and upsert batch
    to_upsert = zip(batch_ids_string, batch_embeddings, meta)

    # upsert to Pinecone
    pinecone_index.upsert(vectors=list(to_upsert))


def get_statistics(pinecone_index: pinecone.Index):
  return pinecone_index.describe_index_stats()


def delete_by_title_pinecone(pinecone_index: pinecone.Index, document_title: str):
  pinecone_index.delete(delete_all=False, filter={"secured_title": document_title})




  