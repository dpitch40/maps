import plot
import numpy as np

plot.plot_us_chloropleth('data/Census.csv', 'population.png', 'Oranges',
                         bins=np.geomspace(100, 10000000, 6))