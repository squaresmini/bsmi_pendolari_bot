import trenitalia_api_caller
from telegram.ext import Updater,CommandHandler
import logging
import os

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',level=logging.INFO)
log = logging.getLogger("bsmi_pendolari_bot")


START_MESS='''
Questo bot ti permette di sapere facilmente lo stato del prossimo treno Brescia-Milano (durante la mattina) e Milano-Brescia (nel pomeriggio).

Lista comandi:
/status : per sapere lo stato del prossimo treno
/status <num_treno> : status di un treno particolare (deve passare da BS o Milano)
'''

def start(update, context):
    log.info("Starting start command for chat " + str(update.effective_chat.id)+" with "+update.effective_user.name)
    context.bot.send_message(chat_id=update.effective_chat.id, text="Ciao "+update.effective_user.name+"!"+START_MESS)


def status(update, context):
    log.info("Starting status command for chat " + str(update.effective_chat.id) +" with "+update.effective_user.name)
    if context.args:
        train_number = context.args[0]
    else:
        train_number = trenitalia_api_caller.calculate_next_train()

        log.info("Train number " + train_number)

    try:
        train_number,station_id=trenitalia_api_caller.retrieve_train(train_number)
        log.info("Train number evaluated: " + train_number + " from station "+station_id)
        status_mess = trenitalia_api_caller.get_status_mess(station_id,train_number)
        log.info("Status correctly calculated")
    except Exception as e:
        log.error("An exception occured",e)
        status_mess = str(e)

    context.bot.send_message(chat_id=update.effective_chat.id, text=status_mess)


def notify_train(context):
    context.bot.send_message


def main():
    updater = Updater(token=os.environ.get('BOTKEY'), use_context=True)
    dispatcher = updater.dispatcher

    start_handler = CommandHandler('start', start)
    status_handler = CommandHandler('status', status)

    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(status_handler)

    updater.start_polling()


if __name__ == '__main__':
    main()