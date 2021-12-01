from .parser import Parser


class SerialJson(Parser):
    """
    Generic class for parsing JSON serialized MARC or PICA data
    """

    def __init__(self, data, skip=1, name=None, level=None):
        super().__init__(data, name=name, level=level)
        self.idx = self._indices()
        self.skip = skip

    def _indices(self):
        indices = {}
        for i, field in enumerate(self.data):
            if field[0] in indices:
                indices[field[0]].append(i)
            else:
                indices[field[0]] = [i]
        return indices

    def _field_pos(self, name):
        if name in self.idx:
            return self.idx[name]

    def _subfield_pos(self, row, subf):
        positions = []
        for i in range(self.skip, len(row), 2):
            if row[i] == subf:
                positions.append(i + 1)
        if len(positions) > 0:
            return positions

    def _value_from_row(self, row, subfield, repeat=True):
        pos = self._subfield_pos(row, subfield)
        if pos is not None:
            if len(pos) == 1:
                return row[pos[0]]
            else:
                if not repeat:
                    if all(len(row[p]) == 1 for p in pos):
                        return [row[p][0] for p in pos]
                    else:
                        self.logger.warning("Expected unrepeated subfield {0} in field {1}. Found mutiple occurrences.".format(subfield, row[0]))
                return [row[p] for p in pos]

    def _value_from_rows(self, rows, subfield, repeat=True, collapse=False, preserve=True):
        found = []
        for row in rows:
            sub_found = []
            pos = self._subfield_pos(row, subfield)
            if pos is not None:
                for p in pos:
                    sub_found.append(row[p])
            elif preserve:
                sub_found.append("")
            if collapse:
                sub_found = "|".join(sub_found)
            found.append(sub_found)
        if len(found) > 0:
            if collapse:
                return "||".join(found)
            if not repeat:
                if not all(len(sbf) == 1 for sbf in found):
                    self.logger.warning("Expected unrepeated subfield {0} in field {1}. Found mutiple occurrences.".format(subfield, rows[0][0]))
                return [sbf[0] for sbf in found]
            return found
        else:
            self.logger.error("Subfield {0} not found in field {1}!".format(subfield, rows[0][0]))
