
import time

STATUS = {
    0: "In viaggio",
    1: "Arrivato a destinazione",
    2: "Non ancora partito",
    3: "Deviato",
    4: "Soppresso",
    5: "Parzialmente soppresso"
}

class Train():
    def __init__(self):
        pass

    def __init__(self,apiresp):
        self.id_number = apiresp['numeroTreno']
        self.last_station = apiresp['stazioneUltimoRilevamento']
        self.train_type = apiresp['tipoTreno']

        self.origin = apiresp['origine']
        self.destination = apiresp['destinazione']

        if self.last_station == '--':
            self.status = 2
        elif self.destination == self.last_station:
            self.status = 1
        elif self.train_type == 'PG':
            self.status = 0
        elif self.train_type == 'DV':
            self.status = 3
        elif self.train_type == 'ST':
            self.status = 4
        else:
            self.status = 5

        self.time_last_data = apiresp['compOraUltimoRilevamento']
        self.cur_orientation = apiresp['orientamento']
        self.minutes_late = apiresp['ritardo']

        self.stops = [ Stop(f['stazione'],
                       f['progressivo'],
                       f['partenza_teorica'],
                       f['arrivo_teorico'],
                       f['orientamento'],
                       f['binarioProgrammatoPartenzaDescrizione'],
                       f['binarioEffettivoPartenzaDescrizione'])
                    for f in apiresp['fermate']]

    def status_str(self):
        return 'Stato treno: ' + STATUS[self.status]

    def orientation_str(self):
        return orientation_str(self)

    def late_str(self):
        if self.status == 2:
            return ''

        if self.minutes_late == 0:
            verb = 'orario'
            late_str = ''
        else:
            if self.minutes_late > 0:
                verb = "ritardo"
            else:
                verb = "anticipo"
            late_str = " di %d minuti" % self.minutes_late

        return '\nRilevato alle %s a %s, in %s%s' % (
        self.time_last_data, self.last_station, verb,late_str)


    def __str__(self):
        return 'Treno %d da %s a %s' % (self.id_number,self.origin,self.destination)

    def get_stop(self,station):
        results=[]
        for s in self.stops:
            if station in s.station:
                results.append(s)

        return results


class Stop():
    def __init__(self, station, index, departure_ts, arrival_ts, orientation, prog_platform, real_platform):
        self.station = station
        self.index = index
        if departure_ts:
            self.departure_ts = time.strftime('%H:%M',time.localtime(departure_ts/1000))
        if arrival_ts:
            self.arrival_ts = time.strftime('%H:%M',time.localtime(arrival_ts / 1000))
        self.orientation = orientation
        self.prog_platform = prog_platform
        self.real_platform = real_platform

    def orientation_str(self):
        return orientation_str(self)

def orientation_str(ob):
    if ob.orientation == 'A':
        desc_orientation = 'Classe Standard in testa treno'
    elif ob.orientation == 'B':
        desc_orientation = 'Classe Standard in coda treno'
    else:
        desc_orientation = 'Non si conosce l\'orientamento del treno'

    return desc_orientation
