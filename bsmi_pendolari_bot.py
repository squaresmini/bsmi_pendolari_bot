import trenitalia_api_caller
from telegram.ext import BaseFilter, Filters, MessageHandler, Updater, CommandHandler, ConversationHandler, \
    CallbackQueryHandler
import logging
import os
import logging.config
from telegram import InlineKeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, ReplyKeyboardMarkup

dir_path = os.path.dirname(os.path.realpath(__file__))
logging.config.fileConfig(dir_path + '/logging.conf')

log = logging.getLogger("bsmi_pendolari_bot")

TRAIN_MORN, UPDATE_MINS_MORN, TRAIN_EVE, UPDATE_MINS_EVE = range(4)

START_MESS = '''
Questo bot ti permette di sapere facilmente lo stato del prossimo treno Brescia-Milano (durante la mattina) e Milano-Brescia (nel pomeriggio).

Lista comandi:
/status : per sapere lo stato del prossimo treno
/status <num_treno> : status di un treno particolare (deve passare da BS o Milano)
'''

numeric_kb = [['10', '15', '20', '25'],
              ['30', '35', '40', '45'],
              ['40', '45', '50', '55'],
              ['60']]
numeric_markup = ReplyKeyboardMarkup(numeric_kb, one_time_keyboard=True)


def start(update, context):
    log.info("Starting start command for chat " + str(update.effective_chat.id) + " with " + update.effective_user.name)
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text="Ciao " + update.effective_user.name + "!" + START_MESS)


def button(update, context):
    query = update.callback_query
    query.edit_message_text(text="Hai scelto: {}".format(query.data))


def status(update, context):
    log.info(
        "Starting status command for chat " + str(update.effective_chat.id) + " with " + update.effective_user.name)
    if context.args:
        train_number = context.args[0]
    else:
        train_number = trenitalia_api_caller.calculate_next_train()

    if not train_number:
        status_mess = "Servizio terminato, ci vediamo domani!"
    else:
        log.info("Train number " + train_number)

        try:
            train_number, station_id = trenitalia_api_caller.retrieve_train(train_number)
            log.info("Train number evaluated: " + train_number + " from station " + station_id)
            status_mess = trenitalia_api_caller.get_status_mess(station_id, train_number)
            log.info("Status correctly calculated")
        except Exception as e:
            log.error("An exception occured", e)
            status_mess = str(e)

    context.bot.send_message(chat_id=update.effective_chat.id, text=status_mess)


def select_train_morning(update, context):
    type = 'morning'
    return select_train(update, context, type)


def select_train_evening(update, context):
    type = 'evening'
    return select_train(update, context, type)


def select_train(update, context, type):
    if type == 'morning':
        train_list = trenitalia_api_caller.TRAIN_MORN_LIST
        keyname = 'train_morning'
        nextstep = UPDATE_MINS_MORN
    else:
        train_list = trenitalia_api_caller.TRAIN_EVE_LIST
        keyname = 'train_evening'
        nextstep = UPDATE_MINS_EVE

    train = update.message.text
    log.info("Chosen train = "+train)
    if train in [a[0] for a in train_list]:
        context.user_data[keyname] = (train, 30)
        update.message.reply_text(
            "Vada per il treno {}! Quanti minuti prima vuoi cominciare a ricevere"
            " aggiornamenti riguardo il treno? (0-59 minuti, oppure /default "
            "se vanno bene 30 minuti)".format(train),
            reply_markup=numeric_markup)
        return nextstep
    else:
        if keyname in context.user_data:
            del context.user_data[keyname]

        update.message.reply_text("Operazione annullata, treno non in lista")
        return ConversationHandler.END


def mins_morning(update, context):
    type = 'morning'
    return select_mins(update, context, type)


def mins_evening(update, context):
    type = 'evening'
    return select_mins(update, context, type)


def calculate_keyboard_markup(train_list):
    keyboard = [[t[0] for t in train_list][k:k + 3] for k in range(0, len(train_list), 3)]
    return ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)


def select_mins(update, context, type, mins=None):
    if not mins:
        mins = update.message.text
        log.info("Mins = "+mins)

    if type == 'morning':
        keyname = 'train_morning'
    else:
        keyname = 'train_evening'

    if keyname in context.user_data:
        context.user_data[keyname] = (context.user_data[keyname][0], int(mins))

    if type == 'morning':
        keyboard = calculate_keyboard_markup(trenitalia_api_caller.TRAIN_EVE_LIST)
        update.message.reply_text(
            "Ok! Riceverai notifiche per il treno del mattino {} minuti prima!\nImpostiamo il treno della sera: "
            "Per quale treno vuoi ricevere aggiornamenti?".format(mins),
            reply_markup=keyboard)
        return TRAIN_EVE
    else:
        notification_status = get_notification_status(context)

        message = "Ok! Ricapitolando, hai impostato queste notifiche:{}".format(notification_status)

        update.message.reply_text(message)
        return ConversationHandler.END


