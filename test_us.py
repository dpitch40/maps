import plot
import numpy as np

plot.plot_us_chloropleth('data/Census.csv', 'population.png', 'Oranges',
                         bins=np.geomspace(10, 10000000, 7))