import util
import plot

bins = util.ColorBins({30000: (5, 'blue'),
                       40000: (7, 'cyan'),
                       50000: (9, 'lime'),
                       60000: (11, 'yellow'),
                       80000: (13, 'orange'),
                       100000: (15, 'red')}, (3, 'purple'))

plot.plot_prop_symbols('data/all_tunnels.csv', 'tunnels.png', bins)
