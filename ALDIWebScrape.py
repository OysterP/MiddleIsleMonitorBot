import requests
import re
from bs4 import BeautifulSoup
from telegram.ext import Updater, InlineQueryHandler, CommandHandler, run_async
import time
import logging
from tinydb import TinyDB, Query
import json

# processes json data contained in a scripts element of site
def scrapeAldiSite(page):
    soup = BeautifulSoup(page.content, 'html.parser')
    # Grab Json data contianed hidden within body of site.
    siteData = json.loads(str(soup.find("script",type="application/ld+json").contents[0]))
    # return results only if item can be ordered online.
    if siteData['offers']['availability'] in ('InStock','PreOrder'):
        return (siteData['offers']['price'],siteData['offers']['availability'])

@run_async
def botIt(update,context):
    # Grab requestor's chat ID, ready to start conversation
    chat_id = update.message.chat_id
    
    # URL validation
    if len(context.args) == 0:
        context.bot.send_message(chat_id,"No URL provided")
        return
    url = context.args[0]
    if not re.match('(^http[s]?:\/{2})|(^\/{1,2})',url):
        context.bot.send_message(chat_id,"URL "+url+" not valid")
        return
    
    productName = " ".join(context.args[1:])
    # Get product name from first h1 HTML field of page if not specified by user.
    if not productName:
        html = requests.get(url)
        productName = BeautifulSoup(html.content, 'html.parser').h1.get_text()
    context.bot.send_message(chat_id,"Don't worry, I'll let you know when "+productName+" is back available.")

    while True:
        # Grab latest content from site
        html = requests.get(url)
        result = scrapeAldiSite(html)
        # If a result is returned, notify user
        if result:
            message = "The "+productName+" is now available at Aldi for £"+result[0] \
                            +"!\n"+url
            context.bot.send_message(chat_id,message)
            break
        else:
            # Give 5 mins before polling again for availability
            time.sleep(300)
            
def main():
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                     level=logging.INFO)
    teleUpdater = Updater('***REMOVED***', use_context=True)
    dp = teleUpdater.dispatcher
    dp.add_handler(CommandHandler('start',botIt))
    dp.add_handler(CommandHandler('check',botIt))
    teleUpdater.start_polling()
    teleUpdater.idle()


if __name__ == '__main__':
    main()