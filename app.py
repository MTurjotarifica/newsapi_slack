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
@app.route('/slack/interactive-endpoint', methods=['GET','POST'])
def interactive_trigger():

    data = request.form
    data2 = request.form.to_dict()
    user_id = data.get('user_id')
    channel_id = json.loads(data2['payload'])['container']['channel_id']
    text = data.get('text')
    print (text)
    response_url = json.loads(data2['payload'])['response_url']
    actions = data.get("actions")
    actions_value = data.get("actions.value")
    action_id = json.loads(data2['payload'])['actions'][0]['action_id']

    
        
    if action_id == "newsapi":
      today = datetime.datetime.now().date()

      api = NewsDataApiClient(apikey="pub_205194b814f4b3a8ef344988313fe445954eb")
      response = api.news_api(q='o2 OR vodafone OR telekom', country='de')
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
                                      'Content': content_translated, 
                                      'Description': description_translated, 
                                      'PubDate': article['pubDate'], 
                                      'Image URL': article['image_url'], 
                                      'Category': category}
                      article_list.append(article_dict)


      df_new = pd.DataFrame(article_list)

      # Send the new links and translated text to Slack
      for index, row in df_new.iterrows():
          link = row['Link']
          content = row['Content']
          description = row['Description']
          title = translate_text(row['Title'])

          if content:
              # Send the content if it exists
              message = content
          elif description:
              # Send the description if content does not exist but description exists
              message = description
          else:
              # Send the title if neither content nor description exists
              message = title

          try:
              response = client.chat_postMessage(
                  channel=channel_id,
                  text=f"• <{link}|{title}>\n{message}\n",
                  unfurl_links=False,
              )
          except SlackApiError as e:
              print("Error sending message to Slack: {}".format(e))
              
      return text, 200
      
        
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

    #this creates the text prompt in slack block kit
    newsapiquery = [
        {
           "type": "divider"
           },
        {
            "dispatch_action": True,
            "type": "input",
            "element": {
                "type": "plain_text_input",
                "action_id": "newsapi"
            },
            "label": {
                "type": "plain_text",
                "text": "Please type the keyword for the visualization ",
                "emoji": True
            }
        }
    ]

    client.chat_postMessage(channel=channel_id, 
                                        text="Query:  ",
                                        blocks = newsapiquery
                                        )

    #returning empty string with 200 response
    return 'newsapi works', 200
        
# Start the Slack app using the Flask app as a middleware
handler = SlackRequestHandler(slack_app)

@app.route("/slack/events", methods=["POST"])
def slack_events():
    return handler.handle(request)

if __name__ == "__main__":
    app.run(debug=True)

