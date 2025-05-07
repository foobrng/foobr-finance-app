import streamlit as st

def calculate_financials(starting_balance, bike_repairs, fuel, airtime, ayo_airtime,
                         chicken_rep_expense, end_of_day_balance, payout, orders):
    balance_after_repairs = starting_balance - bike_repairs
    total_expenses = fuel + airtime + ayo_airtime + chicken_rep_expense
    balance_after_expenses = balance_after_repairs - total_expenses
    food_purchased = end_of_day_balance - balance_after_expenses
    closing_balance = payout + end_of_day_balance
    revenue = closing_balance - balance_after_repairs

    return {
        "Balance After Repairs": balance_after_repairs,
        "Total Expenses": total_expenses,
        "Balance After Expenses": balance_after_expenses,
        "Food Purchased": food_purchased,
        "Closing Balance": closing_balance,
        "Revenue": revenue,
        "Orders": orders
    }

st.title("Foobr Daily Financial Summary")

st.sidebar.header("Enter Daily Figures")

starting_balance = st.sidebar.number_input("Starting Balance", value=478411)
bike_repairs = st.sidebar.number_input("Bike Repairs", value=22500)
fuel = st.sidebar.number_input("Fuel", value=10000)
airtime = st.sidebar.number_input("Airtime", value=1000)
ayo_airtime = st.sidebar.number_input("Ayo's Airtime", value=2100)
chicken_rep_expense = st.sidebar.number_input("Chicken Republic Bike Expense", value=3900)
end_of_day_balance = st.sidebar.number_input("Balance Remaining in Account", value=149472)
payout = st.sidebar.number_input("Payout from Paystack", value=353600)
orders = st.sidebar.number_input("Number of Orders", value=75)

if st.sidebar.button("Calculate"):
    results = calculate_financials(
        starting_balance, bike_repairs, fuel, airtime, ayo_airtime,
        chicken_rep_expense, end_of_day_balance, payout, orders
    )

    st.subheader("Daily Summary Results")
    for key, value in results.items():
        st.write(f"**{key}**: ₦{value:,.2f}" if isinstance(value, (int, float)) else f"**{key}**: {value}")
