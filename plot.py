import re
import argparse
from operator import itemgetter
from collections import defaultdict

import matplotlib as mpl
from mpl_toolkits.basemap import Basemap
# https://matplotlib.org/basemap/index.html
import matplotlib.pyplot as plt
import matplotlib.gridspec as gs
import numpy as np
import pandas as pd

from geonamescache import GeonamesCache
from matplotlib.patches import Polygon
from matplotlib.collections import PatchCollection

import util

default_size = 40
default_map_linewidth = 0.4
default_border_linewidth = 0.3

equivalencies = {2158: 2270, # Wade Hampton Census Area = Kusilvak Census Area, AK
                 46102: 46113, # Oglala Lakota County = Shannon County, SD
                }
equivalencies.update(dict([(v, k) for k, v in equivalencies.items()]))

def plot_dots(datafile, dest, size=6, color='red', scale=1,
              projection='robin', resolution='l', descending=False, inputkwargs={}):
    """Format: CSV with 'Latitude' and 'Longitude' columns."""

    style = {'linestyle': 'none',
             'marker': 'o',
             'markeredgecolor': 'black',
             'markeredgewidth': 0.3 * scale}

    plt.figure(figsize=(default_size * scale, default_size * scale))
    m = Basemap(projection=projection, lon_0=0, resolution=resolution)
    m.drawmapboundary(linewidth=default_map_linewidth * scale)
    m.drawcoastlines(linewidth=default_map_linewidth * scale, color='black')
    m.drawcountries(linewidth=default_border_linewidth * scale, color='black')

    df = pd.read_csv(datafile, converters={'Latitude': util.parse_latlon,
                                           'Longitude': util.parse_latlon},
                     usecols=['Latitude', 'Longitude'], **inputkwargs)
    coords = []

    for f in df.itertuples():
        coords.append((f.Latitude, f.Longitude))

    for latitude, longitude in coords:
        m.plot(longitude, latitude, latlon=True, markersize=size * scale, c=color, **style)

    plt.savefig(dest, bbox_inches='tight')

def plot_prop_symbols(datafile, dest, bins, custom_style={}, scale=1,
                      projection='robin', resolution='l', descending=False, usecol='Magnitude',
                      inputkwargs={}):
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
                                           'Longitude': util.parse_latlon},
                     usecols=['Latitude', 'Longitude', usecol], **inputkwargs)
    magnitudes = defaultdict(int)

    for f in df.itertuples():
        magnitude = getattr(f, usecol)
        if pd.notna(magnitude):
            magnitudes[(f.Latitude, f.Longitude)] += magnitude

    for (latitude, longitude), magnitude in sorted(magnitudes.items(), key=itemgetter(1),
                                                   reverse=descending):
            size, color = bins(magnitude)

            m.plot(longitude, latitude, latlon=True, markersize=size * scale, c=color, **style)

    plt.savefig(dest, bbox_inches='tight')

def plot_world_chloropleth(datafile, dest, colorscale, bins, nodatacolor='#dddddd',
                           scale=1, projection='robin', resolution='l', usecol='Magnitude',
                           inputkwargs={}):
    """Format: CSV with 'Country Name', 'Country Code', and 'Magnitude' columns."""

    # See http://ramiro.org/notebook/basemap-choropleth/
    shapefile = 'ne_10m_admin_0_countries_lakes/ne_10m_admin_0_countries_lakes'
    num_colors = len(bins) - 1

    gc = GeonamesCache()
    iso3_codes = list(gc.get_dataset_by_key(gc.get_countries(), 'iso3').keys())

    df = pd.read_csv(datafile, **inputkwargs)
    df.set_index('Country Code', inplace=True)
    df = df.reindex(iso3_codes)#.dropna() # Filter out non-countries and missing values.

    values = df[usecol]
    # https://matplotlib.org/api/pyplot_summary.html#matplotlib.pyplot.colormaps
    cm = plt.get_cmap(colorscale)
    scheme = [cm(i / num_colors) for i in range(num_colors)]
    scheme.append(nodatacolor)
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
            color = nodatacolor
        else:
            color = scheme[df.loc[iso3]['bin']]

        patches = [Polygon(np.array(shape), True)]
        pc = PatchCollection(patches)
        pc.set_facecolor(color)
        ax.add_collection(pc)

    plt.savefig(dest, bbox_inches='tight')

