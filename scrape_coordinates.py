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

def scrape_wikipedia_url(url):
    try:
        with urlopen(url) as fobj:
            time.sleep(1)
            soup = BeautifulSoup(fobj, 'lxml')
            coords_span = soup.find('span', id='coordinates')
            if coords_span is None:
                return None

            lat = coords_span.find('span', class_='latitude')
            if lat:
                lat = lat.string
            lon = coords_span.find('span', class_='longitude')
            if lon:
                lon = lon.string

            return lat, lon
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
                cur_header_info.append((next(header.stripped_strings), int(colspan), int(rowspan)))
        else:
            break
        header_info.append(cur_header_info)
        row = row.find_next_sibling('tr')

    num_rows = len(header_info)
    num_cols = max(sum(map(operator.itemgetter(1), r)) for r in header_info)

    header_lists = [[] for i in range(num_cols)]
    for info in header_info:
        cur_col = 0
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

def location_from_column(col):
    location_link = col.find('a')
    url = ''
    if location_link:
        url = expand_wikipedia_url(location_link.attrs['href'])
        coords = scrape_wikipedia_url(url)
        if coords:
            lat, lon = coords
        else:
            lat, lon = '', ''
    else:
        lat, lon = '', ''

    return lat, lon, url

def scrape_wikipedia_table_url(url, table_index, preview, magnitude_column, location_column,
                               name_column, limit, backup_location_column, out):

    with urlopen(url) as fobj:
        soup = BeautifulSoup(fobj, 'lxml')

        tables = soup.find_all('table')
        table = tables[table_index]

        headers, first_data_row = parse_table_headers(table)

        if preview:
            print(headers)
            raise SystemExit

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

        if out:
            fobj = open(out, 'w')
            writer = csv.writer(fobj, delimiter='\t' if out.lower().endswith('.tsv') else ',')
            writerow = writer.writerow
        else:
            writerow = lambda row: print('\t'.join(row))

        writerow(['Name', 'Magnitude', 'Latitude', 'Longitude', 'Loc_url', 'Loc_url2'])
        for i, row in enumerate(itertools.chain([first_data_row], first_data_row.find_next_siblings('tr'))):
            cols = row.find_all(['th', 'td'])
            if name_column:
                name = ' '.join(cols[name_index].stripped_strings)
            else:
                name = ''
            magnitude = next(cols[mag_index].stripped_strings)
            lat, lon, loc_url = location_from_column(cols[loc_index])
            loc_url2 = ''
            if not lat and backup_location_column:
                lat, lon, loc_url2 = location_from_column(cols[backup_loc_index])
            else:
                lat, lon, loc_url2 = '', '', ''

            location_link = cols[loc_index].find('a')
            if location_link:
                coords = scrape_wikipedia_url(expand_wikipedia_url(location_link.attrs['href']))
                if coords:
                    lat, lon = coords
                else:
                    lat, lon = '', ''
            else:
                lat, lon = '', ''
            writerow([name, magnitude, lat, lon, loc_url, loc_url2])
            if limit and i >= limit - 1:
                break

        if out:
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
            scrape_wikipedia_table_url(url, args.table_index, args.preview,
                            args.magnitude_column, args.location_column,
                            args.name_column, args.limit, args.backup_location_column, args.out)
        except ValueError as ex:
            print(format_coords(scrape_url(url)))
    elif os.path.isfile(url):
        for url, coordinates in scrape_coordinates(url):
            print(format_coords(coordinates))
    else:
        print(format_coords(scrape_url(url)))

if __name__ == "__main__":
    main()
