import requests
import re
from bs4 import BeautifulSoup
import telegram
from telegram.ext import Updater, InlineQueryHandler, CommandHandler, run_async
from telegram.error import (TelegramError, Unauthorized, BadRequest, 
                            TimedOut, ChatMigrated, NetworkError)
import time
import logging
from tinydb import TinyDB, Query
import json
from configparser import ConfigParser
import threading
import random

def monitor(bot):
    logging.info("Starting monitoring loop")
    while True:
        logging.info("Grabbing all records from DB")
        records = db.all()
        logging.info("Recursing through records")
        for record in records:
            # Grab latest content from site
            html = requests.get(record['url'])
            result = scrapeAldiSite(html)
            # If a result is returned, notify user
            if result:
                message = "The "+record['productName']+" is now available at Aldi for £"+result[0] \
                                +"!\n"+record['url']
                try:
                    bot.send_message(record['chat_id'],message)
                except (Unauthorized,BadRequest):
                    db.remove((Query().chat_id == record['chat_id']))
                db.remove((Query().chat_id == record['chat_id']) & (Query().url == record['url']))
            time.sleep(1)
            time.sleep(1)
        logging.info("Monitor pausing for 60 seconds")
        time.sleep(60)

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
    
    # Check if already part of DB.
    qry = Query()
    if len(db.search((qry.chat_id == chat_id) & (qry.url == url))):
        context.bot.send_message(chat_id,"URL "+url+" is already being monitored for you.")
        return
    
    # Build regex for validating provided URL against supported sites
    supportedSites=('aldi.co.uk',)
    siteRegex=""
    for site in supportedSites:
        if(siteRegex):
            siteRegex+='|'
        siteRegex+='(.*'+site+'/.*)'
    # exit if not a currently supported site
    if not re.match(siteRegex,url):
        context.bot.send_message(chat_id,"Website not currently supported")
        context.bot.send_message(chat_id,"Currently supported sites are:\r\n"+("\r\n".join(supportedSites)))
        return
    
    productName = " ".join(context.args[1:])
    # Get product name from first h1 HTML field of page if not specified by user.
    if not productName:
        html = requests.get(url)
        productName = BeautifulSoup(html.content, 'html.parser').h1.get_text()
    
    # Send confirmation to user
    context.bot.send_message(chat_id,"Don't worry, I'll let you know when "+productName+" is back available.")
    
    # Add entry into DB to be monitored.
    db.insert({'chat_id': chat_id,'url': url, 'productName': productName})

            
def main():
    
    # Intiialise logging
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                     level=logging.INFO)
    
    # Read config file
    config = ConfigParser()
    config.read('config.ini')
    
    # Initialise DB for use globally
    global db
    db = TinyDB(config.get('DB','file'))
    
    # create basic API bot for performing messages without context
    token = config.get('Bot','token')
    bot = telegram.Bot(token)
    # Send bot to the montitor routine to allow posting messages when a result has returned.
    monitorThread = threading.Thread(target=monitor,args=(bot,))
    monitorThread.start()
    # Below used to listen for messages and take action asyncronously via the botIt function
    teleUpdater = Updater(token, use_context=True)
    dp = teleUpdater.dispatcher
    dp.add_handler(CommandHandler('start',botIt))
    dp.add_handler(CommandHandler('check',botIt))
    teleUpdater.start_polling()
    teleUpdater.idle()


if __name__ == '__main__':
    main()