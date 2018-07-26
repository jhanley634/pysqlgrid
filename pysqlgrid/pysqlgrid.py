
# Copyright 2018, REX - Real Estate Exchange Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import csv
import datetime as dt
import html
import io
import re
import urllib.parse

import flask
import sqlalchemy.exc as exc
import sqlalchemy.orm as orm


class PySqlGrid:
    """Turns a SQL query into an interactive sortable data grid.

    All results are computed in the backend DB + web servers.
    """

    def __init__(self, engine, query: str, sort_cols: list):
        self.engine = engine
        self.query_sorted = '{}\n    order by  {}'.format(
            query.rstrip(), ', '.join(sort_cols))
        self.result = self._execute(self.query_sorted + ' limit 1000')
        self.col_names = self._get_metadata()

    def _execute(self, query):
        result = None
        sess = orm.sessionmaker(self.engine)()
        try:
            result = sess.execute(query)
        except exc.StatementError:
            # Can't reconnect until invalid transaction is rolled back
            # (even though `query` really did start with 'select ...')
            sess.rollback()
            result = sess.execute(query)
        return result

    def _get_metadata(self):
        return [col.name
                for col in self.result.cursor.description]

    def _render_html_head(self, table_name, top_text=''):
        dl_link = href(add_query_arg(flask.request.url, 'csv'), 'csv')
        return f"""<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN"
        "http://www.w3.org/TR/html4/strict.dtd">
        <html>
        <head>
          <title>SQL datagrid - {table_name}</title>
          <link  rel="stylesheet" type="text/css" href="/static/style.css">
        </head>
        <body>
          {top_text}
          <p class="csv_download_link">{dl_link}</p>
          <pre class="query_small">{self.query_sorted}</pre>
        """

    def render_table(self):
        if 'csv' in flask.request.args:
            return self._render_as_csv()
        rows = [self._render_column_heading()]
        for i, row in enumerate(self.result.fetchall()):
            row_class = 'mod%d' % (i % 3)
            html = ['<td class="col_{}">{}</td>'.format(
                self.col_names[j], self._render_element(val))
                for j, val in enumerate(row)]
            rows.append('<tr class="{}">{}</tr>'.format(
                row_class, ' '.join(html)))
        rows.append('</table>')
        return self._render_html_head(self._get_tbl_name()) + '\n'.join(rows)

    def _render_element(self, elt):
        if isinstance(elt, dt.datetime):
            day = elt.strftime('%Y-%m-%d ')
            hms = elt.strftime('<span class="small_hms">%H:%M:%S</span>')
            return day + hms
        return html.escape(str(elt))

    def _render_column_heading(self):
        cols = ['<th><span class="label">{}</span>{}</th>'.format(
            col_name.replace('_', ' '), self._sort_up_down(col_name))
            for col_name in self.col_names]
        return '\n<table summary=""><tr>{}</tr>\n'.format(''.join(cols))

    def _sort_up_down(self, col_name):
        return ' &nbsp; {}{}{}'.format(
            href('?sort=' + col_name + '+ASC', '&uarr;'),
            href('?', '&#x2612;'),
            href('?sort=' + col_name + '+DESC', '&darr;'),
        )

    def _get_tbl_name(self):
        """Returns name of first table SELECTed from, if available."""
        # We discard schema, so FROM scm.tbl becomes tbl.
        m = re.search(r'\bfrom\s+(\w+\.)?(\w+)',
                      self.query_sorted, re.IGNORECASE)
        return m.group(2) if m else 'table'

    def _render_as_csv(self):
        fout = io.StringIO()
        sheet = csv.writer(fout)
        sheet.writerow(self.col_names)
        for row in self.result.fetchall():
            sheet.writerow(row)
        fout.seek(0)
        # Equivalently we could return a triple: text, 200, dict
        return flask.Response(fout.read(), mimetype='text/plain')


def href(url, txt):
    return "<a href='{}'>{}</a>".format(url, txt)


def add_query_arg(url, query_arg):
    parts = list(urllib.parse.urlparse(url))
    parts[4] += '&' + query_arg
    return urllib.parse.urlunparse(parts)
