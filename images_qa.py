import os
from dotenv import load_dotenv
from anthropic import Anthropic 
 

load_dotenv()

ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
 
 
client = Anthropic(api_key=ANTHROPIC_API_KEY)

def encode_image(image_path):
    """
    Encode image to base64.
    Args:
        image_path: path to image file
    returns:
        base64 encoded image
    """
    import base64
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def build_image_comparison_message(image_path1, image_path2, question):
    """
    Build message for comparing two images.
    Args:
        image_path1: path to the first image
        image_path2: path to the second image
        question: question about the comparison
    returns:
        Formatted message for the API
    """
    return [
        {
            'role': 'user',
            'content': [
                {
                    'type': 'text',
                    'text': question
                },
                {
                    'type': 'image',
                    'source': {
                        'type': 'base64',
                        'media_type': 'image/jpeg',
                        'data': encode_image(image_path1)
                    }
                },
                {
                    'type': 'image',
                    'source': {
                        'type': 'base64',
                        'media_type': 'image/jpeg',
                        'data': encode_image(image_path2)
                    }
                }
            ]
        }
    ]
 

def get_response(messages, model='claude-3-5-sonnet-20241022', max_tokens=1000):
    """
    Get response from Claude API.
    Args:
        messages: formatted messages to send to API
        model: model to use
        max_tokens: maximum tokens in response
    returns:
        API response or error message
    """
    try:
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=messages
        )
        return response.content[0].text if response.content else "No response found"
    except Exception as e:
        print(f"Error with API request: {e}")
        return None
def compare_images(image_path1, image_path2, question):
    """
    Compare two images and answer question about their differences and similarities.
    """
    messages = build_image_comparison_message(image_path1, image_path2, question)
    return get_response(messages)

if __name__ == '__main__':
    image_path1 = './images/torre-eiffel-parigi.jpg'
    image_path2 = './images/torre-eiffel-parigi2.jpeg'
    question = 'What are the key differences and similarities between these two images?'
    answer = compare_images(image_path1, image_path2, question)
    print(answer)