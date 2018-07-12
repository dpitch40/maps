import re
import argparse
from urllib.request import urlopen
from urllib.error import HTTPError
import time
import os.path
import operator
import itertools
import csv

from bs4 import BeautifulSoup

google_maps_url_re = re.compile(r'http(?:s)?://www.google.com/maps/[^@]*@(\-?\d+\.\d+),(\-?\d+\.\d+)')
wikipedia_url_re = re.compile(r'http(?:s)?://(\w+).wikipedia.org/wiki/')

def expand_wikipedia_url(url):
    return 'https://en.wikipedia.org%s' % url

def scrape_url(url):
    if not url:
        return None

    m = google_maps_url_re.match(url)
    if m:
        return m.groups()

    m = wikipedia_url_re.match(url)
    if m:
        return scrape_wikipedia_url(url)

    raise ValueError('No rules defined for scraping the URL %s' % url)

def scrape_wikipedia_element(soup, path=None):
    if path is None:
        path = [('span', {'id': 'coordinates'})]

    for name, kwargs in path:
        soup = soup.find(name, **kwargs)
        if soup is None:
            return None

    lat = soup.find('span', class_='latitude')
    if lat:
        lat = lat.string
    lon = soup.find('span', class_='longitude')
    if lon:
        lon = lon.string

    return lat, lon

def scrape_wikipedia_url(url, path=None):
    try:
        with urlopen(url) as fobj:
            time.sleep(1)
            soup = BeautifulSoup(fobj, 'lxml')

            return scrape_wikipedia_element(soup, path)

    except HTTPError as ex:
        return None

def parse_table_headers(table):
    row = table.find('tr')
    header_info = []
    while True:
        cur_header_info = []
        row_children = row.find_all(['th', 'td'])
        num_non_headers = len(list(filter(lambda t: t.name == 'td', row_children)))
        if num_non_headers == 0:
            for header in row.find_all('th'):
                colspan = header.attrs.get('colspan', 1)
                rowspan = header.attrs.get('rowspan', 1)
                cur_header_info.append((' '.join(header.stripped_strings), int(colspan), int(rowspan)))
        else:
            break
        header_info.append(cur_header_info)
        row = row.find_next_sibling('tr')

    num_rows = len(header_info)
    num_cols = max(sum(map(operator.itemgetter(1), r)) for r in header_info)

    header_lists = [[] for i in range(num_cols)]
    for rownum, info in enumerate(header_info):
        cur_col = 0
        while len(header_lists[cur_col]) > rownum:
            cur_col += 1
        for header, colspan, rowspan in info:
            for col in range(cur_col, cur_col + colspan):
                header_lists[col].append(header)
            if rowspan > 1:
                for extra_row in range(rowspan - 1):
                    for col in range(cur_col, cur_col + colspan):
                        header_lists[col].append(None)
            cur_col += colspan

    headers = [' '.join(filter(lambda s: s is not None, hl)) for hl in header_lists]

    return headers, row

def location_from_column(col, path=None):

    url = ''
    coords = scrape_wikipedia_element(col, path)
    if coords:
        return coords + (url,)

    location_link = col.find('a')
    if location_link:
        url = expand_wikipedia_url(location_link.attrs['href'])
        coords = scrape_wikipedia_url(url, path)
        if coords:
            lat, lon = coords
        else:
            lat, lon = '', ''
    else:
        lat, lon = '', ''

    return lat, lon, url

