from django.shortcuts import render, get_object_or_404, HttpResponse
from django.http import StreamingHttpResponse, JsonResponse, HttpResponseNotAllowed
from .models import User, ChatSession, Form, Question, Chatbot
from .gpt import stream_gpt_response, evaluate_interest  # Assuming your stream_gpt_response is in a file named gpt.py
from data_pipeline.OpenAIChromaUtils import chat_with_documents
from django.conf import settings
import json
import requests
from django.views import View

# http://127.0.0.1:8000/chatbot/chat/126ad854-eaba-436e-a124-ef3e3c216938/?email=ddsfg@fds.com&username=dffsdf
def chatbot_view(request, platform_key):
    # Verify if the chatbot exists by platform_key in the database
    chatbot = get_object_or_404(Chatbot, platform_key=platform_key)

    # Check if the chatbot is active
    if not chatbot.is_active:
        return render(request, 'chatbot.html', {
            'users': chatbot.users.all(),
            'logo': f"{settings.MEDIA_URL}{chatbot.logo}",
            'suspended_message': "This chatbot is inactive.",  # Pass the suspension message
        })

    # Extract additional parameters (username, email) from GET request
    username = request.GET.get('username')
    email = request.GET.get('email')
    print(username,email,"username,email")
    if username and email and chatbot.save_user_chatsession:
        # Get the existing chat session or create a new one
        chat_session, created = ChatSession.objects.get_or_create(
            chatbot=chatbot, username=username, email=email
        )

        # Load the last 10 messages from the chat history
        chat_history = chat_session.get_message_history()

        logo_url = f"{settings.MEDIA_URL}{chatbot.logo}"

        # Render the chatbot template with chat history
        return render(request, 'chatbot.html', {
            'users': chatbot.users.all(),
            'chatbot': chatbot,
            'logo': logo_url,
            'username': username,
            'email': email,
            'chat_session': chat_session,
            'chat_history': chat_history,  # Pass chat history to the template
            'suspended_message': None  # No suspension message
        })
    else:
        logo_url = f"{settings.MEDIA_URL}{chatbot.logo}"

        # Render the chatbot template with empty chat history
        return render(request, 'chatbot.html', {
            'users': chatbot.users.all(),
            'chatbot': chatbot,
            'logo': logo_url,
            'username': username,
            'email': email,
            'chat_session': [],
            'chat_history': [],  # Pass empty chat history to the template
            'suspended_message': None  # No suspension message
        })

def handle_message(request):
    if request.method == 'POST':
        try:
            # Parse the request body (JSON payload)
            data = json.loads(request.body)

            # Extract required data from the JSON body
            platform_key = data.get('platform_key')
            username = data.get('username',None)
            email = data.get('email',None)
            user_message = data.get('message')
            message_history = data.get('message_history', [])
            if not platform_key or not user_message:
                return JsonResponse({'error': 'Platform key and message are required.', 'message': 'Please provide the required information.'}, status=400)

            # Check if platform_key and chatbot are valid
            chatbot = get_object_or_404(Chatbot, platform_key=platform_key)
            
            if not chatbot.is_active:
                return JsonResponse({'error': 'This chatbot is inactive.', 'message': 'This chatbot is not currently active. Please contact support.'}, status=403)
            if username and email and chatbot.save_user_chatsession:
                print("getting message_history from db")
                # Get or create the chat session
                chat_session, created = ChatSession.objects.get_or_create(
                    chatbot=chatbot, username=username, email=email
                )

                # Get existing chat history from the session
                message_history.extend(chat_session.get_message_history())

            # message_history.append({'role': 'user', 'content': user_message})
            # Define the max response length and temperature for GPT
            max_response_length = 100  # Customize the response length
            temperature = 0.7  # Adjust the temperature as needed

            # Call the stream_gpt_response function to get the event stream from GPT
            # event_stream = stream_gpt_response(message_history, max_response_length, temperature)
            if hasattr(chatbot, 'data_pipeline') and chatbot.data_pipeline:
                print("data pipeline exist")
                # event_stream = chat_with_documents(query=user_message, db_name=str(chatbot.data_pipeline.uuid), chat_history=message_history)

                try:
                    event_stream = chat_with_documents(query=user_message, db_name=str(chatbot.data_pipeline.uuid), chat_history=message_history)
                except Exception as e:
                    print("exception of chroma occur: ", str(e))
                    event_stream = chat_with_documents(query=user_message, chat_history=message_history)

            else:
                event_stream = chat_with_documents(query=user_message, chat_history=message_history)
                
            # Collect and save the bot's response
            full_bot_response = []
            buffer = ""  # Buffer to accumulate chunks

            def stream_and_save():
                nonlocal buffer  # To modify buffer inside the function
                try:
                    for chunk in event_stream():
                        buffer += chunk  # Accumulate chunks
                        full_bot_response.append(chunk)
                        yield chunk

                    # After streaming, concatenate the full response and save it
                    full_response_text = ''.join(full_bot_response)
                    if chatbot.save_user_chatsession and username and email:
                        # Save the chat session only if the chatbot has allowed it
                        chat_session.add_message({'role': 'user', 'content': user_message})
                        chat_session.add_message({'role': 'assistant', 'content': full_response_text})
                        chat_session.save()

                except Exception as e:
                    yield f"Error streaming response: {str(e)}"

            # Return the streaming response
            return StreamingHttpResponse(stream_and_save(), content_type='text/event-stream')

        except KeyError as e:
            return JsonResponse({'error': f'Missing required parameter: {str(e)}', 'message': 'A required field is missing. Please check and try again.'}, status=400)

        except Exception as e:
            return JsonResponse({'error': f'An error occurred: {str(e)}', 'message': 'An unexpected error occurred. Please try again later.'}, status=500)

    else:
        return JsonResponse({'error': 'Invalid request method. Only POST is allowed.', 'message': 'Invalid request method. Please use POST.'}, status=400)

