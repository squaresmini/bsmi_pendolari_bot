import requests
from datetime import datetime,timedelta
from train import Train
import logging

log = logging.getLogger("trenitalia_api_caller")

TRAIN_MORN_LIST = [
    ('9700', "07:34"),
    ('9702', "08:09"),
    ('9706', "08:39"),
    ('9708', "09:09"),
    ('9712', "09:39"),
    ('9716', "10:09"),
]

TRAIN_EVE_LIST = [
    ('9745', "16:45"),
    ('9747', "17:15"),
    ('9749', "17:45"),
    ('9751', "18:15"),
    ('9753', "18:45"),
    ('9755', "19:15"),
    ('9757', "19:45"),
    ('9759', "20:15"),
    ('9761', "20:45"),
    ('9649', "21:15")
]

TRENITALIA_URL = 'http://www.viaggiatreno.it/viaggiatrenonew/resteasy/viaggiatreno'

def call_trenitalia_api(path):
    resp = requests.get(TRENITALIA_URL + path)
    if resp.status_code == 200:
        log.info("API call successful")
        return resp
    else:
        log.error("API call failed: "+str(resp.status_code))
        raise Exception("Errore: status code = " + str(resp.status_code))


def get_status_mess(station_id, train_number):
    path = '/andamentoTreno/' + station_id + "/" + train_number
    resp = call_trenitalia_api(path)
    res = resp.json()

    train = Train(res)

    bs_stops = train.get_stop("BRESCIA")
    mi_stops = train.get_stop("MILANO")

    if not bs_stops or not mi_stops:
        stops_str ='Non passa per Brescia e Milano'
    else:
        if bs_stops[0].index < mi_stops[0].index:
            bsmi_stops = bs_stops+mi_stops
        else:
            bsmi_stops = mi_stops+bs_stops

        stops_list = []
        for i,s in enumerate(bsmi_stops):
            if i == (len(bsmi_stops)-1):
                ttime = s.arrival_ts
            else:
                ttime = s.departure_ts

            stops_list.append("%s (%s)" % (s.station,ttime))

        stops_str = " - ".join(stops_list)

    str_result = str(train) + "\n" \
                 + stops_str + "\n" \
                 + train.status_str() \
                 + train.late_str()\
                 + "\n" + bs_stops[0].orientation_str()

    return str_result


def retrieve_train(number):
    path = "/cercaNumeroTrenoTrenoAutocomplete/"+number
    res = call_trenitalia_api(path)
    train = res.text.split('\n')[0]
    if train:
        return tuple(train.split('|')[1].split('-'))
    else:
        raise Exception("Treno inesistente")


def calculate_next_train():
    curtime = datetime.now().time()
    for train_num,train_time in TRAIN_MORN_LIST + TRAIN_EVE_LIST:
        td = timedelta(minutes=10)
        traindate = datetime.strptime(train_time, "%H:%M") + td
        ttime = traindate.time()
        if  curtime<ttime:
            return train_num
    return None