def scrape_wikipedia_table_url(url, table_index=0, preview=False, row_filter=None, limit=0, path=None,

                               magnitude_column=None, location_column=None, name_column=None,
                               backup_location_column=None,

                               out=None, write_headers=True, out_transform=None):

    with urlopen(url) as fobj:
        soup = BeautifulSoup(fobj, 'lxml')

        tables = soup.find_all('table', class_='sortable')
        table = tables[table_index]

        headers, first_data_row = parse_table_headers(table)

        if preview:
            print(headers)
            raise SystemExit

        num_cols = len(first_data_row.find_all(['th', 'td']))

        if not magnitude_column:
            raise ValueError('Must specify magnitude_column')
        elif magnitude_column not in headers:
            raise ValueError('magnitude_column not in headers')

        if not location_column:
            raise ValueError('Must specify location_column')
        elif location_column not in headers:
            raise ValueError('location_column not in headers')

        mag_index = headers.index(magnitude_column)
        loc_index = headers.index(location_column)
        if name_column:
            name_index = headers.index(name_column)
        if backup_location_column:
            backup_loc_index = headers.index(backup_location_column)

        out_headers = ['Name', 'Magnitude', 'Latitude', 'Longitude', 'Loc_url', 'Loc_url2']
        if out:
            if isinstance(out, str):
                fobj = open(out, 'w')
                writer = csv.DictWriter(fobj, delimiter='\t' if out.lower().endswith('.tsv') else ',',
                                        fieldnames=out_headers)
            else:
                fobj = out
                writer = csv.DictWriter(fobj, delimiter=',', fieldnames=out_headers)
            writerow = writer.writerow
        else:
            writerow = lambda row: print('\t'.join([row[h] for h in out_headers]))

        if write_headers:
            writerow()
        for i, row in enumerate(itertools.chain([first_data_row], first_data_row.find_next_siblings('tr'))):
            cols = row.find_all(['th', 'td'])
            if len(cols) < num_cols:
                continue
            if row_filter and not row_filter(cols):
                continue
            if limit and i >= limit:
                break

            if name_column:
                name = ' '.join(cols[name_index].stripped_strings)
            else:
                name = ''

            mag_col = cols[mag_index]
            mag_el = mag_col.find('span', class_='sorttext')
            if not mag_el:
                mag_el = mag_col
            magnitude = next(mag_el.stripped_strings)

            lat, lon, loc_url = location_from_column(cols[loc_index], path=path)
            loc_url2 = ''
            if not lat or not lon:
                if backup_location_column:
                    lat, lon, loc_url2 = location_from_column(cols[backup_loc_index], path=path)
                else:
                    lat, lon, loc_url2 = '', '', ''

            out_row = {'Name': name, 'Magnitude': magnitude, 'Latitude': lat,
                       'Longitude': lon, 'Loc_url': loc_url, 'Loc_url2': loc_url2}
            if out_transform:
                out_row = out_transform(out_row)
            writerow(out_row)

        if out and isinstance(out, str):
            fobj.close()

    return []

def scrape_coordinates(urlfile):
    urls = open(urlfile, 'r').read().split('\n')
    url_map = {}
    for url in urls:
        if url in url_map:
            yield url, url_map[url]
        else:
            loc = url_map[url] = scrape_url(url)
            yield url, loc

def format_coords(coordinates):
    if coordinates:
        lat, lon = coordinates
        return '%s\t%s' % (lat, lon)
    else:
        return ''

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('urlfile')
    #  For Wikipedia list scraping
    parser.add_argument('-i', '--table-index', type=int, default=0)
    parser.add_argument('-p', '--preview', action='store_true')
    parser.add_argument('-m', '--magnitude-column')
    parser.add_argument('-l', '--location-column', default='Location')
    parser.add_argument('--backup-location-column')
    parser.add_argument('-n', '--name-column')
    parser.add_argument('--limit', type=int, default=0)
    parser.add_argument('-o', '--out')

    args = parser.parse_args()
    url = args.urlfile

    m = wikipedia_url_re.match(url)
    if m:
        try:
            scrape_wikipedia_table_url(url, args.table_index, preview=args.preview,
                            magnitude_column=args.magnitude_column, location_column=args.location_column,
                            name_column=args.name_column, backup_location_column=args.backup_location_column,
                            limit=args.limit, out=args.out)
        except ValueError as ex:
            import traceback
            traceback.print_exc()
            print(format_coords(scrape_url(url)))
    elif os.path.isfile(url):
        for url, coordinates in scrape_coordinates(url):
            print(format_coords(coordinates))
    else:
        print(format_coords(scrape_url(url)))

if __name__ == "__main__":
    main()