def form_view(request, platform_key):
    form = get_object_or_404(Form, chatbot__platform_key=platform_key)
    
    if request.method == 'POST':
        score = 0
        total_questions = form.questions.count()

        for question in form.questions.all():
            user_answer = request.POST.get(f'question_{question.id}')
            if question.is_correct(user_answer):
                score += 1
        
        return JsonResponse({'score': score, 'total_questions': total_questions})

    return render(request, 'form_questions.html', {'form': form})

def form_detail_view(request, platform_key):
    if request.method != 'GET':
        return HttpResponseNotAllowed(['GET'])
    
    try:
        form = Form.objects.get(chatbot__platform_key=platform_key)
        questions = form.questions.all()
        
        form_data = {
            'id': form.id,
            'title': form.title,
            'questions': [
                {'id': question.id, 'text': question.text} for question in questions
            ],
            'whatsapp_link': form.whatsapp_link
        }
        
        return JsonResponse(form_data, status=200)
    
    except Form.DoesNotExist:
        return JsonResponse({'error': 'Form not found'}, status=404)

def evaluate_interest_api(request):
    if request.method != 'POST':
        return HttpResponseNotAllowed(['POST'])

    try:
        # Parse JSON data from the request body
        data = json.loads(request.body)
        questions_replies = data.get('questions_replies', [])
        platform_key = data.get('platform_key', None)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)

    # Check if questions and platform key are provided
    if not questions_replies or not platform_key:
        return JsonResponse({'error': 'Invalid data. Make sure questions and replies are provided and match in length.'}, status=400)

    try:
        # Fetch the form associated with the platform key
        form = Form.objects.get(chatbot__platform_key=platform_key)

        # Fetch all questions associated with this form
        form_questions = {q.id: q for q in form.questions.all()}

        # Iterate over questions_replies and append the correct answer from the form
        for qr in questions_replies:
            question_id = qr.get('question_id')
            if question_id in form_questions:
                correct_answer = form_questions[question_id].answer
                qr['correct_answer'] = correct_answer  # Append the correct answer to the question reply

        # Optionally, evaluate interest or perform any additional processing
        results = evaluate_interest(questions_replies)

        return JsonResponse(results, status=200)

    except Form.DoesNotExist:
        return JsonResponse({'error': 'Form not found for the provided platform key.'}, status=404)

    except Exception as e:
        return JsonResponse({'error': f'Error evaluating interest: {str(e)}'}, status=500)
    
class HubSpotEmailView(View):
    def post(self, request):
        # Parse the JSON body
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        
        # Extract the email and lifecyclestage from the JSON data
        email = data.get('email')
        lifecyclestage = settings.HUBSPOT_LIFECYCLE_STAGE  # Default to 'subscriber' if not provided

        # Check if email is provided
        if not email:
            return JsonResponse({'error': 'Email is required'}, status=400)

        # HubSpot API endpoint
        url = "https://api.hubapi.com/crm/v3/objects/contacts"

        # Define headers, including Bearer token for authorization
        headers = {
            "Authorization": f"Bearer {settings.HUBSPOT_ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }

        # Define the contact data payload
        contact_data = {
            "properties": {
                "email": email,
                "lifecyclestage": lifecyclestage
            }
        }

        # Send the POST request to HubSpot API
        try:
            response = requests.post(url, headers=headers, json=contact_data)
            
            # Check for success status code (201 Created)
            if response.status_code == 201:
                return JsonResponse({'success': 'Contact created successfully'}, status=201)
            else:
                # Return error details from HubSpot
                return JsonResponse({'error': response.json()}, status=response.status_code)
        except requests.RequestException as e:
            # Handle any request-related errors
            return JsonResponse({'error': str(e)}, status=500)
