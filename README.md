# Report Generator

## Report Examples

### Snapshot Plots

Example for **QuotaPctBarChart** class  
Shows percentage quota usage for each group:  
  
![soft\_quota\_pcnt.svg](Images/soft_quota_pcnt.svg)

Example for **UsageQuotaBarChart** class  
Shows disk usage and quota consumption for each group:  
  
![usage+quota\_bar.svg](Images/usage+quota_bar.svg)

Example for **UsagePieChart** class  
Shows usage pie with storage consumption of top groups:  
  
![usage\_pie.svg](Images/usage_pie.svg)

### Time Series Plots

Examples for **TrendChart** class  
  
Shows trend for quota consumption of all groups:  
  
![soft\_quota\_trend.svg](Images/soft_quota_trend.svg)
  
Shows trend for disk space usage of top groups:  
  
![usage\_trend.svg](Images/usage_trend.svg)

## Executables

### Lustre Reports

#### Collect Scripts

* lustre-group-quota-collect.py

#### Report Scripts

* lustre-weekly-reports.py
* lustre-monthly-reports.py
* lustre-migration-report.py

## Prerequisite

**Required**:  
* python36 - Python runtime
* matplotlib (3.1.1) - for plotting
* pandas (0.25.1) - for time series plots

**Optional**:  
* pip3 - installation of Python packages
* mysqlclient (1.4.4) - collecting and retrieving data from MySQL-DB
* getent - group resolution
* lfs quota - determining Lustre FS group quotas

### Build Tools Dependencies

__Python__:  

* python36-devel

__mysqlclient:__  

* gcc
* libmariadbclient-dev
