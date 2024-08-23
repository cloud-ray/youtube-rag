import os
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from langchain_chroma import Chroma
from langchain_groq import ChatGroq
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.prompts import PromptTemplate
from dotenv import load_dotenv

load_dotenv()

os.environ["TOKENIZERS_PARALLELISM"] = "false"

LANGCHAIN_TRACING_V2 = os.getenv('LANGSMITH_TRACING')
LANGCHAIN_ENDPOINT = os.getenv('LANGCHAIN_ENDPOINT')
LANGCHAIN_API_KEY = os.getenv('LANGSMITH_API_KEY')
LANGCHAIN_PROJECT = os.getenv('LANGCHAIN_PROJECT')

# VisionTaskOutput class definition
class VisionTaskOutput(BaseModel):
    answer: str = Field(description="The detailed response to the question")
    start_value: float = Field(description="The 'start' value associated with the best answer")

# Function to create a YouTube link from video_id and timestamp
def create_youtube_link(video_id, timestamp):
    minutes = int(timestamp // 60)
    seconds = int(timestamp % 60)
    timestamp_str = f"{minutes}m{seconds}s"
    return f"https://www.youtube.com/watch?v={video_id}&t={timestamp_str}"

# Function to initialize the language model
def initialize_llm():
    return ChatGroq(
        model="llama3-70b-8192",
        temperature=0.5,
        api_key=os.getenv('GROQ_API_KEY')
    )

# Function to initialize the embedding model and vector store
def initialize_vector_store(chromadb_path="chromadb/"):
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

# Function to set up the retriever from the vector store
def initialize_retriever(vector_store):
    return vector_store.as_retriever(
        search_type="mmr", search_kwargs={"k": 3, "fetch_k": 5}
    )

# Function to define the prompt template
def create_prompt_template():
    return PromptTemplate(
        template="Answer the user query and give a detailed explanation to the reasoning for your 'answer'. You MUST provide the 'start' value associated to the best answer\n{format_instructions}\nContext: {context}\nQuestion: {question}\n",
        input_variables=["question", "context"],
        partial_variables={"format_instructions": JsonOutputParser(pydantic_object=VisionTaskOutput).get_format_instructions()},
    )

# Function to format the documents and extract video_id
def format_docs(docs, original_video_id):
    if docs:
        first_doc_metadata = docs[0].metadata
        original_video_id = first_doc_metadata.get('video_id', original_video_id)
    
    return [(doc.page_content, doc.metadata) for doc in docs], original_video_id

# Function to create and run the RAG chain
def run_rag_chain(user_question, retriever, prompt_template, llm, original_video_id):
    def format_and_extract_docs(docs):
        return format_docs(docs, original_video_id)

    rag_chain = (
        {"context": retriever | format_and_extract_docs, "question": RunnablePassthrough()}
        | prompt_template
        | llm
        | JsonOutputParser(pydantic_object=VisionTaskOutput)
    )

    try:
        return rag_chain.invoke(user_question)
    except Exception as e:
        print(f"Error running RAG chain: {e}")
        return {"answer": "Error occurred", "start_value": None}

# Main function to generate the YouTube link
def generate_youtube_link(user_question, original_video_id):
    if not original_video_id:
        return None, "video_id is required."
    
    llm = initialize_llm()
    vector_store = initialize_vector_store()
    retriever = initialize_retriever(vector_store)
    prompt_template = create_prompt_template()
    
    output = run_rag_chain(user_question, retriever, prompt_template, llm, original_video_id)
    
    answer = output.get('answer')
    start_value = output.get('start_value')

    # Print the values for debugging
    print(f"Original Video ID: {original_video_id}")
    print(f"Start Value (before rounding): {start_value}")

    if original_video_id and start_value is not None:
        start_seconds = int(round(start_value))
        youtube_link = create_youtube_link(original_video_id, start_value)
        print(f"YouTube Link: {youtube_link}")  # Print the generated YouTube link

        return {
            'youtube_link': youtube_link,
            'answer': answer,
            'start': start_seconds  # Include start value in response
        }
    else:
        return {
            'error': 'Unable to create YouTube link or retrieve answer.',
            'start': None  # Explicitly return None if start_value is missing
        }

# Example usage:
if __name__ == "__main__":
    user_question = 'How does the prompt then detect work?'
    original_video_id = 'X7gKBGVz4vs'

    youtube_link, answer = generate_youtube_link(user_question, original_video_id)
    if youtube_link:
        print(f"Answer:\n{answer}")
        print(f"Check it out here:\n   {youtube_link}")
    else:
        print(answer)
