import re
import argparse
import csv
from operator import itemgetter

from mpl_toolkits.basemap import Basemap
# https://matplotlib.org/basemap/index.html
import matplotlib.pyplot as plt

import util

default_bins = util.ColorBins({30000: (5, 'blue'),
                               40000: (7, 'cyan'),
                               50000: (9, 'lime'),
                               60000: (11, 'yellow'),
                               80000: (13, 'orange'),
                               100000: (15, 'red')}, (3, 'purple'))

def load_string_points(datafile):
    with open(datafile, 'r') as fobj:
        reader = csv.reader(fobj)
        yield from reader

def plot_map(map_type, datafile, dest, custom_style, scale, projection, resolution, descending):
    default_style = {'linestyle': 'none',
                     'marker': 'o',
                     'markeredgecolor': 'black',
                     'markeredgewidth': 0.3 * scale}

    style = default_style.copy()
    style.update(custom_style)

    if map_type == 'prop_symbol':
        plt.figure(figsize=(40 * scale, 40 * scale))
        m = Basemap(projection=projection, lon_0=0, resolution=resolution)
        m.drawmapboundary(linewidth=0.4 * scale)
        m.drawcoastlines(linewidth=0.4 * scale, color='black')
        m.drawcountries(linewidth=0.3 * scale, color='black')

        points = util.parse_points_with_magnitude(load_string_points(datafile))
        points = sorted(list(points), reverse=descending, key=itemgetter(2))
        util.plot_points_with_magnitude(m, points, default_bins, scale, **style)

    plt.savefig(dest, bbox_inches='tight')

def main():

    parser = argparse.ArgumentParser()

    parser.add_argument('map_type', choices=['prop_symbol'])
    parser.add_argument('datafile')
    parser.add_argument('-o', '--dest', default='map.png')
    parser.add_argument('--style', nargs=2, action='append', default=[])
    parser.add_argument('--scale', type=int, default=1)
    parser.add_argument('-p', '--proj', default='robin')
    parser.add_argument('-r', '--resolution', default='l')
    parser.add_argument('-d', '--descending', action='store_true')

    args = parser.parse_args()

    plot_map(args.map_type, args.datafile, args.dest, args.style, args.scale, args.proj, args.resolution,
                    args.descending)

if __name__ == "__main__":
    main()
