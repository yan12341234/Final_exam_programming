"""Create three visualizations for EV report."""

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


def ev_plots_panels(df):
    """create three panel figures using simulated power(panel 1) and cleaned ev dataset."""
    sns.set_theme(style="whitegrid", context="notebook", font_scale=0.95)

    fig, axes = plt.subplots(
        3,
        1,
        figsize=(9, 11),
        height_ratios=[1, 1, 1.3],
        constrained_layout=True
    )
    fig.suptitle("Smart Energy & Electric Vehicle (EV)", fontsize=15, fontweight="bold")

    # panel 1: plot simulated hourly grid demand peaks and solar generation.
    hours = list(range(24))
    grid_demand = [
        20, 30, 40, 50, 60, 65, 70, 75, 80, 32, 40, 47,
        100, 108, 95, 80, 88, 35, 45, 55, 55, 70, 75, 83,
    ]

    solar_generation = [
        0, 0, 0, 0, 0, 0, 4, 8, 15, 25, 37, 48,
        52, 48, 43, 35, 20, 12, 5, 0, 0, 0, 0, 0
    ]

    axe_1 = axes[0]
    axe_1.plot(hours, grid_demand, color="#1F5A94", label="Grid demand")
    axe_1.plot(hours, solar_generation, color="#E74C3C", linestyle="--", label="Solar generation",)

    peak_demand = max(grid_demand)
    peak_hour = hours[grid_demand.index(peak_demand)]
    axe_1.annotate(
        f"Peak Demand: {peak_demand} kW",
        xy=(peak_hour, peak_demand),
        xytext=(peak_hour + 2, peak_demand + 5),
        arrowprops={"arrowstyle": "->", "color": "black"},
    )

    axe_1.set_title("Hourly Grid Demand VS Solar Generation (Simulated)", fontsize=12)
    axe_1.set_xlabel("Hours")
    axe_1.set_ylabel("Power (kW)")
    axe_1.set_xticks(range(0, 24, 2))
    axe_1.set_ylim(0, 125)
    axe_1.legend(loc="upper left")


    # panel 2: compare charging session costs by user type.
    axe_2 = axes[1]
    sns.boxplot(
        data=df,
        x="Net_Billable_MYR",
        y="User_Type",
        order=["Student", "Staff", "Visitor"],
        orient="h",
        color="#1F5A94",
        ax=axe_2,
    )
    axe_2.set_title("Charging Session Cost by User Type")
    axe_2.set_xlabel("Net Billable Amount (MYR)")
    axe_2.set_ylabel("User Type")


    # panel 3: plot battery temperature against energy delivered.
    axe_3 = axes[2]
    charger_colours = {"AC": "blue", "DC": "red"}
    for charger, colour in charger_colours.items():
        charger_data = df[df["Charger_Type"] == charger]

        sns.scatterplot(
            data=charger_data,
            x="Battery_Temp_C",
            y="Energy_kWh",
            color=colour,
            alpha=0.30,
            s=16,
            label=charger,
            ax=axe_3,
        )

        # add a trendline
        sns.regplot(
            data=charger_data,
            x="Battery_Temp_C",
            y="Energy_kWh",
            scatter=False,
            ci=None,
            color=colour,
            line_kws={"linewidth": 1.8},
            ax=axe_3,
        )

    axe_3.set_title("Battery Temperature VS Energy Delivered", fontsize=12)
    axe_3.set_xlabel("Battery Temperature (°C)")
    axe_3.set_ylabel("Energy Delivered (kWh)")
    axe_3.legend(title="Charger Type", loc="upper left")

    return fig


if __name__ == "__main__":
    try:
        df = pd.read_csv("cleaned_energy_sales_data.csv")
        figure = ev_plots_panels(df)
        figure.savefig("ev_panel_visualization.png", dpi=300, bbox_inches="tight")
        plt.show()
        plt.close(figure)
    except (OSError, KeyError, ValueError) as error:
        raise SystemExit(f"Could not create charts: {error}") from error
