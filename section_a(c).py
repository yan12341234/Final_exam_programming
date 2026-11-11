import numpy as np
import pandas as pd

df = pd.read_csv("ev_campus_dataset.csv")
#----------------------------------------------------------
#numpy
#----------------------------------------------------------
#calculate average charging power for each session
duration_hours = df["Duration_Mins"].where(df["Duration_Mins"] > 0) / 60
df["Power_Rate_kW"] = df["Energy_kWh"] / duration_hours

#1. 2D array slicing
hourly_data = (
    df.groupby("Start_Hour")[["Power_Rate_kW", "Battery_Temp_C"]]
    .mean()
    .reindex()
    .to_numpy()
)

peak_data = hourly_data[12:18, :]
print("Peak-hour averages: charging power (kW) and temperature (°C)")
print(peak_data)

#2. Boolean masking
#compare temperature > 45
temperatures = df["Battery_Temp_C"].to_numpy()
high_temperature = temperatures[temperatures > 45]


print("Battery temperature above 45 celcius:", high_temperature)

#--------------------------------------------------------
#pandas
#--------------------------------------------------------

# data charging session (illustration data)
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

print("Power Rate values after median imputation: ")
print(df["Power_Rate_kW"].tolist())

print("\nTotal charging revenue(MYR): ")
print(total_revenue)
