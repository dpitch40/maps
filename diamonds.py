import util
import plot

bins = util.ColorBins({200000: (6, 'blue'),
                       500000: (8, 'cyan'),
                       1000000: (10, 'lime'),
                       2000000: (12, 'yellow'),
                       5000000: (14, 'orange'),
                       10000000: (16, 'red')}, (4, 'purple'))

plot.plot_prop_symbols('data/Diamonds.csv', 'maps/diamonds.png', bins, usecol='Production',
                        descending=True)
