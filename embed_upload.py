# embed_upload.py
import os
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled, CouldNotRetrieveTranscript, InvalidVideoId, VideoUnavailable, YouTubeRequestFailed
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

# Function to initialize the embedding model and ChromaDB vector store
def initialize_vector_store(chromadb_path="chromadb/"):
    os.makedirs(chromadb_path, exist_ok=True)

    embeddings = FastEmbedEmbeddings(
        model_name="BAAI/bge-small-en-v1.5",
        batch_size=512,
        parallel=2,
        threads=4
    )

    vector_store = Chroma(
        collection_name="example_collection",
        embedding_function=embeddings,
        persist_directory=chromadb_path
    )
    
    return vector_store

# Function to fetch and combine YouTube transcripts
def get_combined_transcript(video_id, chunk_size=10):
    try:
        print(f"Fetching transcript for video_id: {video_id}...")
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        print(f"Transcript fetched. Total chunks to create: {len(transcript) // chunk_size + 1}")
        
        combined_transcript = [
            {
                "text": " ".join([item["text"] for item in transcript[i:i+chunk_size]]),
                "start": "{:.2f}".format(transcript[i]["start"]),
                "duration": "{:.2f}".format(sum([item["duration"] for item in transcript[i:i+chunk_size]]))
            }
            for i in range(0, len(transcript), chunk_size)
        ]
        print(f"Transcript successfully chunked into {len(combined_transcript)} chunks.")
        return combined_transcript
    except NoTranscriptFound as e:
        print(f"Error: No transcript found for video_id: {video_id}. ({e})")
    except TranscriptsDisabled as e:
        print(f"Error: Transcripts are disabled for video_id: {video_id}. ({e})")
    except CouldNotRetrieveTranscript as e:
        print(f"Error: Could not retrieve transcript for video_id: {video_id}. ({e})")
    except InvalidVideoId as e:
        print(f"Error: Invalid video ID: {video_id}. ({e})")
    except VideoUnavailable as e:
        print(f"Error: Video is unavailable: {video_id}. ({e})")
    except YouTubeRequestFailed as e:
        print(f"Error: YouTube request failed: {video_id}. ({e})")
    except Exception as e:
        print(f"Error: {e}")
    return None

# Function to check if the video_id already has embeddings
def embeddings_exist(video_id, vector_store):
    # Create the filter to search for the specific video_id in metadata
    filter = {"video_id": video_id}
    
    try:
        # Perform the similarity search with the filter
        results = vector_store.similarity_search(query="", k=1, filter=filter)
        
        # Check if any results were returned
        return len(results) > 0
    except Exception as e:
        print(f"Error in search method: {e}")
        return False

# Function to add the combined transcript to ChromaDB
def add_transcript_to_chroma(video_id, vector_store, chunk_size=10):
    combined_transcript = get_combined_transcript(video_id, chunk_size)
    if combined_transcript is None:
        return
    
    documents = []
    for i, combined_item in enumerate(combined_transcript):
        chunk_id = f"{video_id}#text{i+1}"
        print(f"Processing chunk {i+1}/{len(combined_transcript)}: ID = {chunk_id}")
        
        document = Document(
            page_content=combined_item["text"],
            metadata={
                "start": combined_item["start"],
                "duration": combined_item["duration"],
                "video_id": video_id
            },
            id=chunk_id
        )
        
        documents.append(document)
    
    print(f"Adding {len(documents)} documents to the ChromaDB vector store...")
    vector_store.add_documents(documents=documents)
    print("Documents successfully added to the vector store.")

# Main function to run the entire process
def process_video_transcript(video_id, chromadb_path="chromadb/", chunk_size=10):
    vector_store = initialize_vector_store(chromadb_path)
    
    if embeddings_exist(video_id, vector_store):
        print(f"Embeddings already exist for video_id: {video_id}. Skipping processing.")
    else:
        add_transcript_to_chroma(video_id, vector_store, chunk_size)
    
    return vector_store

if __name__ == "__main__":
    # Example usage:
    video_id = "X7gKBGVz4vs"
    print(f"Starting process for video_id: {video_id}")
    vector_store = process_video_transcript(video_id)
    print("Process completed.")












