"""Clean raw data, calculate metrics and export the results"""

import pandas as pd

#---------------------------------------------
# data cleaning
#---------------------------------------------

def process_ev_data(df):
    """replace missing values by median, validate categorical columns"""
    df = df.copy()

    numeric_columns = [
        "Start_Hour",
        "Duration_Mins",
        "Energy_kWh",
        "Overstay_Mins",
        "Battery_Temp_C",
    ]

    # check missing values
    print("\n Missing Values: ")
    print(df.isnull().sum())

    # replace missing values by medians
    for column in numeric_columns:
        median_value = df[column].median()

        if pd.isna(median_value):
            raise ValueError(f"Invalid values in {column}.")

        df[column] = df[column].fillna(median_value)


    #check missing value after imputation
    print("\nMissing Values after imputation: ")
    print(df[numeric_columns].isnull().sum())

    # validate categorical columns
    categorical_columns = {
        "Charger_Type": ["AC", "DC"],
        "User_Type": ["Student", "Staff", "Visitor"],
        "Grid_Status_Label": ["Normal", "Grid_Surge", "Overheated"],
    }

    for column, allowed_values in categorical_columns.items():
        df[column] = df[column].astype("string").str.strip()

        if not df[column].isin(allowed_values).all():
            raise ValueError(f"Invalid values in {column}.")


    #--------------------------------------------
    # feature engineering
    #--------------------------------------------
    # convert charging duration from minutes to hours
    if (df["Duration_Mins"] <= 0).any():
        raise ValueError("Duration Minutes must be greater than 0 minutes.")
    df["Duration_Hours"] = df["Duration_Mins"] / 60

    # calculate power rate and carbon savings
    df["Power_Rate_kW"] = (df["Energy_kWh"] / df["Duration_Hours"])
    df["Carbon_Savings_kgCO2"] = (df["Energy_kWh"] * 0.475).round(2)

    #calculate base fee for each charging session
    df["Base_Rate_MYR"] = df["Charger_Type"].map({"AC": 6, "DC": 15})
    df["Base_Fee_MYR"] = df["Duration_Hours"] * df["Base_Rate_MYR"]


    # peak hour surcharge: 25%(according to the clean dataset provided), from 12:00 to 17:59
    df["Start_Hour"] = df["Start_Hour"].round().astype(int)
    peak_hours = (df["Start_Hour"] >= 12) & (df["Start_Hour"] < 18)

    df["Peak_Surge_MYR"] = 0.0
    df.loc[peak_hours, "Peak_Surge_MYR"] = (
        df.loc[peak_hours, "Base_Fee_MYR"] * 0.25
    )

    # charge MYR0.50 per minute after first 15 overstay mins
    overstay_charge = df["Overstay_Mins"] > 15
    df["Overstay_Fee_MYR"] = 0.0
    df.loc[overstay_charge, "Overstay_Fee_MYR"] = (
        df.loc[overstay_charge, "Overstay_Mins"] - 15) * 0.5

    # round the final bill to two decimal place
    df["Net_Billable_MYR"] = (
            df["Base_Fee_MYR"]
            + df["Peak_Surge_MYR"]
            + df["Overstay_Fee_MYR"]
    ).round(2)

    return df

if __name__ == "__main__":
    try:
        ev_data = pd.read_csv("ev_campus_dataset.csv")
        clean_data = process_ev_data(ev_data)
        output_file = "cleaned_energy_sales_data.csv"
        clean_data.to_csv(output_file, index=False)
        print("\nSummary Statistics: ")
        print(clean_data.describe().round(2).to_string())
        print(f"\nExported to {output_file}")

    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"Data pipeline error: {error}")