def get_notification_status(context):
    notification_status = ""
    for type, label, city in [('train_morning', 'mattina', 'Brescia'), ('train_evening', 'sera', 'Milano')]:
        if type in context.user_data:
            num, mins = context.user_data[type]
            notification_status += "\nPer la {} ti notificherò il treno {}" \
                                   " da {} minuti prima della partenza da {}".format(label, num, str(mins), city)
        else:
            notification_status += "\nNessun treno seguito la {}".format(label)

    return notification_status


def defaultmins_morn(update, context):
    return select_mins(update, context, 'morning', 30)


def defaultmins_eve(update, context):
    return select_mins(update, context, 'evening', 30)


def set_alert(update, context):
    keyboard = calculate_keyboard_markup(trenitalia_api_caller.TRAIN_MORN_LIST)
    update.message.reply_text(
        "Impostiamo il treno della mattina: "
        "Per quale treno vuoi ricevere aggiornamenti?\n/skip per passare a quello della sera\n"
        "/cancel per interrompere il processo)",
        reply_markup=keyboard)
    return TRAIN_MORN


def cancel(update, context):
    user = update.message.from_user
    log.info("User %s canceled the conversation.", user.first_name)
    delete_notifications(update, context)

    update.message.reply_text('Nessuna notifica inserita',
                              reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END


def alert_status(update,context):
    status(update,context)

def delete_notifications(update, context):
    user_data = context.user_data
    is_deleted = False
    if 'train_morning' in user_data:
        is_deleted = True
        del user_data['train_morning']
    if 'train_evening' in user_data:
        is_deleted = True
        del user_data['train_evening']

    return is_deleted


def list_alert(update,context):
    notification_status=get_notification_status(context)

    message = 'Questi sono gli alert che hai impostato: ' + notification_status

    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=message)


def unset_alert(update, context):
    log.info("Starting start command for chat " + str(update.effective_chat.id) + " with " + update.effective_user.name)

    is_deleted = delete_notifications(update, context)
    if is_deleted:
        message = "Alert eliminati"
    else:
        message = "Nessun alert da eliminare"

    context.bot.send_message(chat_id=update.effective_chat.id,
                             text=message)


def error(update, context):
    log.warning('Update "%s" caused error "%s"', update, context.error)


def skip_train_morn(update, context):
    keyboard = calculate_keyboard_markup(trenitalia_api_caller.TRAIN_EVE_LIST)
    update.message.reply_text(
        "Ok! Nessuna notifica per il treno della mattina!\n Impostiamo il treno della sera: "
        "Per quale treno vuoi ricevere aggiornamenti?",
        reply_markup=keyboard)
    return TRAIN_EVE


def skip_train_eve(update, context):
    notification_status = get_notification_status()
    message = "Ok! Nessuna notifica per il treno della sera!\n"
    if notification_status == '':
        message += "Ricapitolando non hai impostato nessuna notifica"
    else:
        message = "Ricapitolando, hai impostato queste notifiche:\n{}".format(notification_status)

    update.message.reply_text(message)
    return ConversationHandler.END


class TrainFilter(BaseFilter):
    train_list = trenitalia_api_caller.TRAIN_MORN_LIST

    def __init__(self, train_list):
        super()
        self.train_list = train_list

    def filter(self, message):
        return message.text in [a[0] for a in self.train_list]


filter_morn = TrainFilter(trenitalia_api_caller.TRAIN_MORN_LIST)
filter_eve = TrainFilter(trenitalia_api_caller.TRAIN_EVE_LIST)


def main():
    updater = Updater(token=os.environ.get('BOTKEY'), use_context=True)

    updater.dispatcher.add_handler(CommandHandler('start', start))
    updater.dispatcher.add_handler(CommandHandler('status', status))
    updater.dispatcher.add_handler(CommandHandler('unsetalert', unset_alert))
    updater.dispatcher.add_handler(CommandHandler('listalert', list_alert))

    # Add conversation handler with the states GENDER, PHOTO, LOCATION and BIO
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('setalert', set_alert)],

        states={
            TRAIN_MORN: [MessageHandler(filter_morn, select_train_morning),
                         CommandHandler('skip', skip_train_morn)],

            UPDATE_MINS_MORN: [MessageHandler(Filters.regex('^[1-6]?[0-9]$'), mins_morning),
                               CommandHandler('default', defaultmins_morn)],

            TRAIN_EVE: [MessageHandler(filter_eve, select_train_evening),
                        CommandHandler('skip', skip_train_eve)],

            UPDATE_MINS_EVE: [MessageHandler(Filters.regex('^[1-6]?[0-9]$'), mins_evening),
                               CommandHandler('default', defaultmins_eve)],

        },

        fallbacks=[CommandHandler('cancel', cancel)]
    )

    updater.dispatcher.add_handler(conv_handler)

    updater.dispatcher.add_error_handler(error)

    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()
