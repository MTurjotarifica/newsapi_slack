import os
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from slackeventsapi import SlackEventAdapter
from flask import Flask, request, make_response
from dotenv import load_dotenv
import requests
import json


import pandas as pd
from openpyxl import load_workbook
from newsdataapi import NewsDataApiClient
import datetime
import deepl

load_dotenv()

def translate_text(text):
        translator = deepl.Translator('bb771f1c-93f7-4ee5-ceed-74dad6649600')
        result = translator.translate_text(text, target_lang='EN-US')
        return result.text

# Initialize the Flask app and the Slack app
app = Flask(__name__)
slack_app = App(
    token=os.environ["SLACK_BOT_TOKEN"],
    signing_secret=os.environ["SLACK_SIGNING_SECRET"]
)

client = slack_app.client

# Handle incoming slash command requests
@app.route("/slack/command", methods=["POST"])
def handle_slash_command():
    # Parse the command and its parameters from the request
    command = request.form.get("command")
    text = request.form.get("text")
    channel_id = request.form.get("channel_id")

    # Execute the appropriate function based on the command
    if command == "/example":
        client.chat_postMessage(channel=channel_id, text="it worksssss! max date")
        response_text = handle_example_command(text)
    else:
        response_text = "Unknown command: {}".format(command)

    # Send the response to the channel
#     slack_app.client.chat_postMessage(channel=response_url, text=response_text)


    # Return an empty response to Slack
    return make_response("", 200)

# Add a route for the /hello command
@app.route("/hello2", methods=["POST"])
def handle_hello_request():
    data = request.form
    channel_id = data.get('channel_id')
    # Execute the /hello command function
    client.chat_postMessage(response_type= "in_channel", channel=channel_id, text=" 2nd it works!33!" )
    return "Hello world1" , 200

@app.route("/newsapi", methods=["POST"])
def newsapi():
    data = request.form
    channel_id = data.get('channel_id')
    text = data.get('text')  # Get the query from the slash command

    today = datetime.datetime.now().date()

    api = NewsDataApiClient(apikey="pub_205194b814f4b3a8ef344988313fe445954eb")
    response = api.news_api(q=text, country='de')  # Use the query in the API call
    articles = response['results']

    article_list = []
    for article in articles:
        pub_date = datetime.datetime.strptime(article['pubDate'], '%Y-%m-%d %H:%M:%S').date()
        if (today - pub_date).days < 3:
            category = [c.lower() for c in article.get('category', [])]  # Get the category key and convert each category to lowercase
            if 'sports' not in category:
                # Check if 'description' key exists and if it is a string before calling translate_text()
                description = article.get('description', None)
                description_translated = translate_text(description) if description else ''
                    
                # Check if 'content' key exists and if it is a string before calling translate_text()
                content = article.get('content', None)
                content_translated = translate_text(content) if content else ''
                
                # Check if the keyword 'Telekom Baskets Bonn' is in the content or description
                if 'Telekom Baskets Bonn' not in content_translated and 'Telekom Baskets Bonn' not in description_translated:
                    article_dict = {'Title': translate_text(article['title']), 
                                    'Link': article['link'], 
                                    'Keywords': article['keywords'], 
                                    'Creator': article['creator'], 
                                    'Description': description_translated, 
                                    'Content': content_translated, 
                                    'PubDate': article['pubDate'], 
                                    'Image URL': article['image_url'], 
                                    'Category': category}
                    article_list.append(article_dict)

    df_new = pd.DataFrame(article_list)

    # Send the new links and translated text to Slack
    for index, row in df_new.iterrows():
        link = row['Link']
        description = row['Description']
        content = row['Content']
        title = translate_text(row['Title'])

        # Choose the text to send based on whether content or description is available
        if content:
            text_to_send = content
        elif description:
            text_to_send = description
        else:
            text_to_send = title

        try:
            response = client.chat_postMessage(
                channel=channel_id,
                text=f"• <{link}|{title}>\n{text_to_send}",
                unfurl_links=False,
            )
        except SlackApiError as e:
            print("Error sending message to Slack: {}".format(e))
            

# Start the Slack app using the Flask app as a middleware
handler = SlackRequestHandler(slack_app)

@app.route("/slack/events", methods=["POST"])
def slack_events():
    return handler.handle(request)

if __name__ == "__main__":
    app.run(debug=True)

