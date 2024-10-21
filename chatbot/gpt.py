import openai
from openai import OpenAI
# Set your OpenAI API key

# for complete the message
# def stream_gpt_response(messages, max_response_length, temperature):
#     response = openai.ChatCompletion.create(
#         model="gpt-3.5-turbo",
#         messages=messages,
#         max_tokens=max_response_length,
#         temperature=temperature,
#         stream=True  # Enable streaming
#     )

#     def event_stream():
#         full_response = ""
#         for chunk in response:
#             if 'choices' in chunk:
#                 content = chunk['choices'][0].get('delta', {}).get('content', '')
#                 finish_reason = chunk['choices'][0].get('finish_reason', None)

#                 # Accumulate the content into a full response
#                 if content:
#                     full_response += content
#                     yield content

#                 # If finish_reason is "length", the response was cut off
#                 if finish_reason == 'length':
#                     yield "\n\n[Response was cut off. Would you like to continue?]"
#                     return

#         # If finish_reason is "stop", the response is complete
#         if finish_reason == 'stop':
#             yield "\n\n[Response complete.]"

#     return event_stream

def stream_gpt_response(messages, max_response_length, temperature):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        # max_tokens=max_response_length,
        temperature=temperature,
        stream=True  # Enable streaming
    )

    def event_stream():
        for chunk in response:
            if 'choices' in chunk:
                content = chunk['choices'][0].get('delta', {}).get('content', '')
                if content:
                    yield content
                    # yield f'{{"sender": "bot", "message": "{content}"}}\n\n'

    return event_stream


# get full response at once
# import time
# def stream_gpt_response(messages, max_response_length, temperature):
#     # Non-streaming GPT API call
#     response = openai.ChatCompletion.create(
#         model="gpt-3.5-turbo",
#         messages=messages,
#         max_tokens=max_response_length,
#         temperature=temperature
#     )

#     # Extract the full response content
#     full_response = response['choices'][0]['message']['content']

#     def event_stream():
#         chunk_size = 50  # Define how many characters you want to send per chunk
#         for i in range(0, len(full_response), chunk_size):
#             chunk = full_response[i:i+chunk_size]
#             yield chunk
#             time.sleep(0.1)  # Simulate delay for streaming

#     return event_stream


def evaluate_interest(questions_replies):
    """
    Evaluates the user's interest based on the replies to the questions and correct answers.

    Parameters:
        questions_replies (list of dict): A list of dictionaries, where each dictionary contains:
            - 'question': The question asked.
            - 'answer': The user's reply.
            - 'correct_answer': The expected correct answer.
    
    Returns:
        dict: A dictionary with the interest score for each question and the overall score in percentage.
    """
    
    # Build a single prompt that includes all questions and answers
    combined_content = "You are an assistant evaluating user interest based on the correct answers.\n"
    combined_content += "For each question, evaluate the user's level of interest on a scale of 0 to 100, based on how closely their response matches the correct answer. Provide each score as a number only, one per line.\n\n"

    # Add each question-answer pair to the combined message
    for index, qr in enumerate(questions_replies, start=1):
        question = qr.get('question', '')
        user_reply = qr.get('answer', '')
        correct_answer = qr.get('correct_answer', '')
        
        # Skip if any of the required fields are missing
        if not question or not user_reply:
            continue

        # Add the details to the message
        combined_content += f"Question {index}: {question}\n"
        combined_content += f"User's Response: {user_reply}\n"
        combined_content += f"Correct Answer: {correct_answer}\n\n"

    # Prepare the message for GPT model
    messages = [
        {"role": "system", "content": combined_content}
    ]

    # Make a single API call
    try:
        client = OpenAI()
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=100,  # Adjust as needed
            temperature=0
        )

        # Process the response
        content = response.choices[0].message.content.strip().splitlines()

        # Convert response lines to scores
        scores = [int(score.strip()) for score in content if score.strip().isdigit()]

    except (ValueError, KeyError, Exception) as e:
        print(f"Error processing response: {str(e)}")
        scores = [0] * len(questions_replies)  # Fallback if there's an error

    # Calculate the overall interest percentage
    total_score = sum(scores)
    num_questions = len(questions_replies)
    overall_interest_percentage = int((total_score / (num_questions * 100)) * 100) if num_questions > 0 else 0

    # Create a result dictionary
    result = {
        "individual_scores": scores,
        "overall_score": overall_interest_percentage
    }

    return result