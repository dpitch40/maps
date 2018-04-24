import re
import argparse
from urllib.request import urlopen
import time
import os.path

from bs4 import BeautifulSoup

google_maps_url_re = re.compile(r'https://www.google.com/maps/[^@]*@(\-?\d+\.\d+),(\-?\d+\.\d+)')

def scrape_url(url):
    if not url:
        return None
    if url.startswith('https://www.google.com/maps'):
        m = google_maps_url_re.match(url)
        if m:
            return m.groups()

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

def scrape_coordinates(urlfile):
    urls = open(urlfile, 'r').read().split('\n')
    for url in urls:
        yield url, scrape_url(url)

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('urlfile')

    args = parser.parse_args()

    if os.path.exists(args.urlfile):
        for url, coordinates in scrape_coordinates(args.urlfile):
            if coordinates:
                lat, lon = coordinates
                print('%s\t%s' % (lat, lon))
            else:
                print(coordinates)
    else:
        print(scrape_url(args.urlfile))

if __name__ == "__main__":
    main()
