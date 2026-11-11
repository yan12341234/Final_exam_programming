
"""identified high-risk charging session and calculate surcharge using simulated records"""

from functools import reduce
def alert_session(records):
    """return an iterator over session that meets both risk conditions"""
    #lambda return True only when both risk conditions exceeded
    #filter() check records on demand and avoids build a list of matches
    return filter(
        lambda session: (
            session["Overstay_Mins"] > 20
            and session["Battery_Temp_C"] > 40
        ),
        records,
    )

def apply_surcharge(alert_sessions):
    """return an iterator include surcharges details."""
    #lambda copies each session into new dictionary
    #map() create each result without build a result list
    # 15% surcharge: base fee * 0.15 ; adjusted fee = base fee * 1.15

    return map(
        lambda session: dict(
            session,
            Surcharge_MYR=session["Base_Fee_MYR"] * 0.15,
            Adjusted_Fee_MYR=session["Base_Fee_MYR"] * 1.15,
        ),
        alert_sessions,
    )

def surcharge_fee(processed_session):
    """calculate total surcharge for processed session"""
    #lambda add each surcharge to total
    #0.0 is initial value, give zero total when there is no alert
    #reduce() adds each surcharge to total without storing all results
    return reduce(
        lambda total, session: total + session["Surcharge_MYR"],
        processed_session,
        0.0,
    )

#illustrative dataset
def main():
    """demonstrate functional pipeline using sample sessions"""
    sessions = [
        {
            "Session_ID": "SESS-1101",
            "Overstay_Mins": 30,
            "Battery_Temp_C": 40.0,
            "Base_Fee_MYR": 25.0,
        },
        {
            "Session_ID": "SESS-1102",
            "Overstay_Mins": 15,
            "Battery_Temp_C": 38.0,
            "Base_Fee_MYR": 30.0,
        },
        {
            "Session_ID": "SESS-1103",
            "Overstay_Mins": 45,
            "Battery_Temp_C": 51.0,
            "Base_Fee_MYR": 43.0,
        },
    ]

    # compose pipeline without intermediate result lists.
    alerts = alert_session(sessions)
    processed = apply_surcharge(alerts)
    total_surcharge = surcharge_fee(processed)

    #format to two decimal places for total surcharges
    print(f"Total surcharge: MYR{total_surcharge:.2f}")

if __name__ == "__main__":
    main()