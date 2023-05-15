from flask import Flask, request, make_response
import json
from slack_bolt import App
from slackeventsapi import SlackEventAdapter
from slack_sdk.errors import SlackApiError
from slack_bolt.adapter.flask import SlackRequestHandler
from slack_sdk import WebClient
import os
import openai
from dotenv import load_dotenv 
from pathlib import Path   

# env_path = Path('.') / '.env'
# load_dotenv(dotenv_path = env_path)

load_dotenv()

# Initialize the Flask app and the Slack app
app = Flask(__name__)
slack_app = App(
    token=os.environ["SLACK_BOT_TOKEN"],
    signing_secret=os.environ["SLACK_SIGNING_SECRET"]
)

slack_client = slack_app.client
client = slack_app.client
# Set up the OpenAI API key
openai.api_key = os.environ["OPENAI_API_KEY"]

@app.route('/slack/interactive-endpoint', methods=['GET','POST'])
def interactive_trigger():
    data = request.form
    data2 = request.form.to_dict()
    # user_id = data.get('user_id')
    channel_id = json.loads(data2['payload'])['container']['channel_id']
    # text = json.loads(data2['payload'])['actions'][0]['value']

    # response_url = json.loads(data2['payload'])['response_url']
    # actions = data.get("actions")
    # actions_value = data.get("actions.value")
    action_id = json.loads(data2['payload'])['actions'][0]['action_id']
    
    if action_id == "newsapi":
        # Get the text of the user's command
        command_text = json.loads(data2['payload'])['actions'][0]['value']
        # Call the OpenAI API to generate a response
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=command_text,
            max_tokens=60,
            n=1,
            stop=None,
            temperature=0.8,
        )
        
        # Send the generated text back to Slack
        try:
            # Get the channel ID from the request
            channel_id = request.form["channel_id"]

            # Use the Slack API client to send a message to the channel
            client.chat_postMessage(
                channel=channel_id,
                text=response.choices[0].text
            )

        except SlackApiError as e:
            # Print any errors to the console
            print(f"Error sending message: {e}")

        # Return an empty response
        return make_response("", 200)
        #return make_response(json.dumps(response_data), 200)   


        
# Define the slash command handler
@app.route("/chatgpt", methods=["POST"])
def handle_chatgpt():
    data = request.form
    channel_id = data.get('channel_id')

    #this creates the text prompt in slack block kit
    gptquery = [
        {
           "type": "divider"
           },
        {
            "dispatch_action": True,
            "type": "input",
            "element": {
                "type": "plain_text_input",
                "action_id": "chatgpt"
            },
            "label": {
                "type": "plain_text",
                "text": "Please type the keyword for the Chatgpt",
                "emoji": True
            }
        }
    ]

    client.chat_postMessage(channel=channel_id, 
                                        text="Query:  ",
                                        blocks = gptquery
                                        )

    #returning empty string with 200 response
    return 'GPT works', 200

    

# Add a route for the /hello command
@app.route("/hello3", methods=["POST"])
def handle_hello_request():
    data = request.form
    channel_id = data.get('channel_id')
    # Execute the /hello command function
    client.chat_postMessage(response_type= "in_channel", channel=channel_id, text=" 2nd it works!33!" )
    return "Hello world3" , 200



# Start the Slack app using the Flask app as a middleware
handler = SlackRequestHandler(slack_app)

@app.route("/slack/events", methods=["POST"])
def slack_events():
    return handler.handle(request)


# Run the Flask app
if __name__ == "__main__":
    # app.run(port=5001)
    app.run(debug=True)
