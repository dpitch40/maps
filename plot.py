import re
import argparse
import csv
from operator import itemgetter

import matplotlib as mpl
from mpl_toolkits.basemap import Basemap
# https://matplotlib.org/basemap/index.html
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from geonamescache import GeonamesCache
from matplotlib.patches import Polygon
from matplotlib.collections import PatchCollection

import util

default_size = 40
default_map_linewidth = 0.4
default_border_linewidth = 0.3

def plot_prop_symbols(datafile, dest, bins, custom_style={}, scale=1,
                      projection='robin', resolution='l', descending=False):
    """Format: CSV with 'Latitude', 'Longitude', and 'Magnitude' columns."""

    default_style = {'linestyle': 'none',
                     'marker': 'o',
                     'markeredgecolor': 'black',
                     'markeredgewidth': 0.3 * scale}

    style = default_style.copy()
    style.update(custom_style)

    plt.figure(figsize=(default_size * scale, default_size * scale))
    m = Basemap(projection=projection, lon_0=0, resolution=resolution)
    m.drawmapboundary(linewidth=default_map_linewidth * scale)
    m.drawcoastlines(linewidth=default_map_linewidth * scale, color='black')
    m.drawcountries(linewidth=default_border_linewidth * scale, color='black')

    df = pd.read_csv(datafile, converters={'Latitude': util.parse_latlon,
                                           'Longitude': util.parse_latlon})

    for f in df.sort_values(by=['Magnitude'], ascending=not descending).itertuples():
        size, color = bins(f.Magnitude)

        m.plot(f.Longitude, f.Latitude, latlon=True, markersize=size * scale, c=color, **style)

    plt.savefig(dest, bbox_inches='tight')

def plot_world_chloropleth(datafile, dest, colorscale, bins, blankcolor='#dddddd',
                           scale=1, projection='robin', resolution='l'):
    """Format: CSV with 'Country Name', 'Country Code', and 'Magnitude' columns."""

    # See http://ramiro.org/notebook/basemap-choropleth/
    shapefile = 'ne_10m_admin_0_countries_lakes/ne_10m_admin_0_countries_lakes'
    num_colors = len(bins) - 1

    gc = GeonamesCache()
    iso3_codes = list(gc.get_dataset_by_key(gc.get_countries(), 'iso3').keys())

    df = pd.read_csv(datafile)
    df.set_index('Country Code', inplace=True)
    df = df.ix[iso3_codes].dropna() # Filter out non-countries and missing values.

    values = df[df.columns[1]]
    # https://matplotlib.org/api/pyplot_summary.html#matplotlib.pyplot.colormaps
    cm = plt.get_cmap(colorscale)
    scheme = [cm(i / num_colors) for i in range(num_colors)]
    df['bin'] = np.digitize(values, bins) - 1
    df.sort_values('bin', ascending=False).head(10)

    # This doesn't work, is it important?
    # mpl.style.use('map')
    fig = plt.figure(figsize=(default_size * scale, default_size * scale))

    ax = fig.add_subplot(111, facecolor='w', frame_on=False)

    m = Basemap(lon_0=0, projection=projection, resolution=resolution)
    m.drawmapboundary(linewidth=default_map_linewidth * scale, color='w')

    m.readshapefile(shapefile, 'units', color='#444444', linewidth=default_border_linewidth * scale)
    for info, shape in zip(m.units_info, m.units):
        iso3 = info['ADM0_A3']
        if iso3 not in df.index:
            color = blankcolor
        else:
            color = scheme[df.ix[iso3]['bin']]

        patches = [Polygon(np.array(shape), True)]
        pc = PatchCollection(patches)
        pc.set_facecolor(color)
        ax.add_collection(pc)

    plt.savefig(dest, bbox_inches='tight')

def main():

    parser = argparse.ArgumentParser()

    parser.add_argument('map_type', choices=['prop_symbol', 'chloropleth'])
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
