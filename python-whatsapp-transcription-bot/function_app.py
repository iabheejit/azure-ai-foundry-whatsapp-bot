import azure.functions as func
import logging
import os
import json
import requests
from openai import AzureOpenAI

app = func.FunctionApp()

@app.route(route="WhatsAppTranscriptionBot", auth_level=func.AuthLevel.ANONYMOUS)
def WhatsAppTranscriptionBot(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request')
    
    if req.method == 'POST':
        return(handle_message(req))
    else:
        return(verify(req))

def verify(req):
    logging.info("verify - Start")
    verify_token = os.environ["VERIFY_TOKEN"]
    
    mode = req.params.get("hub.mode")
    token = req.params.get("hub.verify_token")
    challenge = req.params.get("hub.challenge")
    
    if mode and token:
        if mode == "subscribe" and token == verify_token:
            return func.HttpResponse(challenge, status_code=200)
        else:
            return func.HttpResponse("Verification failed", status_code=403)
    else:
        return func.HttpResponse("Missing parameters", status_code=400)

def handle_message(req):
    try:
        body = req.get_json()
        
        # Handle WhatsApp status updates
        if (body.get("entry", [{}])[0]
            .get("changes", [{}])[0]
            .get("value", {})
            .get("statuses")):
            return func.HttpResponse("OK", status_code=200)

        if is_valid_whatsapp_message(body):
            process_whatsapp_message(body)
            return func.HttpResponse("OK", status_code=200)
        else:
            return func.HttpResponse(
                "Not a WhatsApp API event",
                status_code=404
            )
    except Exception as e:
        logging.error(f"Error processing message: {str(e)}")
        return func.HttpResponse(
            "Error processing message",
            status_code=500
        )

def is_valid_whatsapp_message(body):
    return (
        body.get("object")
        and body.get("entry")
        and body["entry"][0].get("changes")
        and body["entry"][0]["changes"][0].get("value")
        and body["entry"][0]["changes"][0]["value"].get("messages")
        and body["entry"][0]["changes"][0]["value"]["messages"][0]
    )

def process_whatsapp_message(body):
    wa_id = body["entry"][0]["changes"][0]["value"]["contacts"][0]["wa_id"]
    
    # Security check
    if wa_id != os.environ["RECIPIENT_WAID"]:
        logging.error("Unauthorized user")
        return

    message = body["entry"][0]["changes"][0]["value"]["messages"][0]
    
    if "text" in message:
        text = "Hi, I am an AI assistant. I can help you transcribe WhatsApp voice messages."
        data = get_text_message_input(wa_id, text)
        send_message(data)
    elif "audio" in message:
        media_id = message["audio"]["id"]
        text = "Transcribing your message..."
        data = get_text_message_input(wa_id, text)
        send_message(data)
        handle_voice_message(media_id, wa_id)

def get_text_message_input(recipient, text):
    return json.dumps({
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": recipient,
        "type": "text",
        "text": {"preview_url": False, "body": text}
    })

def send_message(data):
    headers = {
        "Content-type": "application/json",
        "Authorization": f"Bearer {os.environ['ACCESS_TOKEN']}"
    }
    
    url = f"https://graph.facebook.com/{os.environ['VERSION']}/{os.environ['PHONE_NUMBER_ID']}/messages"
    return send_post_request_to_graph_facebook(url, data, headers)

def handle_voice_message(media_id, wa_id):
    headers = {
        "Authorization": f"Bearer {os.environ['ACCESS_TOKEN']}"
    }
    
    url = f"https://graph.facebook.com/{os.environ['VERSION']}/{media_id}"
    response = send_get_request_to_graph_facebook(url, headers)
    
    response_json = json.loads(response.text)
    download_url = response_json["url"]
    
    data = requests.get(download_url, headers=headers, allow_redirects=True)
    
    local_file_name = '/tmp/voice_message.ogg'
    with open(local_file_name, 'wb') as file:
        file.write(data.content)
    
    transcribed_text = transcribe_file(local_file_name)
    if transcribed_text:
        data = get_text_message_input(wa_id, f"*Transcription:*\n{transcribed_text}")
        send_message(data)

def transcribe_file(audio_file):
    client = AzureOpenAI(
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
    )
    
    with open(audio_file, "rb") as audio:
        transcription = client.audio.transcriptions.create(
            file=audio,
            model="whisper-1"
        )
    
    return transcription.text

def send_post_request_to_graph_facebook(url, data, headers):
    try:
        response = requests.post(url, data=data, headers=headers, timeout=10)
        response.raise_for_status()
        return response
    except requests.RequestException as e:
        logging.error(f"Request failed: {e}")
        raise

def send_get_request_to_graph_facebook(url, headers):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response
    except requests.RequestException as e:
        logging.error(f"Request failed: {e}")
        raise