def plot_us_chloropleth(datafile, dest, colorscale, bins, nodatacolor='#dddddd',
                        scale=1, resolution='l', usecol='Magnitude',
                        inputkwargs={}):
    """Format: CSV with 'Geography', 'Geoid', and 'Magnitude' columns."""

    shapefile = 'cb_2017_us_county_500k/cb_2017_us_county_500k'
    num_colors = len(bins) - 1

    gc = GeonamesCache()
    # iso3_codes = list(gc.get_dataset_by_key(gc.get_countries(), 'iso3').keys())

    df = pd.read_csv(datafile, **inputkwargs)
    df.set_index('Geoid', inplace=True)
    # df = df.loc[iso3_codes].dropna() # Filter out non-countries and missing values.

    values = df[usecol]
    # https://matplotlib.org/api/pyplot_summary.html#matplotlib.pyplot.colormaps
    cm = plt.get_cmap(colorscale)
    scheme = [cm(i / num_colors) for i in range(num_colors)]
    df['bin'] = np.digitize(values, bins) - 1
    df.sort_values('bin', ascending=False).head(10)

    # This doesn't work, is it important?
    # mpl.style.use('map')
    fig = plt.figure(figsize=(default_size * scale, default_size * scale))
    grid = gs.GridSpec(nrows=10, ncols=10)

    for lon_0, lat_0, gridpos, llcrnrlon, llcrnrlat, urcrnrlon, urcrnrlat in \
        [(-98.5795, 39.828, grid[:-2, :], -121, 22, -64, 47), # Contiguous US
         (-160, 63.5, grid[-4:, :6], -185.3, 49, -116, 65.5), # Alaska
         (-158, 21, grid[-3:, 6:], -161, 18, -154, 23)]: # Hawaii

        m = Basemap(lon_0=lon_0, lat_0=lat_0, projection='ortho', resolution=resolution)
        ax = fig.add_subplot(gridpos, facecolor='#00000000', frame_on=False)

        m.readshapefile(shapefile, 'units', color='#444444', linewidth=default_border_linewidth * scale)
        for info, shape in zip(m.units_info, m.units):
            geoid = int(info['GEOID'])
            if geoid in equivalencies and geoid not in df.index:
                geoid = equivalencies[geoid]

            if geoid not in df.index:
                color = nodatacolor
            else:
                color = scheme[df.loc[geoid]['bin']]

            patches = [Polygon(np.array(shape), True)]
            pc = PatchCollection(patches)
            pc.set_facecolor(color)
            ax.add_collection(pc)

        xmin, ymin = m(llcrnrlon, llcrnrlat)
        xmax, ymax = m(urcrnrlon, urcrnrlat)

        ax.set_xlim(xmin, xmax)
        ax.set_ylim(ymin, ymax)


    plt.savefig(dest, bbox_inches='tight')

def plot_us_state_chloropleth(datafile, dest, colorscale, bins, nodatacolor='#dddddd',
                              scale=1, resolution='l', usecol='Magnitude',
                              inputkwargs={}):
    """Format: CSV with 'Geography', 'AFFGEOID', and 'Magnitude' columns."""

    shapefile = 'cb_2017_us_state_500k/cb_2017_us_state_500k'
    num_colors = len(bins) - 1

    gc = GeonamesCache()

    df = pd.read_csv(datafile, **inputkwargs)
    df.set_index('AFFGEOID', inplace=True)

    values = df[usecol]
    # https://matplotlib.org/api/pyplot_summary.html#matplotlib.pyplot.colormaps
    cm = plt.get_cmap(colorscale)
    scheme = [cm(i / num_colors) for i in range(num_colors)]
    df['bin'] = np.digitize(values, bins) - 1
    df.sort_values('bin', ascending=False).head(10)

    fig = plt.figure(figsize=(default_size * scale, default_size * scale))
    grid = gs.GridSpec(nrows=10, ncols=10)

    for lon_0, lat_0, gridpos, llcrnrlon, llcrnrlat, urcrnrlon, urcrnrlat in \
        [(-98.5795, 39.828, grid[:-2, :], -121, 22, -64, 47), # Contiguous US
         (-160, 63.5, grid[-4:, :6], -185.3, 49, -116, 65.5), # Alaska
         (-158, 21, grid[-3:, 6:], -161, 18, -154, 23)]: # Hawaii

        m = Basemap(lon_0=lon_0, lat_0=lat_0, projection='ortho', resolution=resolution)
        ax = fig.add_subplot(gridpos, facecolor='#00000000', frame_on=False)

        m.readshapefile(shapefile, 'units', color='#444444', linewidth=default_border_linewidth * scale)
        for info, shape in zip(m.units_info, m.units):
            geoid = info['AFFGEOID']
            if geoid in equivalencies and geoid not in df.index:
                geoid = equivalencies[geoid]

            if geoid not in df.index:
                color = nodatacolor
            else:
                color = scheme[df.loc[geoid]['bin']]

            patches = [Polygon(np.array(shape), True)]
            pc = PatchCollection(patches)
            pc.set_facecolor(color)
            ax.add_collection(pc)

        xmin, ymin = m(llcrnrlon, llcrnrlat)
        xmax, ymax = m(urcrnrlon, urcrnrlat)

        ax.set_xlim(xmin, xmax)
        ax.set_ylim(ymin, ymax)

    plt.savefig(dest, bbox_inches='tight')
