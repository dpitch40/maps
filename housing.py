import plot
import numpy as np

# usecol = "Percent; HOUSING TENURE - Occupied housing units - Renter-occupied"

# plot.plot_us_chloropleth('~/Downloads/ACS_16_5YR_DP04/ACS_16_5YR_DP04_with_ann.csv', 'households.png', 'OrRd',
#                          bins=np.arange(0, 110, 10),
#                          nodatacolor='#ffffff',
#                          usecol=usecol,
#                          inputkwargs={'encoding': 'latin',
#                                       'usecols': ['Geography', 'Geoid', usecol]})

usecol = "% renters"

plot.plot_us_chloropleth('~/Downloads/ACS_16_5YR_B25008/ACS_16_5YR_B25008_with_ann.csv', 'housing.png', 'OrRd',
                         bins=np.arange(0, 110, 10),
                         nodatacolor='#ffffff',
                         usecol=usecol,
                         inputkwargs={'encoding': 'latin',
                                      'usecols': ['Geography', 'Geoid', usecol]})
