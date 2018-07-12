import re
from operator import itemgetter

point_pattern_re = re.compile(r'~?(\d+)[°o]\s?(?:(\d+(?:\.\d+)?)\s?[\'′’]?)?\s?(?:(\d+(?:\.\d+)?)(?:["″”]|\'\')?)?\s?([NESW])')
float_re = re.compile(r'(\d+\.\d+)\s*°?\s*([NESW])')
comma_dot_re = re.compile(r'(\d+,\d+)')
split_re = re.compile(r'(?<=[NE])(?:\s?,?\s+|\s+,?\s*)(?=\d)')

def parse_latlon(s):
    try:
        return float(s)
    except ValueError:
        m = float_re.match(s)
        if m:
            latlon, polarity = m.groups()
            latlon = float(latlon)
        else:
            m = point_pattern_re.match(s)
            if m is None:
                return None
                # raise ValueError('Could not parse latitude/longitude: %r' % s)

            degs, mins, secs, polarity =  m.groups()
            if secs:
                latlon = float(degs) + float(mins) / 60 + float(secs) / (60 * 60)
            elif mins:
                latlon = float(degs) + float(mins) / 60
            else:
                latlon = float(degs)

        if polarity in 'SW':
            latlon *= -1

        return latlon

def parse_lat_and_lon(s):
    if s.count(',') > 1:
        s = comma_dot_re.subn(lambda m: m.group(1).replace(',', '.'), s)[0]
    try:
        lat, lon = s.strip().split(',')
    except ValueError:
        try:
            lat, lon = split_re.split(s)
        except ValueError as ex:
            raise ValueError('Unrecognized latlon: %r' % s)
    return parse_latlon(lat.strip()), parse_latlon(lon.strip())

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

    def __repr__(self):
        return 'ColorBins(%r, default=%r)' % (self.bins, self.default)
