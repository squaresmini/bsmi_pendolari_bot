import bsmi_pendolari_bot,json
from telegram.ext import Updater,CommandHandler

def main():
    with open('botconfig.json') as json_data_file:
        config = json.load(json_data_file)


    updater = Updater(token=config['botkey'], use_context=True)
    updater.start_webhook(listen='0.0.0.0',
                          port=config['port'],
                          url_path=config['botkey'],
                          key='private.key',
                          cert='cert.pem',
                          webhook_url='https://'+config['host']+ ':' + config['port']+ '/' + config['botkey'])
    dispatcher = updater.dispatcher

    start_handler = CommandHandler('start', start)
    status_handler = CommandHandler('status', status)

    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(status_handler)

    updater.start_polling()


if __name__ == '__main__':
    main()