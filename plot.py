import re
import argparse
import csv

from mpl_toolkits.basemap import Basemap
import matplotlib.pyplot as plt

import util

default_bins = util.ColorBins({2000: (5, 'blue'),
                               3000: (7, 'cyan'),
                               4000: (9, 'lime'),
                               5000: (11, 'yellow'),
                               6000: (13, 'orange'),
                               7000: (15, 'red')}, (3, 'purple'))

default_style = {'linestyle': 'none',
                 'marker': 'o',
                 'markeredgecolor': 'black',
                 'markeredgewidth': 0.3}

base_size = 40
base_line_width = 0.3

def load_string_points(datafile):
    with open(datafile, 'r') as fobj:
        reader = csv.reader(fobj)
        yield from reader

def plot_map(map_type, datafile, dest, custom_style, scale, projection, resolution):
    style = default_style.copy()
    style.update(custom_style)

    if map_type == 'prop_symbol':
        plt.figure(figsize=(base_size * scale, base_size * scale))
        m=Basemap(projection=projection, lon_0=0, resolution=resolution)
        m.drawmapboundary(linewidth=base_line_width * scale)
        m.drawcoastlines(linewidth=base_line_width * scale, color='black')
        m.drawcountries(linewidth=base_line_width * scale, color='black')

        points = util.parse_points_with_magnitude(load_string_points(datafile))
        util.plot_points_with_magnitude(m, points, default_bins, **style)
            
    plt.savefig(dest, bbox_inches='tight')

def main():

    parser = argparse.ArgumentParser()

    parser.add_argument('map_type', choices=['prop_symbol'])
    parser.add_argument('datafile')
    parser.add_argument('--dest', default='map.png')
    parser.add_argument('--style', nargs=2, action='append', default=[])
    parser.add_argument('--scale', type=int, default=1)
    parser.add_argument('--proj', default='robin')
    parser.add_argument('--resolution', default='l')

    args = parser.parse_args()

    plot_map(args.map_type, args.datafile, args.dest, args.style, args.scale, args.proj, args.resolution)

if __name__ == "__main__":
    main()
