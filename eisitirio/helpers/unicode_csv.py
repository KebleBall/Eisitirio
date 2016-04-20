# coding: utf-8
"""Helper to support writing Unicode CSV files."""

import codecs
import cStringIO
import csv

import six

class UnicodeWriter(object):
    """CSV writer which supports unicode output.

    Lifted from https://docs.python.org/2/library/csv.html
    """

    def __init__(self, stream, dialect=csv.excel, encoding="utf-8", **kwds):
        self.buffer = cStringIO.StringIO()
        self.writer = csv.writer(self.buffer, dialect=dialect, **kwds)
        self.stream = stream
        self.encoder = codecs.getincrementalencoder(encoding)()

    def writerow(self, row):
        """Write a row, encoding it in the chosen encoding.

        Works by using the built in CSV writer to write utf-8 encoded data to a
        buffer, and then re-encodes that data to the chosen encoding before
        writing it to the given stream.
        """
        def encode_strings(row):
            for item in row:
                if isinstance(item, six.string_types):
                    yield item.encode("utf-8")
                else:
                    yield item

        self.writer.writerow(list(encode_strings(row)))

        self.stream.write(
            self.encoder.encode(
                self.buffer.getvalue().decode("utf-8")
            )
        )

        self.buffer.truncate(0)

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)
