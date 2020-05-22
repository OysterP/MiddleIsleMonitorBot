import requests
import re
from bs4 import BeautifulSoup
from telegram.ext import Updater, InlineQueryHandler, CommandHandler, run_async
import time
import logging
from tinydb import TinyDB, Query

def pollAldiSite(url, htmlType, htmlClass, product):
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')
    priceField = soup.find_all(htmlType, class_=htmlClass)[0].get_text()
    #m = re.search(".*Product no longer available.*",priceField)
    if not re.search(".*Product no longer available.*", priceField.strip('\r\n\t ')):
        return priceField.strip('\r\n\t ')

@run_async
def botIt(update,context):
    #something
    chat_id = update.message.chat_id
    if len(context.args) == 0:
        context.bot.send_message(chat_id,"No URL provided")
        return
    url = context.args[0]
    if not re.match('(^http[s]?:\/{2})|(^\/{1,2})',url):
        context.bot.send_message(chat_id,"URL "+url+" not valid")
        return
    productName = " ".join(context.args[1:])
    if not productName:
        html = requests.get(url)
        productName = BeautifulSoup(html.content, 'html.parser').h1.get_text()
    context.bot.send_message(chat_id,"Don't worry, I'll let you know when "+productName+" is back available.")

    #url = "https://www.aldi.co.uk/ferrex-patio-and-wall-cleaner/p/090494322104400"
    #url = "https://www.aldi.co.uk/ferrex-18v-cordless-mitre-saw/p/021106302710800"
    # productName = 'Ferrex Patio And Wall Cleaner'
    #productName = 'Ferrex 18v cordless mitre saw'
    while True:
        result = pollAldiSite(url, 'span', 'product-price__value',
                        productName)
        if result:
            message = "The "+productName+" is now available at Aldi for £"+result \
                            +"!\n"+url
            context.bot.send_message(chat_id,message)
            break
        else:
            # context.bot.send_message(chat_id,"No die")
            time.sleep(600)

      
    

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