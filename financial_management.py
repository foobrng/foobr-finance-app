import streamlit as st
import pandas as pd
import datetime
import io

# Set page configuration
st.set_page_config(
    page_title="Foobr Financial Dashboard",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add basic CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2rem;
        font-weight: 700;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 1rem;
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

# Save data to CSV
def save_to_csv(data_dict, report_date):
    """Save financial data to CSV."""
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
    
    # Check if we have existing data
    if 'financial_data' not in st.session_state:
        st.session_state.financial_data = df
    else:
        # Check if entry for this date already exists
        existing_data = st.session_state.financial_data
        if formatted_date in existing_data['Date'].values:
            # Update existing entry
            existing_data.loc[existing_data['Date'] == formatted_date] = df.values
        else:
            # Append new entry
            st.session_state.financial_data = pd.concat([existing_data, df], ignore_index=True)
    
    # Return CSV data for download
    return st.session_state.financial_data.to_csv(index=False)

# Load data from CSV
def load_data_from_csv(uploaded_file):
    """Load financial data from uploaded CSV file."""
    df = pd.read_csv(uploaded_file)
    
    # Ensure Date column is datetime
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'])
    
    # Store in session state
    st.session_state.financial_data = df
    return df

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

# Visualize trends
def visualize_trends(data):
    """Create visualizations of financial trends."""
    if data.empty or len(data) < 2:  # Need at least 2 points for a trend
        return None
    
    # Ensure Date column is datetime
    if 'Date' in data.columns:
        data['Date'] = pd.to_datetime(data['Date'])
    else:
        return None
    
    # Sort by date
    data = data.sort_values('Date')
    
    # Create weekly and monthly aggregations
    data['Week'] = data['Date'].dt.strftime('%Y-%U')
    data['Month'] = data['Date'].dt.strftime('%Y-%m')
    
    weekly_data = data.groupby('Week').agg({
        'Revenue': 'sum',
        'Orders': 'sum'
    }).reset_index()
    
    monthly_data = data.groupby('Month').agg({
        'Revenue': 'sum',
        'Orders': 'sum'
    }).reset_index()
    
    return {
        'daily': data,
        'weekly': weekly_data,
        'monthly': monthly_data
    }

# Main application
def main():
    # Display app title
    st.markdown("<h1 class='main-header'>Foobr Financial Dashboard</h1>", unsafe_allow_html=True)
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    app_mode = st.sidebar.radio("", ["Daily Entry", "Historical Data"])
    
    # Initialize session state for financial data if not exists
    if 'financial_data' not in st.session_state:
        st.session_state.financial_data = pd.DataFrame()
    
    # Daily Entry Page
    if app_mode == "Daily Entry":
        # Add date selection
        report_date = st.sidebar.date_input("Report Date", datetime.date.today())
        
        # Input form in the sidebar
        st.sidebar.markdown("### Step 1: Starting Values")
        starting_balance = st.sidebar.number_input("Starting Balance", 
                                                help="Total amount of money from the day before",
                                                value=0.0)
        bike_repairs = st.sidebar.number_input("Bike Repairs & Company Expenses", 
                                            help="Any expenses aside from fuel and airtime",
                                            value=0.0)

        st.sidebar.markdown("### Step 2: Daily Expenses")
        fuel = st.sidebar.number_input("Fuel", 
                                    help="Daily fuel expenses for delivery vehicles",
                                    value=0.0)
        airtime = st.sidebar.number_input("Airtime", 
                                       help="Daily communication expenses",
                                       value=0.0)

        st.sidebar.markdown("### Step 3: End of Day Values")
        end_of_day_balance = st.sidebar.number_input("Balance Remaining", 
                                                  help="Balance remaining in all accounts after daily expenditures",
                                                  value=0.0)
        payout = st.sidebar.number_input("Payout from Paystack", 
                                      help="Total payments received through Paystack",
                                      value=0.0)
        orders = st.sidebar.number_input("Number of Orders", 
                                      help="Total number of orders fulfilled today",
                                      min_value=0,
                                      value=0)

        calculate_button = st.sidebar.button("Calculate", use_container_width=True)
        
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
                st.info(f"**Starting Balance**\n₦{starting_balance:,.2f}")
                st.error(f"**- Bike Repairs**\n₦{bike_repairs:,.2f}")
                st.success(f"**= Balance After Repairs**\n₦{results['Balance After Repairs']:,.2f}")
                
            with flow_col2:
                st.info(f"**Balance After Repairs**\n₦{results['Balance After Repairs']:,.2f}")
                st.error(f"**- Fuel + Airtime**\n₦{results['Total Daily Expenses']:,.2f}")
                st.success(f"**= Balance After Expenses**\n₦{results['Balance After Expenses']:,.2f}")
                
            with flow_col3:
                st.info(f"**Balance After Expenses**\n₦{results['Balance After Expenses']:,.2f}")
                st.error(f"**- End of Day Balance**\n₦{end_of_day_balance:,.2f}")
                st.success(f"**= Food Purchased**\n₦{results['Food Purchased']:,.2f}")
            
            st.markdown("---")
            st.subheader("Final Results")
            final_col1, final_col2 = st.columns(2)
            
            with final_col1:
                st.info(f"**End of Day Balance**\n₦{end_of_day_balance:,.2f}")
                st.success(f"**+ Paystack Payout**\n₦{payout:,.2f}")
                st.warning(f"**= Closing Balance**\n₦{results['Closing Balance']:,.2f}")
                
            with final_col2:
                st.info(f"**Closing Balance**\n₦{results['Closing Balance']:,.2f}")
                st.error(f"**- Balance After Repairs**\n₦{results['Balance After Repairs']:,.2f}")
                st.success(f"**= Revenue**\n₦{results['Revenue']:,.2f}")
            
            # Save data
            st.markdown("---")
            st.subheader("Save Data")
            
            csv_data = save_to_csv(save_data, report_date)
            st.download_button(
                label="Download Daily Report",
                data=csv_data,
                file_name=f"foobr_financial_data_{report_date.strftime('%Y-%m-%d')}.csv",
                mime="text/csv"
            )
    
    # Historical Data Page
    elif app_mode == "Historical Data":
        st.subheader("Historical Financial Data")
        
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
            # Period selection
            period = st.radio("Select Period", ["All Time", "This Week", "This Month"], horizontal=True)
            
            # Filter data based on period
            filtered_data = data.copy()
            if period == "This Week":
                today = pd.Timestamp.today()
                start_of_week = today - pd.Timedelta(days=today.dayofweek)
                filtered_data = filtered_data[filtered_data['Date'] >= start_of_week] 
                summary = generate_summary(filtered_data, 'week')
                period_name = "Weekly"
            elif period == "This Month":
                today = pd.Timestamp.today()
                start_of_month = today.replace(day=1)
                filtered_data = filtered_data[filtered_data['Date'] >= start_of_month]
                summary = generate_summary(filtered_data, 'month')
                period_name = "Monthly"
            else:
                summary = generate_summary(filtered_data)
                period_name = "All-Time"
            
            # Show summary statistics
            st.subheader(f"{period_name} Performance Summary")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Revenue", f"₦{summary['Total Revenue']:,.2f}")
            with col2:
                st.metric("Total Orders", f"{summary['Total Orders']}")
            with col3:
                st.metric("Avg Order Value", f"₦{summary['Average Order Value']:,.2f}")
            
            # Display data table
            st.markdown("---")
            st.subheader("Financial Records")
            
            # Prepare display columns and format data
            display_df = filtered_data.copy()
            if 'Date' in display_df.columns:
                display_df['Date'] = display_df['Date'].dt.strftime('%b %d, %Y')
            
            # Sort by date (newest first)
            display_df = display_df.sort_values('Date', ascending=False)
            
            # Show the data
            st.dataframe(display_df)
            
            # Export functionality
            st.markdown("---")
            st.subheader("Export Data")
            
            export_period = st.radio("Export Period", ["All Data", "Current Selection"], horizontal=True)
            export_data = data if export_period == "All Data" else filtered_data
            
            col1, col2 = st.columns(2)
            
            with col1:
                csv = export_data.to_csv(index=False)
                st.download_button(
                    label=f"Download {period_name} Report as CSV",
                    data=csv,
                    file_name=f"foobr_financial_data_{period.lower().replace(' ', '_')}.csv",
                    mime="text/csv"
                )
            
            with col2:
                # Create Excel file
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    export_data.to_excel(writer, sheet_name='Financial Data', index=False)
                excel_data = output.getvalue()
                st.download_button(
                    label=f"Download {period_name} Report as Excel",
                    data=excel_data,
                    file_name=f"foobr_financial_data_{period.lower().replace(' ', '_')}.xlsx", 
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

# Run the application
if __name__ == "__main__":
    main()
