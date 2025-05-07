import streamlit as st

def calculate_financials(starting_balance, bike_repairs, fuel, airtime,
                         end_of_day_balance, payout, orders):
    """
    Calculate daily financial metrics for the food delivery business.
    
    Parameters:
    -----------
    starting_balance: float (X)
        Beginning account balance for the day (balance brought forward)
    bike_repairs: float
        Expenses for motorcycle repairs (deducted from starting balance)
    fuel: float 
        Daily fuel expenses
    airtime: float
        Daily communication expenses
    end_of_day_balance: float (U)
        Remaining balance in account at day end
    payout: float
        Payments received through Paystack
    orders: int
        Number of orders processed today
    
    Returns:
    --------
    dict: Dictionary containing calculated financial metrics
    """
    # Balance after removing bike repairs and other company expenses from starting balance
    balance_after_repairs = starting_balance - bike_repairs  # Y
    
    # Daily expenses (only fuel and airtime)
    total_expenses = fuel + airtime
    
    # Balance after daily expenses
    balance_after_expenses = balance_after_repairs - total_expenses  # Z
    
    # Food purchased calculation (Z - U)
    food_purchased = balance_after_expenses - end_of_day_balance  # G
    
    # Closing balance (U + Paystack payout)
    closing_balance = end_of_day_balance + payout  # O
    
    # Revenue calculation (O - Y)
    revenue = closing_balance - balance_after_repairs
    
    # Calculate average order value
    average_order_value = revenue / orders if orders > 0 else 0

    return {
        "Balance After Repairs (Y)": balance_after_repairs,
        "Total Daily Expenses (Fuel + Airtime)": total_expenses,
        "Balance After Expenses (Z)": balance_after_expenses,
        "Food Purchased (G)": food_purchased,
        "Closing Balance (O)": closing_balance,
        "Revenue": revenue,
        "Orders": orders,
        "Average Order Value": average_order_value
    }

# App title and description
st.title("Foobr Daily Financial Summary")
st.markdown("Track and analyze your daily delivery business finances")

# Add date selection
import datetime
report_date = st.sidebar.date_input("Report Date", datetime.date.today())

st.sidebar.header("Enter Daily Figures")

# Input fields with more descriptive help text
# Input fields with clear variable labels (X, Y, Z, U, G, O)
st.sidebar.markdown("### Step 1: Starting Values")
starting_balance = st.sidebar.number_input("Starting Balance (X)", 
                                         help="Account balance at the beginning of the day",
                                         value=478411)
bike_repairs = st.sidebar.number_input("Bike Repairs & Other Company Expenses", 
                                     help="All company expenses except fuel and airtime",
                                     value=22500)

st.sidebar.markdown("### Step 2: Daily Expenses")
fuel = st.sidebar.number_input("Fuel", 
                             help="Daily fuel expenses",
                             value=10000)
airtime = st.sidebar.number_input("Airtime", 
                                help="Daily communication expenses",
                                value=1000)

st.sidebar.markdown("### Step 3: End of Day Values")
end_of_day_balance = st.sidebar.number_input("Balance Remaining in Account (U)", 
                                           help="Account balance at the end of the day",
                                           value=149472)
payout = st.sidebar.number_input("Payout from Paystack", 
                               help="Total payments received through Paystack",
                               value=353600)
orders = st.sidebar.number_input("Number of Orders", 
                               help="Total number of orders fulfilled today",
                               min_value=0,
                               value=75)

if st.sidebar.button("Calculate"):
    results = calculate_financials(
        starting_balance, bike_repairs, fuel, airtime,
        end_of_day_balance, payout, orders
    )

    # Display results
    st.subheader(f"Daily Summary Results for {report_date.strftime('%B %d, %Y')}")
    
    # Create financial flow visualization
    st.markdown("### Financial Flow")
    flow_col1, flow_col2, flow_col3 = st.columns(3)
    
    with flow_col1:
        st.info(f"**Starting Balance (X)**\n₦{starting_balance:,.2f}")
        st.error(f"**- Bike Repairs & Other**\n₦{bike_repairs:,.2f}")
        st.success(f"**= Balance After Repairs (Y)**\n₦{results['Balance After Repairs (Y)']:,.2f}")
        
    with flow_col2:
        st.info(f"**Balance After Repairs (Y)**\n₦{results['Balance After Repairs (Y)']:,.2f}")
        st.error(f"**- Fuel + Airtime**\n₦{results['Total Daily Expenses (Fuel + Airtime)']:,.2f}")
        st.success(f"**= Balance After Expenses (Z)**\n₦{results['Balance After Expenses (Z)']:,.2f}")
        
    with flow_col3:
        st.info(f"**Balance After Expenses (Z)**\n₦{results['Balance After Expenses (Z)']:,.2f}")
        st.error(f"**- End of Day Balance (U)**\n₦{end_of_day_balance:,.2f}")
        st.success(f"**= Food Purchased (G)**\n₦{results['Food Purchased (G)']:,.2f}")
    
    st.markdown("---")
    st.markdown("### Final Results")
    final_col1, final_col2 = st.columns(2)
    
    with final_col1:
        st.info(f"**End of Day Balance (U)**\n₦{end_of_day_balance:,.2f}")
        st.success(f"**+ Paystack Payout**\n₦{payout:,.2f}")
        st.warning(f"**= Closing Balance (O)**\n₦{results['Closing Balance (O)']:,.2f}")
        
    with final_col2:
        st.info(f"**Closing Balance (O)**\n₦{results['Closing Balance (O)']:,.2f}")
        st.error(f"**- Balance After Repairs (Y)**\n₦{results['Balance After Repairs (Y)']:,.2f}")
        st.success(f"**= Revenue**\n₦{results['Revenue']:,.2f}")
    
    # Create two columns - one for detailed results, one for chart
    st.markdown("### Detailed Results")
    col1, col2 = st.columns([3, 2])
    
    with col1:
        for key, value in results.items():
            if key == "Orders":
                st.write(f"**{key}**: {value}")
            elif key == "Average Order Value":
                st.write(f"**{key}**: ₦{value:,.2f}")
            else:
                st.write(f"**{key}**: ₦{value:,.2f}")
    
    # Create simple visualization of expenses and revenue
    with col2:
        import pandas as pd
        import matplotlib.pyplot as plt
        
        # Expense breakdown
        expense_data = {
            'Category': ['Bike Repairs & Other', 'Fuel', 'Airtime', 'Food Purchased'],
            'Amount': [bike_repairs, fuel, airtime, results['Food Purchased (G)']]
        }
        expense_df = pd.DataFrame(expense_data)
        
        fig, ax = plt.subplots()
        ax.bar(expense_df['Category'], expense_df['Amount'])
        ax.set_title('Expense Breakdown')
        ax.set_ylabel('Amount (₦)')
        plt.xticks(rotation=45)
        plt.tight_layout()
        st.pyplot(fig)
        
    # Show key metrics
    st.subheader("Key Metrics")
    metrics_col1, metrics_col2, metrics_col3 = st.columns(3)
    with metrics_col1:
        st.metric("Revenue", f"₦{results['Revenue']:,.2f}")
    with metrics_col2:
        st.metric("Orders", results['Orders'])
    with metrics_col3:
        st.metric("Avg Order Value", f"₦{results['Average Order Value']:,.2f}")
