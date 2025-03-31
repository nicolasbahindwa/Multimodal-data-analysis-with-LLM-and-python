import os
from dotenv import load_dotenv
from anthropic import Anthropic
import pandas as pd
import argparse
from tqdm import tqdm

load_dotenv()

ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
client = Anthropic(api_key=ANTHROPIC_API_KEY)

def create_prompt(question, schema=None):
    """
    Create a prompt for text-to-SQL translation.
    Args:
        question: Natural language question to translate to SQL
        schema: Optional database schema information
    returns:
        Formatted prompt for the model
    """
    parts = []
    
    # Add database schema information
    parts.append('# Database Schema')
    if schema:
        parts.append(schema)
    else:
        parts.append('CREATE TABLE Customers(customerID int, customerName text, city text);')
        parts.append('CREATE TABLE Orders(orderID int, customerID int, orderDate date, totalAmount decimal);')
        parts.append('CREATE TABLE Products(productID int, productName text, price decimal, category text);')
        parts.append('CREATE TABLE OrderDetails(orderID int, productID int, quantity int);')
    
    # Add instructions and question
    parts.append('\n# Instructions')
    parts.append('Translate the following question into a valid SQL query based on the schema above.')
    parts.append('Return only the SQL query without any explanations.')
    parts.append('\n# Question')
    parts.append(question)
    
    return '\n'.join(parts)

def get_sql_translation(question, schema=None, model='claude-3-5-sonnet-20241022', max_tokens=1000):
    """
    Translate natural language question to SQL using Claude.
    Args:
        question: Natural language question
        schema: Optional database schema
        model: Model to use
        max_tokens: Maximum tokens in response
    returns:
        SQL query
    """
    prompt = create_prompt(question, schema)
    
    try:
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=[{'role': 'user', 'content': prompt}]
        )
        sql_query = response.content[0].text.strip()
        return sql_query
    except Exception as e:
        print(f"Error with API request: {e}")
        return None

def load_schema_from_file(file_path):
    """
    Load database schema from a file.
    Args:
        file_path: Path to the schema file
    returns:
        Schema as a string
    """
    try:
        with open(file_path, 'r') as file:
            return file.read()
    except Exception as e:
        print(f"Error loading schema file: {e}")
        return None

def batch_process_questions(questions_file, output_file, schema_file=None):
    """
    Process a batch of questions from a file and save results.
    Args:
        questions_file: File with questions (one per line)
        output_file: File to save results
        schema_file: Optional schema file
    """
    # Load schema if provided
    schema = None
    if schema_file:
        schema = load_schema_from_file(schema_file)
    
    # Load questions
    with open(questions_file, 'r') as file:
        questions = [line.strip() for line in file if line.strip()]
    
    # Process questions
    results = []
    for question in tqdm(questions, desc="Translating questions"):
        sql_query = get_sql_translation(question, schema)
        results.append({"question": question, "sql_query": sql_query})
    
    # Save results
    df = pd.DataFrame(results)
    df.to_csv(output_file, index=False)
    print(f"Results saved to {output_file}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Text to SQL translation using Claude')
    parser.add_argument('--question', type=str, help='Single question to translate')
    parser.add_argument('--schema', type=str, help='Path to database schema file')
    parser.add_argument('--questions_file', type=str, help='File containing questions to translate')
    parser.add_argument('--output_file', type=str, default='sql_translations.csv', help='Output file for batch processing')
    
    args = parser.parse_args()
    
    if args.question:
        # Process single question
        schema = None
        if args.schema:
            schema = load_schema_from_file(args.schema)
        
        sql = get_sql_translation(args.question, schema)
        print(f"Question: {args.question}")
        print(f"SQL: {sql}")
    
    elif args.questions_file:
        # Process batch of questions
        batch_process_questions(args.questions_file, args.output_file, args.schema)
    
    else:
        # Example usage
        question = "How many customers do we have?"
        sql = get_sql_translation(question)
        print(f"Question: {question}")
        print(f"SQL: {sql}")