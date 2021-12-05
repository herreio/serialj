import logging
import datetime

from .serialj import SerialJson


class PicaJson(SerialJson):
    """
    Class for parsing PICA JSON (http://format.gbv.de/pica/json)
    """

    def __init__(self, data, name=__name__, level=logging.INFO):
        super().__init__(data, skip=2, name=name, level=level)

    def get_field(self, name, occurrence=None, unique=False):
        found = []
        positions = self._field_pos(name)
        if positions is not None:
            for i in positions:
                if self.data[i][1] is not None and \
                        self.data[i][1].strip() != "" and \
                        occurrence is not None and \
                        self.data[i][1] != occurrence:
                    continue
                found.append(self.data[i])
        if unique:
            if len(found) == 1:
                return found[0]
            else:
                self.logger.warning("Expected field {0} to be unique. Found {1} occurrences.".format(name, len(found)))
        if len(found) > 0:
            return found

    def get_value(self, field, subfield, occurrence=None, unique=False, repeat=True, collapse=False, preserve=True):
        found = self.get_field(field, occurrence=occurrence, unique=unique)
        if found is not None:
            if unique and type(found[0]) != list:
                return self._value_from_row(found, subfield, repeat=repeat)
            else:
                return self._value_from_rows(found, subfield, repeat=repeat, collapse=collapse, preserve=True)
        else:
            self.logger.error("Field {0} with occurrence {1} not found!".format(field, occurrence))

    def get_ppn(self):
        """
        003@/0100: Pica-Produktionsnummer
        """
        return self.get_value("003@", "0", unique=True)

    def get_first_entry(self):
        """
        001A/0200: Kennung und Datum der Ersterfassung
        """
        return self.get_value("001A", "0", unique=True)

    def get_first_entry_code(self):
        """
        001A/0200: Kennung der Ersterfassung
        """
        return self.get_first_entry().split(":")[0]

    def get_first_entry_date(self):
        """
        001A/0200: Datum der Ersterfassung
        """
        return self.get_first_entry().split(":")[1]

    def get_first_entry_date_date(self):
        """
        001A/0200: Datum der Ersterfassung (as date object)
        """
        first_entry_date = self.get_first_entry_date()
        return datetime.datetime.strptime(first_entry_date, "%d-%m-%y").date()

    def get_first_entry_date_iso(self):
        """
        001A/0200: Datum der Ersterfassung (in ISO format)
        """
        first_entry_date = self.get_first_entry_date_date()
        return first_entry_date.isoformat()

    def get_latest_change(self):
        """
        001B/0210: Kennung und Datum der letzten Änderung
        """
        return self.get_value("001B", "0", unique=True)

    def get_latest_change_code(self):
        """
        001B/0210: Kennung der letzten Änderung
        """
        return self.get_latest_change().split(":")[0]

    def get_latest_change_date(self):
        """
        001B/0210: Datum der letzten Änderung
        """
        return self.get_latest_change().split(":")[1]

    def get_latest_change_time(self):
        """
        001B/0210: Uhrzeit der letzten Änderung
        """
        return self.get_value("001B", "t", unique=True)

    def get_latest_change_str(self):
        """
        001B/0210: Zeitstempel der letzten Änderung
        """
        d = self.get_latest_change_date()
        t = self.get_latest_change_time()
        return "{0} {1}".format(d, t)

    def get_latest_change_datetime(self):
        """
        001B/0210: Zeitstempel der letzten Änderung (as datetime object)
        """
        change_datetime = self.get_latest_change_str()
        return datetime.datetime.strptime(change_datetime, "%d-%m-%y %H:%M:%S.%f").astimezone(self.timezone)

    def get_latest_change_iso(self):
        """
        001B/0210: Zeitstempel der letzten Änderung (in ISO format)
        """
        change_datetime = self.get_latest_change_datetime()
        return change_datetime.isoformat()

    def get_rvk(self, collapse=False):
        """
        045R/5090: Regensburger Verbundklassifikation (RVK)
        """
        return self.get_value("045R", "a", unique=False, repeat=False, collapse=collapse)

    def get_holdings_epn(self, occurrence="01"):
        """
        203@/7800: EPNs der Exemplardaten
        """
        return self.get_value("203@", "0", occurrence=occurrence, repeat=False)

    def get_holdings_iln(self, occurrence=None):
        """
        101@: ILNs der Exemplardaten
        """
        return self.get_value("101@", "a", occurrence=occurrence, repeat=False)

    def get_holdings_iln_index(self, iln, occurrence=None):
        """
        101@: ILNs der Exemplardaten
        """
        codes = self.get_holdings_iln(occurrence=occurrence)
        if codes is not None:
            index = [i for i, c in enumerate(codes) if c == iln]
            if len(index) > 0:
                return index

    def get_holdings_iln_count(self, occurrence=None):
        """
        209A/7100: Signatur (Exemplardaten)
          $B    Sigel (nur SWB)
        """
        codes = self.get_holdings_iln(occurrence=occurrence)
        if codes is not None:
            return len(codes)
        else:
            return 0

    def get_holdings_from_iln(self, iln):
        """
        101@: ILNs der Exemplardaten
        203@/7800: EPNs der Exemplardaten
        """
        index = self.get_holdings_iln_index(iln, occurrence=None)
        if index is not None:
            epns = self.get_holdings_epn(occurrence="01")
            if epns is not None and len(epns) == self.get_holdings_iln_count(occurrence=None):
                holdings = []
                for i in index:
                    holdings.append(epns[i])
                if len(holdings) > 0:
                    return holdings
            else:
                self.logger.error("Unequal number of holding ILNs and EPNs in record {0}".format(self.get_ppn()))

    def get_holdings_isil(self, occurrence="01"):
        """
        209A/7100: Signatur (Exemplardaten)
          $B    Sigel (nur SWB)

        Das Unterfeld $B wird bei SWB-Bibliotheken im ersten Signaturfeld maschinell belegt.
        """
        return self.get_value("209A", "B", occurrence=occurrence, repeat=False)

    def get_holdings_isil_occurrence(self, occurrence="01"):
        """
        209A/7100: Signatur (Exemplardaten)
          $B    Sigel (nur SWB)
        """
        codes = self.get_holdings_isil(occurrence=occurrence)
        if codes is not None:
            return len(codes)
        else:
            return 0

    def get_holdings_isil_index(self, isil, occurrence="01"):
        """
        209A/7100: Signatur (Exemplardaten)
          $B    Sigel (nur SWB)
        """
        codes = self.get_holdings_isil(occurrence=occurrence)
        if codes is not None:
            index = [i for i, c in enumerate(codes) if c == isil]
            if len(index) > 0:
                return index

    def get_holdings_from_isil(self, isil, occurrence="01"):
        """
        203@/7800: EPNs der Exemplardaten
        209A/7100: Signatur (Exemplardaten)
            $B    Sigel (nur SWB)
        """
        index = self.get_holdings_isil_index(isil, occurrence=occurrence)
        if index is not None:
            epns = self.get_holdings_epn(occurrence=occurrence)
            if epns is not None and len(epns) == self.get_holdings_isil_occurrence(occurrence=occurrence):
                holdings = []
                for i in index:
                    holdings.append(epns[i])
                if len(holdings) > 0:
                    return holdings
            else:
                self.logger.error("Unequal number of holding ISILs and EPNs in record {0}".format(self.get_ppn()))

    def get_holdings_first_entry_date(self, occurrence="01"):
        """
        201A/7902: Datum der Ersterfassung (Exemplardaten)
        """
        return self.get_value("201A", "0", occurrence=occurrence, repeat=False)

    def get_holdings_first_entry_date_date(self, occurrence="01"):
        """
        201A/7902: Datum der Ersterfassung (Exemplardaten)
        """
        first_entry_dates = self.get_holdings_first_entry_date(occurrence=occurrence)
        if first_entry_dates is not None:
            first_entry_date_objs = []
            for first_entry_date in first_entry_dates:
                first_entry_date_objs.append(datetime.datetime.strptime(first_entry_date, "%d-%m-%y").date())
            return first_entry_date_objs

    def get_holdings_first_entry_date_iso(self, occurrence="01"):
        """
        201A/7902: Datum der Ersterfassung (Exemplardaten)
        """
        first_entry_dates = self.get_holdings_first_entry_date(occurrence=occurrence)
        if first_entry_dates is not None:
            first_entry_date_iso = []
            for first_entry_date in first_entry_dates:
                first_entry_date_iso.append(datetime.datetime.strptime(first_entry_date, "%d-%m-%y").date().isoformat())
            return first_entry_date_iso

    def get_holdings_latest_change_date(self, occurrence="01"):
        """
        201B/7903: Datum und Uhrzeit der letzten Änderung (Exemplardaten)
        """
        return self.get_value("201B", "0", occurrence=occurrence, repeat=False)

    def get_holdings_latest_change_time(self, occurrence="01"):
        """
        201B/7903: Datum und Uhrzeit der letzten Änderung (Exemplardaten)
        """
        return self.get_value("201B", "t", occurrence=occurrence, repeat=False)

    def get_holdings_latest_change_str(self, occurrence="01"):
        """
        201B/7903: Datum und Uhrzeit der letzten Änderung (Exemplardaten)
        """
        latest_change_date = self.get_holdings_latest_change_date(occurrence=occurrence)
        latest_change_time = self.get_holdings_latest_change_time(occurrence=occurrence)
        if latest_change_date is not None and latest_change_time is not None:
            if len(latest_change_date) != len(latest_change_time):
                self.logger.error("Unequal number of edit dates and times in holding data of record {0}".format(self.get_ppn()))
                return None
            latest_change_str = []
            for i in range(len(latest_change_date)):
                latest_change_str.append("{0} {1}".format(latest_change_date[i], latest_change_time[i]))
            if len(latest_change_str) > 0:
                return latest_change_str

    def get_holdings_latest_change_datetime(self, occurrence="01"):
        """
        201B/7903: Datum und Uhrzeit der letzten Änderung (Exemplardaten) (as datetime object)
        """
        change_str = self.get_holdings_latest_change_str(occurrence=occurrence)
        if change_str is not None:
            latest_change_datetime = []
            for ch_str in change_str:
                if ch_str != "" and ch_str is not None:
                    latest_change_datetime.append(datetime.datetime.strptime(ch_str, "%d-%m-%y %H:%M:%S.%f").astimezone(self.timezone))
                else:
                    latest_change_datetime.append(ch_str)
            if len(latest_change_datetime) > 0:
                return latest_change_datetime

    def get_holdings_latest_change_iso(self, occurrence="01"):
        """
        201B/7903: Datum und Uhrzeit der letzten Änderung (Exemplardaten) (in ISO format)
        """
        change_str = self.get_holdings_latest_change_str(occurrence=occurrence)
        if change_str is not None:
            latest_change_iso = []
            for ch_str in change_str:
                if ch_str != "" and ch_str is not None:
                    latest_change_iso.append(datetime.datetime.strptime(ch_str, "%d-%m-%y %H:%M:%S.%f").astimezone(self.timezone).isoformat())
                else:
                    latest_change_iso.append(ch_str)
            if len(latest_change_iso) > 0:
                return latest_change_iso

    def get_holdings_isil_latest_change_str(self, isil, occurrence="01"):
        """
        201B/7903: Datum und Uhrzeit der letzten Änderung (Exemplardaten)
        """
        index = self.get_holdings_isil_index(isil)
        if index is not None:
            isil_latest_change_str = []
            change_str = self.get_holdings_latest_change_str(occurrence=occurrence)
            if change_str is not None:
                for i in index:
                    isil_latest_change_str.append(change_str[i])
            if len(isil_latest_change_str) > 0:
                return isil_latest_change_str

    def get_holdings_isil_latest_change_datetime(self, isil, occurrence="01"):
        """
        201B/7903: Datum und Uhrzeit der letzten Änderung (Exemplardaten) (as datetime object)
        """
        change_str = self.get_holdings_isil_latest_change_str(isil, occurrence=occurrence)
        if change_str is not None:
            latest_change_datetime = []
            for ch_str in change_str:
                latest_change_datetime.append(datetime.datetime.strptime(ch_str, "%d-%m-%y %H:%M:%S.%f").astimezone(self.timezone))
            if len(latest_change_datetime) > 0:
                return latest_change_datetime

    def get_holdings_isil_latest_change_iso(self, isil, occurrence="01"):
        """
        201B/7903: Datum und Uhrzeit der letzten Änderung (Exemplardaten) (in ISO format)
        """
        change_str = self.get_holdings_isil_latest_change_str(isil, occurrence=occurrence)
        if change_str is not None:
            latest_change_iso = []
            for ch_str in change_str:
                latest_change_iso.append(datetime.datetime.strptime(ch_str, "%d-%m-%y %H:%M:%S.%f").astimezone(self.timezone).isoformat())
            if len(latest_change_iso) > 0:
                return latest_change_iso

    def get_holdings_iln_latest_change_str(self, iln):
        """
        201B/7903: Datum und Uhrzeit der letzten Änderung (Exemplardaten)
        """
        index = self.get_holdings_iln_index(iln, occurrence=None)
        if index is not None:
            change_str = self.get_holdings_latest_change_str(occurrence="01")
            if change_str is not None:
                if len(change_str) == self.get_holdings_iln_count(occurrence=None):
                    isil_latest_change_str = []
                    for i in index:
                        isil_latest_change_str.append(change_str[i])
                    if len(isil_latest_change_str) > 0:
                        return isil_latest_change_str
                else:
                    self.logger.error("Unequal number of holding ILNs and EPNs in record {0}".format(self.get_ppn()))

    def get_holdings_iln_latest_change_datetime(self, iln):
        """
        201B/7903: Datum und Uhrzeit der letzten Änderung (Exemplardaten) (as datetime object)
        """
        change_str = self.get_holdings_iln_latest_change_str(iln)
        if change_str is not None:
            latest_change_datetime = []
            for ch_str in change_str:
                latest_change_datetime.append(datetime.datetime.strptime(ch_str, "%d-%m-%y %H:%M:%S.%f").astimezone(self.timezone))
            if len(latest_change_datetime) > 0:
                return latest_change_datetime

    def get_holdings_iln_latest_change_iso(self, iln):
        """
        201B/7903: Datum und Uhrzeit der letzten Änderung (Exemplardaten) (in ISO format)
        """
        change_str = self.get_holdings_iln_latest_change_str(iln)
        if change_str is not None:
            latest_change_iso = []
            for ch_str in change_str:
                latest_change_iso.append(datetime.datetime.strptime(ch_str, "%d-%m-%y %H:%M:%S.%f").astimezone(self.timezone).isoformat())
            if len(latest_change_iso) > 0:
                return latest_change_iso

    def get_holdings_source_first_entry(self, occurrence="01"):
        """
        201D/7901: Quelle und Datum der Ersterfassung (Exemplardaten)
        """
        return self.get_value("201D", "0", occurrence=occurrence, repeat=False)

    def get_holdings_source_first_entry_eln(self, occurrence="01"):
        """
        201D/7901: Quelle der Ersterfassung (Exemplardaten)
        """
        source_first_entry = self.get_holdings_source_first_entry(occurrence=occurrence)
        if source_first_entry is not None:
            codes = []
            for sfe in source_first_entry:
                codes.append(sfe.split(":")[0])
            if len(codes) > 0:
                return codes

    def get_holdings_source_first_entry_date(self, occurrence="01"):
        """
        201D/7901: Datum der Ersterfassung (Exemplardaten)
        """
        source_first_entry = self.get_holdings_source_first_entry(occurrence=occurrence)
        if source_first_entry is not None:
            dates = []
            for sfe in source_first_entry:
                dates.append(sfe.split(":")[1])
            if len(dates) > 0:
                return dates

    def get_holdings_source_first_entry_date_date(self, occurrence="01"):
        """
        201D/7901: Datum der Ersterfassung (Exemplardaten) (as date object)
        """
        source_first_entry_date = self.get_holdings_source_first_entry_date(occurrence=occurrence)
        if source_first_entry_date is not None:
            dates = []
            for sfe_date in source_first_entry_date:
                dates.append(datetime.datetime.strptime(sfe_date, "%d-%m-%y").date())
            if len(dates) > 0:
                return dates

    def get_holdings_source_first_entry_date_iso(self, occurrence="01"):
        """
        201D/7901: Quelle und Datum der Ersterfassung (Exemplardaten) (in ISO format)
        """
        source_first_entry_date = self.get_holdings_source_first_entry_date_date(occurrence=occurrence)
        if source_first_entry_date is not None:
            dates = []
            for sfe_date in source_first_entry_date:
                dates.append(sfe_date.isoformat())
            if len(dates) > 0:
                return dates

    def get_holdings_eln_first_entry(self, eln, occurrence="01"):
        """
        201D/7901: Quelle und Datum der Ersterfassung (Exemplardaten)
        """
        elns = self.get_holdings_source_first_entry_eln(occurrence=occurrence)
        if elns is not None and eln in elns:
            eln_entries = []
            entries = self.get_holdings_source_first_entry(occurrence=occurrence)
            if entries is not None:
                eln_entries = [e for e in entries if eln in e]
            if len(eln_entries) > 0:
                return eln_entries

    def get_holdings_eln_first_entry_date(self, eln, occurrence="01"):
        """
        201D/7901: Datum der Ersterfassung (Exemplardaten)
        """
        first_entry_date = self.get_holdings_eln_first_entry(eln, occurrence=occurrence)
        if first_entry_date is not None:
            dates = []
            for sfe in first_entry_date:
                dates.append(sfe.split(":")[1])
            if len(dates) > 0:
                return dates

    def get_holdings_eln_first_entry_date_date(self, eln, occurrence="01"):
        """
        201D/7901: Datum der Ersterfassung (Exemplardaten) (as date object)
        """
        first_entry_date = self.get_holdings_eln_first_entry_date(eln, occurrence=occurrence)
        if first_entry_date is not None:
            dates = []
            for sfe_date in first_entry_date:
                dates.append(datetime.datetime.strptime(sfe_date, "%d-%m-%y").date())
            if len(dates) > 0:
                return dates

    def get_holdings_eln_first_entry_date_iso(self, eln, occurrence="01"):
        """
        201D/7901: Quelle und Datum der Ersterfassung (Exemplardaten) (in ISO format)
        """
        first_entry_date = self.get_holdings_eln_first_entry_date_date(eln, occurrence=occurrence)
        if first_entry_date is not None:
            dates = []
            for sfe_date in first_entry_date:
                dates.append(sfe_date.isoformat())
            if len(dates) > 0:
                return dates

    def get_holdings_url(self, occurrence="01"):
        """
        209R/7133: Lokale Angaben zum Zugriff auf Online-Ressourcen (Exemplardaten)
          $u    URL
        """
        return self.get_value("209R", "u", occurrence=occurrence, repeat=False)

    def get_holdings_new_date(self, occurrence="01"):
        """
        208@/E001: Neuanlagedatum und Selektionsschlüssel (Exemplardaten)
          $a    Neuanlagedatum
        """
        return self.get_value("208@", "a", occurrence=occurrence, repeat=False)

    def get_holdings_new_date_date(self, occurrence="01"):
        """
        208@/E001: Neuanlagedatum und Selektionsschlüssel (Exemplardaten)
          $a    Neuanlagedatum
        """
        new_date = self.get_value("208@", "a", occurrence=occurrence, repeat=False)
        if new_date is not None:
            dates = []
            for n_date in new_date:
                dates.append(datetime.datetime.strptime(n_date, "%d-%m-%y").date())
            if len(dates) > 0:
                return dates

    def get_holdings_new_date_iso(self, occurrence="01"):
        """
        208@/E001: Neuanlagedatum und Selektionsschlüssel (Exemplardaten)
          $a    Neuanlagedatum
        """
        new_date = self.get_holdings_new_date_date(occurrence=occurrence)
        if new_date is not None:
            dates = []
            for n_date in new_date:
                dates.append(n_date.isoformat())
            if len(dates) > 0:
                return dates

    def get_holdings_isil_new_date(self, isil, occurrence="01"):
        """
        208@/E001: Neuanlagedatum und Selektionsschlüssel (Exemplardaten)
          $a    Neuanlagedatum
        209A/7100: Signatur (Exemplardaten)
            $B    Sigel (nur SWB)
        """
        index = self.get_holdings_isil_index(isil, occurrence=occurrence)
        if index is not None:
            new_dates = self.get_holdings_new_date(occurrence=occurrence)
            if new_dates is not None and len(new_dates) == self.get_holdings_isil_occurrence(occurrence=occurrence):
                dates = []
                for i in index:
                    dates.append(new_dates[i])
                if len(dates) > 0:
                    return dates
            else:
                self.logger.error("Unequal number of holding ISILs and new dates in record {0}".format(self.get_ppn()))

    def get_holdings_isil_new_date_date(self, isil, occurrence="01"):
        """
        208@/E001: Neuanlagedatum und Selektionsschlüssel (Exemplardaten)
          $a    Neuanlagedatum (as date object)
        209A/7100: Signatur (Exemplardaten)
            $B    Sigel (nur SWB)
        """
        new_date = self.get_holdings_isil_new_date(isil, occurrence=occurrence)
        if new_date is not None:
            dates = []
            for n_date in new_date:
                dates.append(datetime.datetime.strptime(n_date, "%d-%m-%y").date())
            if len(dates) > 0:
                return dates

    def get_holdings_isil_new_date_iso(self, isil, occurrence="01"):
        """
        208@/E001: Neuanlagedatum und Selektionsschlüssel (Exemplardaten)
          $a    Neuanlagedatum (in ISO format)
        209A/7100: Signatur (Exemplardaten)
            $B    Sigel (nur SWB)
        """
        new_date = self.get_holdings_isil_new_date_date(isil, occurrence=occurrence)
        if new_date is not None:
            dates = []
            for n_date in new_date:
                dates.append(n_date.isoformat())
            if len(dates) > 0:
                return dates

    def get_holdings_new_key(self, occurrence="01"):
        """
        208@/E001: Neuanlagedatum und Selektionsschlüssel (Exemplardaten)
          $b    Selektionsschlüssel
        """
        return self.get_value("208@", "b", occurrence=occurrence, repeat=False)

    def get_holdings_isil_new_key(self, isil, occurrence="01"):
        """
        208@/E001: Neuanlagedatum und Selektionsschlüssel (Exemplardaten)
          $b    Selektionsschlüssel
        209A/7100: Signatur (Exemplardaten)
            $B    Sigel (nur SWB)
        """
        index = self.get_holdings_isil_index(isil, occurrence=occurrence)
        if index is not None:
            new_key = self.get_holdings_new_key(occurrence=occurrence)
            if new_key is not None and len(new_key) == self.get_holdings_isil_occurrence(occurrence=occurrence):
                keys = []
                for i in index:
                    keys.append(new_key[i])
                if len(keys) > 0:
                    return keys
            else:
                self.logger.error("Unequal number of holding ISILs and new keys in record {0}".format(self.get_ppn()))
