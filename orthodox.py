import plot
import numpy as np

plot.plot_us_chloropleth('data/orthodox.csv', 'orthodox.png', 'YlGnBu',
                         bins=[0, 0.0625, 0.25, 1, 4, 16, 100],
                         nodatacolor='#ffffff')