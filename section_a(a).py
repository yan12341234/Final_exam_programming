import numpy as np
import pandas as pd


#----------------------------------------------------------
#numpy
#----------------------------------------------------------
# simulated hourly grid demand (kW)
# row represent two charging hubs, columns represent hours (11:00 to 18:00)
grid_load = np.array([
    [30, 40, 60, 80, 35, 55, 30, 85],
    [60, 80, 85, 50, 70, 45, 60, 65]],
dtype=float
)

#1. 2D array slicing
# select both hubs and hours readings (12:00 to 17:00)
peak_load = grid_load[:, 1:7]
print("Peak Load Demand(kW):")
print(peak_load)

#2. Boolean masking
#select temperature > 45
battery_temperature = np.array([30, 40, 45, 60, 70 ])
high_temperature = battery_temperature[battery_temperature > 45]

print("\nBattery temperature above 45°C.:", high_temperature)

#--------------------------------------------------------
#pandas
#--------------------------------------------------------

# data charging session (simulated)
df = pd.DataFrame({
    "Charger_Type": ["AC", "DC", "DC", "AC"],
    "Power_Rate_kW": [5.2, 33.9, None, 28.5],
    "Revenue_MYR": [15, 50.5, 20, 45.5]
})

#missing value
print(df.isnull().sum())

#1. Median imputation for missing value replacement
power_rate_median = df["Power_Rate_kW"].median()
df["Power_Rate_kW"] = df["Power_Rate_kW"].fillna(power_rate_median)

#2. group-wise revenue aggregration (group sessions by charger type & sum revenues)
total_revenue = (df.groupby("Charger_Type")["Revenue_MYR"].sum())

print("\nPower Rate values after median imputation: ")
print(df["Power_Rate_kW"].tolist())

print("\nTotal charging revenue(MYR): ")
print(total_revenue)
