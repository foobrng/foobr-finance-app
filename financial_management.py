import streamlit as st
import pandas as pd
import datetime
import io

# Set page configuration
st.set_page_config(
    page_title="Foobr Financial Dashboard",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Add minimal CSS for the black, grey, and white theme
st.markdown("""
<style>
    .main-header {
        font-size: 2rem;
        font-weight: 700;
        color: #000000;
        text-align: center;
        margin-bottom: 1rem;
    }
    .subheader {
        color: #333333;
        font-weight: 600;
    }
    .stButton>button {
        background-color: #333333;
        color: white;
    }
    div.block-container {
        padding-top: 2rem;
    }
    .metric-container {
        background-color: #f5f5f5;
        padding: 1rem;
        border-radius: 5px;
    }
    .tab-content {
        padding: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

def calculate_financials(starting_balance, bike_repairs, fuel, airtime,
                         end_of_day_balance, payout, orders):
    """Calculate daily financial metrics for the food delivery business."""
    # Balance after removing bike repairs from starting balance
    balance_after_repairs = starting_balance - bike_repairs
    
    # Daily expenses (fuel and airtime)
    total_expenses = fuel + airtime
    
    # Balance after daily expenses
    balance_after_expenses = balance_after_repairs - total_expenses
    
    # Food purchased calculation
    food_purchased = balance_after_expenses - end_of_day_balance
    
    # Closing balance
    closing_balance = end_of_day_balance + payout
    
    # Revenue calculation
    revenue = closing_balance - balance_after_repairs
    
    # Calculate average order value
    average_order_value = revenue / orders if orders > 0 else 0

    return {
        "Balance After Repairs": balance_after_repairs,
        "Total Daily Expenses": total_expenses,
        "Balance After Expenses": balance_after_expenses,
        "Food Purchased": food_purchased,
        "Closing Balance": closing_balance,
        "Revenue": revenue,
        "Orders": orders,
        "Average Order Value": average_order_value
    }

def save_to_csv(data_dict, report_date):
    """Save financial data to CSV and ensure the file is properly created for download.
    
    Args:
        data_dict (dict): Dictionary containing financial data
        report_date (datetime.date): Date of the financial report
        
    Returns:
        str: CSV data as string for download
    """
    # Format the date
    formatted_date = report_date.strftime('%Y-%m-%d')
    
    # Create a DataFrame with a single row
    df = pd.DataFrame([{
        'Date': formatted_date,
        'Starting Balance': data_dict['Starting Balance'],
        'Bike Repairs': data_dict['Bike Repairs'],
        'Fuel': data_dict['Fuel'],
        'Airtime': data_dict['Airtime'],
        'End of Day Balance': data_dict['End of Day Balance'],
        'Payout': data_dict['Payout'],
        'Orders': data_dict['Orders'],
        'Balance After Repairs': data_dict['Balance After Repairs'],
        'Total Expenses': data_dict['Total Daily Expenses'],
        'Balance After Expenses': data_dict['Balance After Expenses'],
        'Food Purchased': data_dict['Food Purchased'],
        'Closing Balance': data_dict['Closing Balance'],
        'Revenue': data_dict['Revenue'],
        'Average Order Value': data_dict['Average Order Value']
    }])
    
    # Initialize financial_data in session state if not exists
    if 'financial_data' not in st.session_state:
        st.session_state.financial_data = df
    else:
        # Check if entry for this date already exists
        existing_data = st.session_state.financial_data
        date_exists = formatted_date in existing_data['Date'].values if 'Date' in existing_data.columns else False
        
        if date_exists:
            # Update existing entry
            existing_data.loc[existing_data['Date'] == formatted_date] = df.values
            st.session_state.financial_data = existing_data
        else:
            # Append new entry
            st.session_state.financial_data = pd.concat([existing_data, df], ignore_index=True)
    
    # Make sure we save the updated data to CSV
    csv_data = st.session_state.financial_data.to_csv(index=False)
    
    return csv_data

# Generate summary statistics
def generate_summary(data, period=None):
    """Generate basic summary statistics."""
    if data.empty:
        return {}
    
    # Filter by period if specified
    if period == 'week':
        today = pd.Timestamp.today()
        start_of_week = today - pd.Timedelta(days=today.dayofweek)
        data = data[data['Date'] >= start_of_week]
    elif period == 'month':
        today = pd.Timestamp.today()
        start_of_month = today.replace(day=1)
        data = data[data['Date'] >= start_of_month]
    
    summary = {
        'Total Revenue': data['Revenue'].sum(),
        'Average Daily Revenue': data['Revenue'].mean(),
        'Total Orders': data['Orders'].sum(),
        'Average Daily Orders': data['Orders'].mean(),
        'Average Order Value': data['Revenue'].sum() / data['Orders'].sum() if data['Orders'].sum() > 0 else 0
    }
    
    return summary

def filter_data_by_period(data, period):
    """Filter DataFrame by selected time period.
    
    Args:
        data (pd.DataFrame): DataFrame containing financial data
        period (str): Time period to filter by ('week', 'month', 'all')
        
    Returns:
        pd.DataFrame: Filtered DataFrame
    """
    if data.empty or 'Date' not in data.columns:
        return data
        
    # Ensure Date column is datetime
    if not pd.api.types.is_datetime64_any_dtype(data['Date']):
        data['Date'] = pd.to_datetime(data['Date'])
    
    # Filter based on period
    if period == 'week':
        today = pd.Timestamp.today()
        start_of_week = today - pd.Timedelta(days=today.dayofweek)
        return data[data['Date'] >= start_of_week]
    elif period == 'month':
        today = pd.Timestamp.today()
        start_of_month = today.replace(day=1)
        return data[data['Date'] >= start_of_month]
    else:  # 'all'
        return data

def load_data_from_csv(file):
    """Load financial data from uploaded CSV file.
    
    Args:
        file: File object from st.file_uploader
        
    Returns:
        pd.DataFrame: Loaded data
    """
    try:
        data = pd.read_csv(file)
        # Convert Date column to datetime if it exists
        if 'Date' in data.columns:
            data['Date'] = pd.to_datetime(data['Date'])
        return data
    except Exception as e:
        st.error(f"Error loading CSV file: {e}")
        return pd.DataFrame()

# Main application
def main():
    # Display app title
    st.markdown("<h1 class='main-header'>Foobr Financial Dashboard</h1>", unsafe_allow_html=True)
    
    # Top navigation using tabs instead of sidebar
    tab1, tab2 = st.tabs(["Daily Entry", "Historical Data"])
    
    # Initialize session state for financial data if not exists
    if 'financial_data' not in st.session_state:
        st.session_state.financial_data = pd.DataFrame()
    
    # Daily Entry Page
    with tab1:
        st.markdown("<h3 class='subheader'>Daily Financial Entry</h3>", unsafe_allow_html=True)
        
        # Add date selection
        report_date = st.date_input("Report Date", datetime.date.today())
        
        # Create two columns for input form
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Starting Values")
            starting_balance = st.number_input("Starting Balance", 
                                              help="Total amount of money from the day before",
                                              value=0.0)
            bike_repairs = st.number_input("Bike Repairs & Company Expenses", 
                                          help="Any expenses aside from fuel and airtime",
                                          value=0.0)

            st.markdown("### Daily Expenses")
            fuel = st.number_input("Fuel", 
                                  help="Daily fuel expenses for delivery vehicles",
                                  value=0.0)
            airtime = st.number_input("Airtime", 
                                     help="Daily communication expenses",
                                     value=0.0)

        with col2:
            st.markdown("### End of Day Values")
            end_of_day_balance = st.number_input("Balance Remaining", 
                                                help="Balance remaining in all accounts after daily expenditures",
                                                value=0.0)
            payout = st.number_input("Payout from Paystack", 
                                    help="Total payments received through Paystack",
                                    value=0.0)
            orders = st.number_input("Number of Orders", 
                                    help="Total number of orders fulfilled today",
                                    min_value=0,
                                    value=0)

        # Calculate and save buttons
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            calculate_button = st.button("Calculate", use_container_width=True)
        
        # Display the calculations
        if calculate_button:
            results = calculate_financials(
                starting_balance, bike_repairs, fuel, airtime,
                end_of_day_balance, payout, orders
            )

            # Store input data and results for saving
            save_data = {
                'Starting Balance': starting_balance,
                'Bike Repairs': bike_repairs,
                'Fuel': fuel,
                'Airtime': airtime,
                'End of Day Balance': end_of_day_balance,
                'Payout': payout,
                'Orders': orders
            }
            save_data.update(results)
            
            # Display results 
            st.subheader(f"Daily Summary for {report_date.strftime('%B %d, %Y')}")
            
            # Show key metrics at the top
            metric_col1, metric_col2, metric_col3 = st.columns(3)
            with metric_col1:
                st.metric("Revenue", f"₦{results['Revenue']:,.2f}")
            with metric_col2:
                st.metric("Orders", results['Orders'])
            with metric_col3:
                st.metric("Avg Order Value", f"₦{results['Average Order Value']:,.2f}")
            
            st.markdown("---")
            
            # Create financial flow visualization
            st.subheader("Financial Flow")
            flow_col1, flow_col2, flow_col3 = st.columns(3)
            
            with flow_col1:
                st.markdown(f"**Starting Balance**\n₦{starting_balance:,.2f}")
                st.markdown(f"**- Bike Repairs**\n₦{bike_repairs:,.2f}")
                st.markdown(f"**= Balance After Repairs**\n₦{results['Balance After Repairs']:,.2f}")
                
            with flow_col2:
                st.markdown(f"**Balance After Repairs**\n₦{results['Balance After Repairs']:,.2f}")
                st.markdown(f"**- Fuel + Airtime**\n₦{results['Total Daily Expenses']:,.2f}")
                st.markdown(f"**= Balance After Expenses**\n₦{results['Balance After Expenses']:,.2f}")
                
            with flow_col3:
                st.markdown(f"**Balance After Expenses**\n₦{results['Balance After Expenses']:,.2f}")
                st.markdown(f"**- End of Day Balance**\n₦{end_of_day_balance:,.2f}")
                st.markdown(f"**= Food Purchased**\n₦{results['Food Purchased']:,.2f}")
            
            st.markdown("---")
            st.subheader("Final Results")
            final_col1, final_col2 = st.columns(2)
            
            with final_col1:
                st.markdown(f"**End of Day Balance**\n₦{end_of_day_balance:,.2f}")
                st.markdown(f"**+ Paystack Payout**\n₦{payout:,.2f}")
                st.markdown(f"**= Closing Balance**\n₦{results['Closing Balance']:,.2f}")
                
            with final_col2:
                st.markdown(f"**Closing Balance**\n₦{results['Closing Balance']:,.2f}")
                st.markdown(f"**- Balance After Repairs**\n₦{results['Balance After Repairs']:,.2f}")
                st.markdown(f"**= Revenue**\n₦{results['Revenue']:,.2f}")
            
            # Save button after calculations
            with col_btn2:
                save_button = st.button("Save Record", use_container_width=True)
                
                if save_button:
                    csv_data = save_to_csv(save_data, report_date)
                    st.success(f"Data for {report_date.strftime('%B %d, %Y')} saved successfully!")
                    st.download_button(
                        label="Download Daily Report",
                        data=csv_data,
                        file_name=f"foobr_financial_data_{report_date.strftime('%Y-%m-%d')}.csv",
                        mime="text/csv"
                    )
    
    # Historical Data Page
    with tab2:
        st.markdown("<h3 class='subheader'>Historical Financial Data</h3>", unsafe_allow_html=True)
        
        # File uploader for CSV
        uploaded_file = st.file_uploader("Upload financial data CSV", type="csv")
        
        if uploaded_file is not None:
            data = load_data_from_csv(uploaded_file)
            st.success(f"Loaded {len(data)} records from CSV file.")
        else:
            data = st.session_state.financial_data
        
        if data.empty:
            st.info("No historical data available. Please upload a CSV file or add entries in the Daily Entry tab.")
        else:
            # Simple period selector
            col1, col2 = st.columns([1, 3])
            with col1:
                period = st.radio("Select Period", ["All Time", "This Week", "This Month"])
            
            # Map period selection to filter code
            period_filter = 'all'
            if period == "This Week":
                period_filter = 'week'
                period_name = "Weekly"
            elif period == "This Month":
                period_filter = 'month'
                period_name = "Monthly"
            else:
                period_name = "All-Time"
            
            # Filter data based on period
            filtered_data = filter_data_by_period(data, period_filter)
            
            # Generate and display summary statistics
            summary = generate_summary(filtered_data, period_filter)
            
            with col2:
                st.markdown(f"### {period_name} Performance Summary")
                metric_col1, metric_col2, metric_col3 = st.columns(3)
                
                with metric_col1:
                    st.metric("Total Revenue", f"₦{summary.get('Total Revenue', 0):,.2f}")
                with metric_col2:
                    st.metric("Total Orders", f"{summary.get('Total Orders', 0)}")
                with metric_col3:
                    st.metric("Avg Order Value", f"₦{summary.get('Average Order Value', 0):,.2f}")
            
            # Display data table
            st.markdown("---")
            st.subheader("Financial Records")
            
            # Prepare display columns and format data
            display_df = filtered_data.copy()
            if not display_df.empty and 'Date' in display_df.columns:
                display_df['Date'] = display_df['Date'].dt.strftime('%b %d, %Y')
            
            # Sort by date (newest first)
            if not display_df.empty and 'Date' in display_df.columns:
                display_df = display_df.sort_values('Date', ascending=False)
            
            # Show the data
            st.dataframe(display_df)
            
            # Export functionality
            st.markdown("---")
            col_export1, col_export2 = st.columns(2)
            
            with col_export1:
                st.subheader("Export Data")
                if not filtered_data.empty:
                    csv = filtered_data.to_csv(index=False)
                    st.download_button(
                        label=f"Download {period_name} Report (CSV)",
                        data=csv,
                        file_name=f"foobr_financial_data_{period.lower().replace(' ', '_')}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
            
# Run the application
if __name__ == "__main__":
    main()
