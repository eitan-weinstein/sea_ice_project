import numpy as np
import xarray as xr # opening netcdf files as labeled multidimensional arrays
import pandas as pd
import subprocess
import matplotlib.pyplot as plt
import cftime
from scipy.stats import linregress

def sea_ice_correlations(independent_var, saving):
    
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

    # Calculate number of rows and columns for subplots
    num_plots = len(ds_avg_list)
    num_cols = 1  # Number of columns in subplot grid
    num_rows = num_plots // num_cols + (1 if num_plots % num_cols > 0 else 0)  # Calculate number of rows

    # Calculate figure size based on number of rows and columns
    fig_width = 10 * num_cols
    fig_height = 8 * num_rows

    # Create the figure and subplots
    fig, axes = plt.subplots(num_rows, num_cols, figsize=(fig_width, fig_height))

    # Plot linear regressions between variables
    for i, ax in enumerate(axes.flat):
        if i < num_plots:
            # Perform linear regression on the two variables
            y = ds_avg_list[i]
            slope, intercept = np.polyfit(x, y, 1)

            # Create a regression line and calculate a linear regression
            regression_line = slope * x + intercept
            lin_regression = linregress(x, y)
            r = lin_regression[2]

            # Plot linear regression
            ax.scatter(x=x, y=y)
            ax.set_xlabel(indep_title + ' ' + indep_units)
            ax.set_ylabel(ds_list[i].long_name + ' [' + ds_list[i].units + ']')
            ax.set_title(ds_list[i].long_name + ' vs ' + indep_title)
            ax.plot(x, regression_line, color='red', label='Linear Regression, r = {:.3f}'.format(r))
            ax.legend()
            ax.grid()

    # Adjust layout
    plt.tight_layout()

    # Conditionally save figure
    if saving:
        filename = './SImon_vars_vs_{}.png'.format(indep_title)
        plt.savefig(filename)

    # Show plot
    plt.show()

sea_ice_correlations('tos', saving=True)