import plot
import numpy as np

plot.plot_us_chloropleth('data/inuit.csv', 'maps/inuit.png', 'Blues',
                         bins=[0, 0.08, 0.4, 2, 10, 50, 100],
                         inputkwargs={'encoding': 'latin'})