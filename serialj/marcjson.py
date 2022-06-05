import logging
import datetime

from .serialj import SerialJson


class MarcJson(SerialJson):
    """
    Class for parsing MARC JSON (http://format.gbv.de/marc/json)
    """

    def __init__(self, data, name=__name__, level=logging.INFO):
        super().__init__(data, skip=3, name=name, level=level)

    def get_field(self, name, indicator1=None, indicator2=None, unique=False):
        found = []
        positions = self._field_pos(name)
        if positions is not None:
            for i in positions:
                if self.data[i][1] is not None and \
                        self.data[i][1].strip() != "" and \
                        indicator1 is not None and \
                        self.data[i][1] != indicator1:
                    continue
                if self.data[i][2] is not None and \
                        self.data[i][2].strip() != "" and \
                        indicator2 is not None and \
                        self.data[i][2] != indicator2:
                    continue
                found.append(self.data[i])
        if unique:
            if len(found) == 1:
                return found[0]
            else:
                self.logger.warning("Expected field {0} to be unique. Found {1} occurrences.".format(name, len(found)))
        if len(found) > 0:
            return found

    def get_value(self, field, subfield, indicator1=None, indicator2=None, unique=False, repeat=True, collapse=False, preserve=True):
        found = self.get_field(field, indicator1=indicator1, indicator2=indicator2, unique=unique)
        if found is not None:
            if unique and type(found[0]) != list:
                return self._value_from_row(found, subfield, repeat=repeat)
            else:
                return self._value_from_rows(found, subfield, repeat=repeat, collapse=collapse, preserve=True)
        else:
            self.logger.error("Field {0} with indicators {1} and {2} not found!".format(field, indicator1, indicator2))

    def get_ppn(self):
        """
        001: Control Number
        """
        return self.get_value("001", "_", unique=True)

    def get_latest_trans(self):
        """
        005: Date and Time of Latest Transaction
        """
        return self.get_value("005", "_", unique=True)

    def get_latest_trans_datetime(self):
        """
        005: Date and Time of Latest Transaction (as datetime object)
        """
        latest_trans = self.get_latest_trans()
        if latest_trans is not None:
            try:
                return datetime.datetime.strptime(latest_trans, "%Y%m%d%H%M%S.0")
            except ValueError:
                return datetime.datetime.strptime(latest_trans, "%Y%m%d222222:2")

    def get_latest_trans_iso(self):
        """
        005: Date and Time of Latest Transaction (in ISO format)
        """
        latest_trans = self.get_latest_trans_datetime()
        if latest_trans is not None:
            return latest_trans.isoformat()

    def get_data_elements(self):
        """
        008: Fixed-Length Data Elements
        """
        return self.get_value("008", "_", unique=True)

    def get_date_entered(self):
        """
        008: Fixed-Length Data Elements

          00-05 - Date entered on file
        """
        date_elements = self.get_data_elements()
        if len(date_elements) > 5:
            return date_elements[:6]

    def get_date_entered_date(self):
        """
        008: Fixed-Length Data Elements

          00-05 - Date entered on file (as date object)
        """
        date_entered = self.get_date_entered()
        if date_entered is not None:
            return datetime.datetime.strptime(date_entered, "%y%m%d").date()

    def get_date_entered_iso(self):
        """
        008: Fixed-Length Data Elements

          00-05 - Date entered on file (in ISO format)
        """
        date_entered = self.get_date_entered_date()
        if date_entered is not None:
            return date_entered.isoformat()

    def get_holdings_epn(self, indicator1="0", indicator2=None):
        """
        924/DNB: Bestandsinformationen
          $a - Lokale IDN des Bestandsdatensatzes
        """
        return self.get_value("924", "a", indicator1=indicator1, indicator2=indicator2, repeat=False)

    def get_holdings_isil(self, indicator1="0", indicator2=None):
        """
        924/DNB: Bestandsinformationen
          $b - ISIL als Kennzeichnung der besitzenden Institution
        """
        return self.get_value("924", "b", indicator1=indicator1, indicator2=indicator2, repeat=False)

    def get_holdings_from_isil(self, isil, indicator1="0", indicator2=None):
        """
        924/DNB: Bestandsinformationen
          $b - ISIL als Kennzeichnung der besitzenden Institution
          $a - Lokale IDN des Bestandsdatensatzes
        """
        isils = self.get_holdings_isil(indicator1=indicator1, indicator2=indicator2)
        if isils is None or isil not in isils:
            self.logger.info("Library {0} has no holding for record {1}".format(isil, self.get_ppn()))
            return None
        holdings = []
        holding_fields = self.get_field("924")
        for holding_field in holding_fields:
            if self._value_from_row(holding_field, "b", repeat=False) == isil:
                holdings.append(self._value_from_row(holding_field, "a", repeat=False))
        if len(holdings) > 0:
            return holdings

    def get_holdings_status(self, indicator1="0", indicator2=None):
        """
        924/DNB: Bestandsinformationen
          $d - Fernleihindikator
        """
        return self.get_value("924", "d", indicator1=indicator1, indicator2=indicator2, repeat=False)

    def get_holdings_epn_status(self, epn, indicator1="0", indicator2=None):
        """
        924/DNB: Bestandsinformationen
          $b - ISIL als Kennzeichnung der besitzenden Institution
          $d - Fernleihindikator
        """
        epns = self.get_holdings_epn(indicator1=indicator1, indicator2=indicator2)
        if epns is None or epn not in epns:
            self.logger.info("Holding {0} not found in record {1}".format(epn, self.get_ppn()))
            return None
        holding_fields = self.get_field("924")
        for holding_field in holding_fields:
            if self._value_from_row(holding_field, "a", repeat=False) == epn:
                return self._value_from_row(holding_field, "d", repeat=False)

    def get_holdings_isil_status(self, isil, indicator1="0", indicator2=None):
        """
        924/DNB: Bestandsinformationen
          $b - ISIL als Kennzeichnung der besitzenden Institution
          $d - Fernleihindikator
        """
        isils = self.get_holdings_isil(indicator1=indicator1, indicator2=indicator2)
        if isils is None or isil not in isils:
            self.logger.info("Library {0} has no holding for record {1}".format(isil, self.get_ppn()))
            return None
        statuses = []
        holding_fields = self.get_field("924")
        for holding_field in holding_fields:
            if self._value_from_row(holding_field, "b", repeat=False) == isil:
                statuses.append(self._value_from_row(holding_field, "d", repeat=False))
        if len(statuses) > 0:
            return statuses

    def get_holdings_signature(self, indicator1="0", indicator2=None):
        """
        924/DNB: Bestandsinformationen
          $g - Signatur
        """
        return self.get_value("924", "g", indicator1=indicator1, indicator2=indicator2)

    def get_holdings_epn_signature(self, epn, indicator1="0", indicator2=None):
        """
        924/DNB: Bestandsinformationen
          $a - Lokale IDN des Bestandsdatensatzes
          $g - Signatur
        """
        epns = self.get_holdings_epn(indicator1=indicator1, indicator2=indicator2)
        if epns is None or epn not in epns:
            self.logger.info("Holding {0} not found in record {1}".format(epn, self.get_ppn()))
            return None
        holding_fields = self.get_field("924")
        for holding_field in holding_fields:
            if self._value_from_row(holding_field, "a", repeat=False) == epn:
                return self._value_from_row(holding_field, "g")

    def get_holdings_isil_signature(self, isil, indicator1="0", indicator2=None):
        """
        924/DNB: Bestandsinformationen
          $b - ISIL als Kennzeichnung der besitzenden Institution
          $g - Signatur
        """
        isils = self.get_holdings_isil(indicator1=indicator1, indicator2=indicator2)
        if isils is None or isil not in isils:
            self.logger.info("Library {0} has no holding for record {1}".format(isil, self.get_ppn()))
            return None
        signatures = []
        holding_fields = self.get_field("924")
        for holding_field in holding_fields:
            if self._value_from_row(holding_field, "b", repeat=False) == isil:
                signatures.append(self._value_from_row(holding_field, "g"))
        if len(signatures) > 0:
            return signatures
