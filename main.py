import os
from dotenv import load_dotenv
from anthropic import Anthropic 
import pandas as pd
import argparse
from tqdm import tqdm 

load_dotenv()


# Get API key and file path from environment variables
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
CSV_FILE_PATH = os.getenv('CSV_FILE_PATH')

client = Anthropic(api_key=ANTHROPIC_API_KEY)
file_path = CSV_FILE_PATH
print(file_path)
 

def analyze_sentiment(reviews):
    """
    Process the CSV file in chunks to avoid token limits
    
    Args:
        file_path: Path to the CSV file
        chunk_size: Number of reviews to process in each batch
    
    Returns:
        Summary of sentiment analysis
    """
    prompt = (
        "Below are customer reviews. Please analyze the sentiment of each review "
        "and categorize it as Positive, Negative, or Neutral. Then, provide a summary in percentages: "
        "1. Total number of reviews "
        "2. Number of Positive reviews and their percentage (%) "
        "3. Number of Negative reviews and their percentage (%) "
        "4. Number of Neutral reviews and their percentage (%)\n\n"
        "Additionally, please provide the final metrics showing the percentage breakdown for each category "
        "in a clear and concise format.\n\n"
        f"Reviews: {reviews}"
    )
    
    print("Sending data to claude for the analysis")
 
    try:
        response = client.messages.create(
            model='claude-3-5-sonnet-20241022',
            max_tokens = 1000,
            messages=[
                {
                    'role': 'user',
                    'content': prompt
                }
            ]
        )
        return response.content[0].text if response.content else "No reponse found"        
    except Exception as e:
        print(f"Error with API request: {e}")
        
def process_csv(file_path, chunk_size=20):
    """
     Reads a CSV file in chunks, sends reviews to Claude for sentiment analysis.
    
    Args:
        file_path (str): Path to the CSV file.
        chunk_size (int): Number of reviews to process per batch to avoid token limits.
    
    """
    
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' not found")
        return
    
    try:
        df = pd.read_csv(file_path)
        if 'Review Body' not in df.columns:
            print("Error: CSV file must contain a 'Review Body' column")
            return
        total_reviews = len(df)
        print(f"Processing {total_reviews} reviews in chunks of {chunk_size}")
        
        all_results = []
        for i in tqdm(range(0, total_reviews, chunk_size), desc="processing batches" ):
            batch_reviews = df['Review Body'][i:i+chunk_size].tolist()
            result = analyze_sentiment(batch_reviews)
            all_results.append(result)
        
        print("\=== SENTIMENT ANALYSIS RESULT")
        for res in all_results:
            print(res)
    except Exception as e:
        print(f"Error processing file : {e}")
        
    except Exception as e:
        print(f"Error processing file: {e}")
    
if __name__ == '__main__':
     
    process_csv(file_path)

 