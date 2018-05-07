import plot
import numpy as np

usecol = 'Percent - Both sexes; Total population - Under 18 years'

plot.plot_us_chloropleth('data/ageandsex.csv', 'maps/children.png', 'YlGnBu',
                         bins=[0, 10, 15, 20, 25, 30, 35, 40, 50],
                         usecol=usecol,
                         inputkwargs={'encoding': 'latin',
                                      'usecols': ['Geoid', 'Geography', usecol]})