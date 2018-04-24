import re
from operator import itemgetter

point_pattern_re = re.compile(r'(\d+)[°o](\d+(?:\.\d+)?)[\'′](?:(\d+(?:\.\d+)?)["″])?([NESW])')

def parse_latlon(s):
    try:
        return float(s)
    except ValueError:
        m = point_pattern_re.match(s)
        if m is None:
            raise ValueError('Could not parse latitude/longitude: %r' % s)

        degs, mins, secs, polarity =  m.groups()
        if secs:
            latlon = float(degs) + float(mins) / 60 + float(secs) / (60 * 60)
        else:
            latlon = float(degs) + float(mins) / 60

        if polarity in 'SW':
            latlon *= -1

        return latlon

def parse_points(l):
    for lat, lon in l:
        yield parse_latlon(lat), parse_latlon(lon)

def parse_points_with_magnitude(l):
    for lat, lon, magnitude in l:
        yield parse_latlon(lat), parse_latlon(lon), int(magnitude)

class ColorBins(object):
    def __init__(self, bins_dict, default):
        self.bins = sorted(list(bins_dict.items()), key=itemgetter(0), reverse=True)
        self.default = default

    def __call__(self, magnitude):
        for binmag, style in self.bins:
            if magnitude >= binmag:
                return style
        else:
            return self.default

def plot_points_with_magnitude(map_, points, bins, scale ,**style):
    for lat, lon, magnitude in points:
        size, color = bins(magnitude)

        map_.plot(lon, lat, latlon=True, markersize=size * scale, c=color, **style)
