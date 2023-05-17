from dotenv import load_dotenv 
import openai
import os

import deepl

from newsapi.newsapi_client  import NewsApiClient
from datetime import datetime as dt
from datetime import timedelta as delta

load_dotenv()
# Set up the OpenAI API key
openai.api_key = os.environ["OPENAI_API_KEY"]

# Define NEWS API key

api = NewsApiClient(api_key=os.environ["NEWS_API_KEY"])

def chatgpt(content_list):
    summaries = []

    # Iterate over the content
    for content in content_list:
        # Generate a prompt combining the content and a specific instruction for summary
        prompt = f"Summarize the following content:\n\n{content}"

        # Call the OpenAI API to generate a response
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=500,
            n=1,
            stop=None,
            temperature=0.8,
        )
        # Extract the generated summary from the API response
        summary = response.choices[0].text.strip()
        summaries.append(summary)

    return summaries

def translate_text(text):
    translator = deepl.Translator(os.environ['DEEPL_API'])
    result = translator.translate_text(text, target_lang='EN-US')
    return result.text

def newsapi_query():
    # Get last two day's date
    yesterday = (dt.now()-delta(days=1)).strftime("%Y-%m-%d")
    two_days_ago = (dt.now()-delta(days=2)).strftime("%Y-%m-%d")

    # Retrieve News for last two Days
    telco = api.get_everything(q='o2 OR vodafone OR telekom',language='de',from_param=two_days_ago,to=yesterday)
    
    # Extract URLs from the telco dictionary
    urls = [article['url'] for article in telco['articles']]
    # Extract Titles from the telco dictionary
    titles = [article['title'] for article in telco['articles']]
    # Extract Titles from the telco dictionary
    descriptions = [article['description'] for article in telco['articles']]

    # Limit the number of URLs and titles to 5
    urls = urls[:10]
    titles = titles[:10]
    descriptions = descriptions[:10]

    return urls, titles, descriptions


def newsgpt(urls, titles, descriptions):
    # Create an empty list to store the translated content
    translated_list = []

    # Iterate over the content
    for content in descriptions:
        if content:
            translated_text = translate_text(content)
            translated_list.append(translated_text)

    # Call the `chatgpt` function with the `content_list`
    summary_list = chatgpt(translated_list)

    #For collecting translated title
    title_list=[]
    for title in titles:
        if title:
            translated_title = translate_text(title)
            title_list.append(translated_title)     
    
    return title_list, translated_list


