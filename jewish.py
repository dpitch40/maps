import plot
import numpy as np

plot.plot_us_chloropleth('data/jewish.csv', 'jewish.png', 'YlGnBu',
                         bins=[0, 0.25, 0.5, 1, 2, 4, 8, 16, 100],
                         nodatacolor='#ffffff')