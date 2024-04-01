import os
import numpy as np
import xarray as xr
import subprocess
import matplotlib.pyplot as plt
import cftime
from scipy.stats import linregress
import warnings

def sea_ice_correlations(independent_var, saving):
    # Suppress FutureWarnings
    warnings.filterwarnings("ignore", category=FutureWarning)
    # Suppress SerializationWarnings
    warnings.filterwarnings("ignore", category=xr.SerializationWarning)
    
    # Create path structure for .nc files
    simon_base_path = '/glade/collections/cmip/CMIP6/CMIP/NOAA-GFDL/GFDL-ESM4/historical/r1i1p1f1/SImon/'
    repo_tag = '/gn/v20190726/'
    file_tag = '/*.nc'
    # Extract a list of variable names in the SImon repository
    simon_vars = subprocess.run(['ls', simon_base_path], capture_output=True, text=True).stdout.splitlines()


    # Convert the start and end dates to cftime objects
    start_date = cftime.DatetimeNoLeap(1991, 1, 1)
    end_date = cftime.DatetimeNoLeap(2010, 12, 31)

    # Iterate over the variables in SImon to import the files and process them
    ds_list = []
    ds_avg_list = []
    for var in simon_vars:
        # Set variable specific path
        path = simon_base_path + var + repo_tag + var + file_tag
        
        # Use a try-except statement in case there are no available files
        try:
            # Import data
            ds = xr.open_mfdataset(path)[var]

            # Select for the Southern Hemisphere
            ds = ds.where(ds.lat < 0)
            ds_list.append(ds)

            # Define the time range
            time_range = (ds.time >= start_date) & (ds.time <= end_date)
            ds = ds.sel(time=time_range)
            ds = ds.groupby('time.month').mean('time',skipna=1).mean('x',skipna=1).mean('y',skipna=1).values

            # Append the dataset to a list of all of the datasets
            ds_avg_list.append(ds)

            # Print status update
            print('Imported {}'.format(var))
        except:
            # In the case that the try fails, just skip it and keep going
            continue

    # Designate desired independent variable
    # Comparing against Sea Surface Temperature
    if independent_var == 'tos':
        indep_path= '/glade/collections/cmip/CMIP6/CMIP/NCAR/CESM2/historical/r1i1p1f1/Omon/tos/gr/v20190308/tos_Omon_CESM2_historical_r1i1p1f1_gr_185001-201412.nc'
        indep_title = 'Sea Surface Temperature'
        indep_units = '[K]'
    # Comparing against Sea Surface Salinity
    elif independent_var == 'sos':
        indep_path = '/glade/collections/cmip/CMIP6/CMIP/NCAR/CESM2/historical/r1i1p1f1/Omon/sos/gr/v20190308/sos_Omon_CESM2_historical_r1i1p1f1_gr_185001-201412.nc'
        indep_title = 'Sea Surface Salinity'
        indep_units = '[0.001]'

    # Extract and process independent variables
    ds_indep = xr.open_dataset(indep_path)
    ds_indep = ds_indep.where(ds_indep.lat < 0)
    time_range = (ds_indep.time >= start_date) & (ds_indep.time <= end_date)
    ds_indep = ds_indep.sel(time=time_range)
    x = ds_indep.groupby('time.month').mean('time',skipna=1).mean('lon',skipna=1).mean('lat',skipna=1)[independent_var]

    # Conditionally create directory to save figures
    if saving:
        save_folder = 'SImon_vars_vs_{}'.format(indep_title)
        os.makedirs(save_folder, exist_ok=True)

    # Plot linear regressions between variables
    for i in range(len(ds_avg_list)):
        # Create a new figure for each plot
        plt.figure()

        # Perform linear regression on the two variables
        y = ds_avg_list[i]
        slope, intercept = np.polyfit(x, y, 1)

        # Create a regression line and calculate a linear regression
        regression_line = slope * x + intercept
        lin_regression = linregress(x, y)
        r = lin_regression[2]

        # Plot linear regression
        plt.scatter(x=x, y=y)
        plt.xlabel(indep_title + ' ' + indep_units)
        plt.ylabel(ds_list[i].long_name + ' [' + ds_list[i].units + ']')
        plt.title(ds_list[i].long_name + ' vs ' + indep_title)
        plt.plot(x, regression_line, color='red', label='Linear Regression, r = {:.3f}'.format(r))
        plt.legend()
        plt.grid()

        # Conditionally save figure
        if saving:
            filename = os.path.join(save_folder, '{}_vs_{}.png'.format(simon_vars[i], indep_title))
            plt.savefig(filename)
        # If not saving, show the figure (in the Jupyter notebook)
        else:
            plt.show()
        # Close the figure to release memory
        plt.close()

# Call the function
sea_ice_correlations('tos', saving=True)