# # embed_upload.py
# import os
# from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
# from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
# from langchain_chroma import Chroma
# from langchain_core.documents import Document

# # Function to initialize the embedding model and ChromaDB vector store
# def initialize_vector_store(chromadb_path="chromadb/"):
#     os.makedirs(chromadb_path, exist_ok=True)

#     embeddings = FastEmbedEmbeddings(
#         model_name="BAAI/bge-small-en-v1.5",
#         batch_size=512,
#         parallel=2,
#         threads=4
#     )

#     vector_store = Chroma(
#         collection_name="example_collection",
#         embedding_function=embeddings,
#         persist_directory=chromadb_path
#     )
    
#     return vector_store

# # Function to fetch and combine YouTube transcripts
# def get_combined_transcript(video_id, chunk_size=10):
#     try:
#         print(f"Fetching transcript for video_id: {video_id}...")
#         transcript = YouTubeTranscriptApi.get_transcript(video_id)
#         print(f"Transcript fetched. Total chunks to create: {len(transcript) // chunk_size + 1}")
        
#         combined_transcript = [
#             {
#                 "text": " ".join([item["text"] for item in transcript[i:i+chunk_size]]),
#                 "start": "{:.2f}".format(transcript[i]["start"]),
#                 "duration": "{:.2f}".format(sum([item["duration"] for item in transcript[i:i+chunk_size]]))
#             }
#             for i in range(0, len(transcript), chunk_size)
#         ]
#         print(f"Transcript successfully chunked into {len(combined_transcript)} chunks.")
#         return combined_transcript
#     except TranscriptsDisabled:
#         print(f"Error: Transcripts are disabled for video_id: {video_id}. No subtitles available.")
#     except NoTranscriptFound:
#         print(f"Error: No subtitles found for video_id: {video_id}.")
#     except Exception as e:
#         print(f"Error fetching transcript: {e}")
#     return None

# # Function to check if the video_id already has embeddings
# def embeddings_exist(video_id, vector_store):
#     # Create the filter to search for the specific video_id in metadata
#     filter = {"video_id": video_id}
    
#     try:
#         # Perform the similarity search with the filter
#         results = vector_store.similarity_search(query="", k=1, filter=filter)
        
#         # Check if any results were returned
#         return len(results) > 0
#     except Exception as e:
#         print(f"Error in search method: {e}")
#         return False

# # Function to add the combined transcript to ChromaDB
# def add_transcript_to_chroma(video_id, vector_store, chunk_size=10):
#     combined_transcript = get_combined_transcript(video_id, chunk_size)
#     if combined_transcript is None:
#         return
    
#     documents = []
#     for i, combined_item in enumerate(combined_transcript):
#         chunk_id = f"{video_id}#text{i+1}"
#         print(f"Processing chunk {i+1}/{len(combined_transcript)}: ID = {chunk_id}")
        
#         document = Document(
#             page_content=combined_item["text"],
#             metadata={
#                 "start": combined_item["start"],
#                 "duration": combined_item["duration"],
#                 "video_id": video_id
#             },
#             id=chunk_id
#         )
        
#         documents.append(document)
    
#     print(f"Adding {len(documents)} documents to the ChromaDB vector store...")
#     vector_store.add_documents(documents=documents)
#     print("Documents successfully added to the vector store.")

# # Main function to run the entire process
# def process_video_transcript(video_id, chromadb_path="chromadb/", chunk_size=10):
#     vector_store = initialize_vector_store(chromadb_path)
    
#     if embeddings_exist(video_id, vector_store):
#         print(f"Embeddings already exist for video_id: {video_id}. Skipping processing.")
#     else:
#         add_transcript_to_chroma(video_id, vector_store, chunk_size)
    
#     return vector_store

# if __name__ == "__main__":
#     # Example usage:
#     video_id = "X7gKBGVz4vs"
#     print(f"Starting process for video_id: {video_id}")
#     vector_store = process_video_transcript(video_id)
#     print("Process completed.")
