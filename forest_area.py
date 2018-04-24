import plot
import util

import numpy as np

bins = np.arange(0, 110, 10)

plot.plot_world_chloropleth('forest_data.csv', 'forest-area.png', 'Greens', bins)
