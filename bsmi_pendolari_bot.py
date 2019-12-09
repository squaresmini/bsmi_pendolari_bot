import trenitalia_api_caller
from telegram.ext import Updater,CommandHandler


def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Ciao "+update.effective_user.name+"! Digita /status per sapere lo stato del prossimo treno")


def status(update, context):
    if context.args:
        train_number = context.args[0]
    else:
        train_number = trenitalia_api_caller.calculate_next_train()

    try:
        train_number,station_id=trenitalia_api_caller.retrieve_train(train_number)
        status_mess = trenitalia_api_caller.get_status_mess(station_id,train_number)
    except Exception as e:
        status_mess = str(e)

    context.bot.send_message(chat_id=update.effective_chat.id, text=status_mess)


def notify_train(context):
    context.bot.send_message


def main():
    updater = Updater(token='907871825:AAE38Zk9qcc2fdxlS2kGW9EAddsWgOmuMxw', use_context=True)
    dispatcher = updater.dispatcher

    start_handler = CommandHandler('start', start)
    status_handler = CommandHandler('status', status)

    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(status_handler)

    updater.start_polling()


if __name__ == '__main__':
    main()