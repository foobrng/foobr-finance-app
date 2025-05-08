import streamlit as st
import datetime
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from google.oauth2 import service_account
import os

# Set page configuration for a better UI experience
st.set_page_config(
    page_title="Foobr Financial Dashboard",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add custom CSS to improve the UI
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: 500;
        margin-top: 1.5rem;
    }
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .sidebar .sidebar-content {
        background-color: #f8f9fa;
    }
    .stDateInput > div > div > input {
        width: 100%;
    }
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 1.5rem;
        box-shadow: 0 0.15rem 1.75rem 0 rgba(58, 59, 69, 0.15);
    }
    .info-text {
        color: #6c757d;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

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

# Function to connect to Google Sheets
def connect_to_gsheets():
    """Connect to Google Sheets using service account credentials."""
    try:
        # Check if credentials have been uploaded
        if "gsheets_creds" not in st.session_state:
            st.session_state.gsheets_credentials_error = True
            return None
            
        credentials = service_account.Credentials.from_service_account_info(
            st.session_state.gsheets_creds,
            scopes=['https://spreadsheets.google.com/feeds', 
                   'https://www.googleapis.com/auth/drive']
        )
        
        gc = gspread.authorize(credentials)
        return gc
    except Exception as e:
        st.error(f"Error connecting to Google Sheets: {e}")
        return None

# Function to load data from Google Sheets
def load_data_from_gsheets(gc, spreadsheet_key, worksheet_name="Financial Data"):
    """Load financial data from Google Sheets."""
    try:
        # Open the spreadsheet and worksheet
        spreadsheet = gc.open_by_key(spreadsheet_key)
        worksheet = spreadsheet.worksheet(worksheet_name)
        
        # Get all data from the worksheet
        data = worksheet.get_all_records()
        
        if data:
            df = pd.DataFrame(data)
            return df
        else:
            # If no data, return empty DataFrame with expected columns
            return pd.DataFrame(columns=[
                'Date', 'Starting Balance', 'Bike Repairs', 'Fuel', 'Airtime',
                'End of Day Balance', 'Payout', 'Orders', 'Revenue', 'Average Order Value'
            ])
    except Exception as e:
        st.error(f"Error loading data from Google Sheets: {e}")
        return pd.DataFrame()

# Function to save data to Google Sheets
def save_data_to_gsheets(gc, spreadsheet_key, data_dict, report_date, worksheet_name="Financial Data"):
    """Save financial data to Google Sheets."""
    try:
        # Open the spreadsheet
        spreadsheet = gc.open_by_key(spreadsheet_key)
        
        # Check if worksheet exists, if not create it
        try:
            worksheet = spreadsheet.worksheet(worksheet_name)
        except:
            worksheet = spreadsheet.add_worksheet(title=worksheet_name, rows=1000, cols=20)
            # Add headers if new worksheet
            headers = [
                'Date', 'Starting Balance', 'Bike Repairs', 'Fuel', 'Airtime',
                'End of Day Balance', 'Payout', 'Orders', 'Balance After Repairs', 
                'Total Expenses', 'Balance After Expenses', 'Food Purchased',
                'Closing Balance', 'Revenue', 'Average Order Value'
            ]
            worksheet.append_row(headers)
        
        # Format the date
        formatted_date = report_date.strftime('%Y-%m-%d')
        
        # Prepare row data
        row_data = [
            formatted_date,
            data_dict['Starting Balance'],
            data_dict['Bike Repairs'],
            data_dict['Fuel'],
            data_dict['Airtime'],
            data_dict['End of Day Balance'],
            data_dict['Payout'],
            data_dict['Orders'],
            data_dict['Balance After Repairs (Y)'],
            data_dict['Total Daily Expenses (Fuel + Airtime)'],
            data_dict['Balance After Expenses (Z)'],
            data_dict['Food Purchased (G)'],
            data_dict['Closing Balance (O)'],
            data_dict['Revenue'],
            data_dict['Average Order Value']
        ]
        
        # Check if the entry for this date already exists
        all_data = worksheet.get_all_records()
        df = pd.DataFrame(all_data)
        
        if 'Date' in df.columns and formatted_date in df['Date'].values:
            # Update existing row
            row_index = df[df['Date'] == formatted_date].index[0] + 2  # +2 because of header and 0-indexing
            cell_list = worksheet.range(f'A{row_index}:O{row_index}')
            for i, cell in enumerate(cell_list):
                cell.value = row_data[i]
            worksheet.update_cells(cell_list)
            return "Data updated successfully!"
        else:
            # Append new row
            worksheet.append_row(row_data)
            return "Data saved successfully!"
    except Exception as e:
        return f"Error saving data: {e}"

# Function to generate summary statistics
def generate_summary(data, period='daily'):
    """Generate summary statistics based on the selected period."""
    if data.empty:
        return pd.DataFrame()
    
    # Ensure Date column is datetime
    if 'Date' in data.columns:
        data['Date'] = pd.to_datetime(data['Date'])
    else:
        return pd.DataFrame()
    
    if period == 'daily':
        # Daily data is already in the right format
        return data
    elif period == 'weekly':
        data['Week'] = data['Date'].dt.strftime('%Y-W%U')
        grouped = data.groupby('Week').agg({
            'Revenue': 'sum',
            'Orders': 'sum',
            'Starting Balance': 'first',
            'End of Day Balance': 'last',
            'Date': ['min', 'max']  # Get first and last dates of the week
        })
        # Flatten multi-index columns
        grouped.columns = ['_'.join(col).strip() for col in grouped.columns.values]
        grouped['Date_Range'] = grouped.apply(lambda x: f"{x['Date_min'].strftime('%b %d')} - {x['Date_max'].strftime('%b %d, %Y')}", axis=1)
        grouped['Average Order Value'] = grouped['Revenue_sum'] / grouped['Orders_sum']
        return grouped.reset_index()
    elif period == 'monthly':
        data['Month'] = data['Date'].dt.strftime('%Y-%m')
        grouped = data.groupby('Month').agg({
            'Revenue': 'sum',
            'Orders': 'sum',
            'Starting Balance': 'first',
            'End of Day Balance': 'last',
            'Date': ['min', 'max']  # Get first and last dates of the month
        })
        # Flatten multi-index columns
        grouped.columns = ['_'.join(col).strip() for col in grouped.columns.values]
        grouped['Date_Range'] = grouped.apply(lambda x: f"{x['Date_min'].strftime('%b %d')} - {x['Date_max'].strftime('%b %d, %Y')}", axis=1)
        grouped['Average Order Value'] = grouped['Revenue_sum'] / grouped['Orders_sum']
        return grouped.reset_index()
    
    return pd.DataFrame()

# Function to display the latest historical data
def display_historical_data(data, period='daily', top_n=10):
    """Display the historical data in a table view."""
    if data.empty:
        st.warning("No historical data available.")
        return
    
    # Generate summary based on selected period
    summary_data = generate_summary(data, period)
    
    if summary_data.empty:
        st.warning(f"No {period} summary data available.")
        return
    
    # Display the latest entries
    st.markdown("### Recent Financial Records")
    
    if period == 'daily':
        # For daily view, show the most recent records
        display_df = summary_data.sort_values('Date', ascending=False).head(top_n)
        # Format columns for display
        display_df['Date'] = display_df['Date'].dt.strftime('%b %d, %Y')
        display_columns = ['Date', 'Orders', 'Revenue', 'Average Order Value']
        
        # Format numeric columns
        for col in display_df.columns:
            if col in ['Revenue', 'Average Order Value']:
                display_df[col] = display_df[col].apply(lambda x: f"₦{x:,.2f}")
        
        st.dataframe(display_df[display_columns], use_container_width=True)
    else:
        # For weekly/monthly view
        if period == 'weekly':
            display_df = summary_data.sort_values('Week', ascending=False).head(top_n)
            id_col = 'Week'
        else:
            display_df = summary_data.sort_values('Month', ascending=False).head(top_n)
            id_col = 'Month'
        
        # Format columns for display
        display_columns = [id_col, 'Date_Range', 'Orders_sum', 'Revenue_sum', 'Average Order Value']
        rename_map = {
            'Orders_sum': 'Total Orders',
            'Revenue_sum': 'Total Revenue',
            'Average Order Value': 'Avg Order Value',
            'Date_Range': 'Date Range'
        }
        
        # Format numeric columns
        for col in display_df.columns:
            if 'Revenue' in col or 'Average' in col:
                display_df[col] = display_df[col].apply(lambda x: f"₦{x:,.2f}")
        
        display_df = display_df[display_columns].rename(columns=rename_map)
        st.dataframe(display_df, use_container_width=True)

# Function to display metrics for a specific period
def display_period_metrics(data, period='daily'):
    """Display metrics for the selected period."""
    if data.empty:
        return
    
    summary_data = generate_summary(data, period)
    
    if summary_data.empty:
        return
    
    if period == 'daily':
        # For daily data, calculate the averages
        avg_revenue = data['Revenue'].mean()
        avg_orders = data['Orders'].mean()
        avg_order_value = data['Average Order Value'].mean()
        
        # Find highest revenue day
        highest_revenue_idx = data['Revenue'].idxmax()
        highest_revenue_day = data.loc[highest_revenue_idx]
        
        # Find lowest revenue day
        lowest_revenue_idx = data['Revenue'].idxmin()
        lowest_revenue_day = data.loc[lowest_revenue_idx]
        
        # Display metrics
        st.markdown("### Performance Metrics")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"**Average Daily Revenue**  \n₦{avg_revenue:,.2f}")
            st.markdown(f"**Average Daily Orders**  \n{avg_orders:.1f}")
            st.markdown(f"**Average Order Value**  \n₦{avg_order_value:,.2f}")
        
        with col2:
            st.markdown("**Highest Revenue Day**")
            st.markdown(f"Date: {highest_revenue_day['Date'].strftime('%b %d, %Y')}")
            st.markdown(f"Revenue: ₦{highest_revenue_day['Revenue']:,.2f}")
            st.markdown(f"Orders: {highest_revenue_day['Orders']}")
        
        with col3:
            st.markdown("**Lowest Revenue Day**")
            st.markdown(f"Date: {lowest_revenue_day['Date'].strftime('%b %d, %Y')}")
            st.markdown(f"Revenue: ₦{lowest_revenue_day['Revenue']:,.2f}")
            st.markdown(f"Orders: {lowest_revenue_day['Orders']}")
    else:
        # For weekly/monthly summaries
        if period == 'weekly':
            agg_data = summary_data.sort_values('Week')
            id_col = 'Week'
        else:
            agg_data = summary_data.sort_values('Month')
            id_col = 'Month'
        
        # Calculate totals and averages
        total_revenue = agg_data['Revenue_sum'].sum()
        total_orders = agg_data['Orders_sum'].sum()
        avg_revenue_per_period = agg_data['Revenue_sum'].mean()
        avg_orders_per_period = agg_data['Orders_sum'].mean()
        
        # Find highest revenue period
        highest_revenue_idx = agg_data['Revenue_sum'].idxmax()
        highest_revenue_period = agg_data.iloc[highest_revenue_idx]
        
        # Display metrics
        st.markdown(f"### {period.capitalize()} Performance Summary")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"**Total Revenue**  \n₦{total_revenue:,.2f}")
            st.markdown(f"**Total Orders**  \n{total_orders}")
        
        with col2:
            st.markdown(f"**Average {period.capitalize()} Revenue**  \n₦{avg_revenue_per_period:,.2f}")
            st.markdown(f"**Average {period.capitalize()} Orders**  \n{avg_orders_per_period:.1f}")
        
        st.markdown("---")
        st.markdown(f"**Highest Revenue {period.capitalize()}**")
        if period == 'weekly':
            st.markdown(f"Week: {highest_revenue_period['Date_Range']}")
        else:
            st.markdown(f"Month: {highest_revenue_period['Date_Range']}")
        st.markdown(f"Revenue: ₦{highest_revenue_period['Revenue_sum']:,.2f}")
        st.markdown(f"Orders: {highest_revenue_period['Orders_sum']}")

# Function to visualize trends
def visualize_trends(data, period='daily'):
    """Create visualizations of financial trends."""
    if data.empty:
        return
    
    # Ensure Date column is datetime
    if 'Date' in data.columns:
        data['Date'] = pd.to_datetime(data['Date'])
    else:
        return
    
    # Sort by date
    data = data.sort_values('Date')
    
    if period == 'daily':
        # For daily visualization
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
        
        # Revenue trend
        ax1.plot(data['Date'], data['Revenue'], 'b-', marker='o')
        ax1.set_title('Daily Revenue Trend')
        ax1.set_ylabel('Revenue (₦)')
        ax1.tick_params(axis='x', rotation=45)
        ax1.grid(True, linestyle='--', alpha=0.7)
        
        # Orders trend
        ax2.plot(data['Date'], data['Orders'], 'g-', marker='s')
        ax2.set_title('Daily Orders Trend')
        ax2.set_ylabel('Number of Orders')
        ax2.tick_params(axis='x', rotation=45)
        ax2.grid(True, linestyle='--', alpha=0.7)
        
        plt.tight_layout()
        st.pyplot(fig)
    else:
        # For weekly/monthly visualization
        summary_data = generate_summary(data, period)
        
        if summary_data.empty:
            return
        
        if period == 'weekly':
            x_axis = summary_data['Week']
            title_period = 'Weekly'
        else:
            x_axis = summary_data['Month']
            title_period = 'Monthly'
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
        
        # Revenue trend
        ax1.bar(range(len(x_axis)), summary_data['Revenue_sum'], color='skyblue')
        ax1.set_title(f'{title_period} Revenue Trend')
        ax1.set_ylabel('Total Revenue (₦)')
        ax1.set_xticks(range(len(x_axis)))
        ax1.set_xticklabels(x_axis, rotation=45)
        ax1.grid(True, linestyle='--', alpha=0.7, axis='y')
        
        # Orders trend
        ax2.bar(range(len(x_axis)), summary_data['Orders_sum'], color='lightgreen')
        ax2.set_title(f'{title_period} Orders Trend')
        ax2.set_ylabel('Total Orders')
        ax2.set_xticks(range(len(x_axis)))
        ax2.set_xticklabels(x_axis, rotation=45)
        ax2.grid(True, linestyle='--', alpha=0.7, axis='y')
        
        plt.tight_layout()
        st.pyplot(fig)

# Import for Excel export
import io

# Main application
def main():
    # Display app title with improved styling
    st.markdown("<h1 class='main-header'>Foobr Financial Dashboard</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; margin-bottom: 30px;'>Track, analyze, and manage your daily delivery business finances</p>", unsafe_allow_html=True)
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    app_mode = st.sidebar.radio("", ["Daily Entry", "Historical Data", "Google Sheets Setup"])
    
    # Google Sheets Setup Page
    if app_mode == "Google Sheets Setup":
        st.markdown("<h2 class='sub-header'>Google Sheets Integration Setup</h2>", unsafe_allow_html=True)
        
        st.markdown("""
        ### Instructions
        
        1. Create a Google Cloud project and enable the Google Sheets API
        2. Create a service account and download the JSON credentials file
        3. Upload the credentials file below
        4. Create a Google Sheet and share it with the service account email
        5. Enter the Google Sheet ID below (from the URL)
        """)
        
        # Upload credentials file
        uploaded_file = st.file_uploader("Upload Google Service Account Credentials (JSON)", type="json")
        
        if uploaded_file is not None:
            import json
            creds_dict = json.load(uploaded_file)
            st.session_state.gsheets_creds = creds_dict
            st.success("Credentials uploaded successfully!")
            
            # Display the service account email for sharing
            if "client_email" in creds_dict:
                st.info(f"Share your Google Sheet with this email: **{creds_dict['client_email']}**")
        
        # Google Sheet ID input
        sheet_id = st.text_input("Google Sheet ID", 
                                 help="The ID is the part of the Google Sheet URL between /d/ and /edit")
        
        if sheet_id:
            st.session_state.sheet_id = sheet_id
            st.success("Sheet ID saved!")
        
        # Test connection button
        if st.button("Test Connection"):
            if "gsheets_creds" not in st.session_state:
                st.error("Please upload credentials file first")
            elif "sheet_id" not in st.session_state:
                st.error("Please enter Sheet ID first")
            else:
                gc = connect_to_gsheets()
                if gc:
                    try:
                        sheet = gc.open_by_key(st.session_state.sheet_id)
                        st.success(f"Successfully connected to sheet: {sheet.title}")
                    except Exception as e:
                        st.error(f"Error connecting to sheet: {e}")
                else:
                    st.error("Failed to authorize Google Sheets API")
    
    # Daily Entry Page
    elif app_mode == "Daily Entry":
        # Add date selection
        report_date = st.sidebar.date_input("Report Date", datetime.date.today())
        
        # Improved input UI in the sidebar
        st.sidebar.markdown("### Step 1: Starting Values")
        starting_balance = st.sidebar.number_input("Starting Balance (X)", 
                                                value=478411,
                                                help="Account balance at the beginning of the day")
        bike_repairs = st.sidebar.number_input("Bike Repairs & Other Company Expenses", 
                                            value=22500,
                                            help="All company expenses except fuel and airtime")

        st.sidebar.markdown("### Step 2: Daily Expenses")
        fuel = st.sidebar.number_input("Fuel", 
                                    value=10000,
                                    help="Daily fuel expenses")
        airtime = st.sidebar.number_input("Airtime", 
                                        value=1000,
                                        help="Daily communication expenses")

        st.sidebar.markdown("### Step 3: End of Day Values")
        end_of_day_balance = st.sidebar.number_input("Balance Remaining in Account (U)", 
                                                  value=149472,
                                                  help="Account balance at the end of the day")
        payout = st.sidebar.number_input("Payout from Paystack", 
                                      value=353600,
                                      help="Total payments received through Paystack")
        orders = st.sidebar.number_input("Number of Orders", 
                                      min_value=0,
                                      value=75,
                                      help="Total number of orders fulfilled today")

        calculate_button = st.sidebar.button("Calculate", use_container_width=True)
        
        # Display the calculations
        if calculate_button:
            results = calculate_financials(
                starting_balance, bike_repairs, fuel, airtime,
                end_of_day_balance, payout, orders
            )

            # Store input data and results in session state for saving
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
            st.session_state.current_results = save_data
            
            # Display results with improved UI
            st.markdown(f"<h2 class='sub-header'>Daily Summary for {report_date.strftime('%B %d, %Y')}</h2>", unsafe_allow_html=True)
            
            # Show key metrics at the top
            metric_col1, metric_col2, metric_col3 = st.columns(3)
            with metric_col1:
                st.metric("Revenue", f"₦{results['Revenue']:,.2f}")
            with metric_col2:
                st.metric("Orders", results['Orders'])
            with metric_col3:
                st.metric("Avg Order Value", f"₦{results['Average Order Value']:,.2f}")
            
            st.markdown("---")
            
            # Create financial flow visualization with better styling
            st.markdown("<h3 class='sub-header'>Financial Flow</h3>", unsafe_allow_html=True)
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
            st.markdown("<h3 class='sub-header'>Final Results</h3>", unsafe_allow_html=True)
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
            st.markdown("<h3 class='sub-header'>Expense Breakdown</h3>", unsafe_allow_html=True)
            expense_col1, expense_col2 = st.columns([3, 2])
            
            with expense_col1:
                # Create a DataFrame for better display of detailed results
                details_df = pd.DataFrame({
                    'Metric': list(results.keys()),
                    'Value': list(results.values())
                })
                
                # Format the values
                details_df['Formatted Value'] = details_df['Value'].apply(
                    lambda x: f"₦{x:,.2f}" if isinstance(x, (int, float)) and 'Orders' not in details_df.iloc[details_df['Value'] == x]['Metric'].values else x
                )
                
                st.dataframe(details_df[['Metric', 'Formatted Value']], hide_index=True, use_container_width=True)
            
            # Create simple visualization of expenses and revenue
            with expense_col2:
                # Expense breakdown
                expense_data = {
                    'Category': ['Bike Repairs', 'Fuel', 'Airtime', 'Food Purchased'],
                    'Amount': [bike_repairs, fuel, airtime, results['Food Purchased (G)']]
                }
                expense_df = pd.DataFrame(expense_data)
                
                fig, ax = plt.subplots()
                bars = ax.bar(expense_df['Category'], expense_df['Amount'], color=['#ff9999', '#66b3ff', '#99ff99', '#ffcc99'])
                ax.set_title('Expense Breakdown')
                ax.set_ylabel('Amount (₦)')
                plt.xticks(rotation=45)
                
                # Add value labels on top of bars
                for bar in bars:
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height + 5,
                            f'₦{height:,.0f}',
                            ha='center', va='bottom', rotation=0, size=8)
                
                plt.tight_layout()
                st.pyplot(fig)
            
            # Save to Google Sheets section
            st.markdown("---")
            st.markdown("<h3 class='sub-header'>Save to Google Sheets</h3>", unsafe_allow_html=True)
            
            if "gsheets_creds" in st.session_state and "sheet_id" in st.session_state:
                if st.button("Save to Google Sheets"):
                    gc = connect_to_gsheets()
                    if gc:
                        result = save_data_to_gsheets(gc, st.session_state.sheet_id, save_data, report_date)
                        st.success(result)
            else:
                st.warning("Please set up Google Sheets integration in the 'Google Sheets Setup' tab before saving data.")
    
    # Historical Data Page
    elif app_mode == "Historical Data":
        st.markdown("<h2 class='sub-header'>Historical Financial Data</h2>", unsafe_allow_html=True)
        
        # Check if Google Sheets is set up
        if "gsheets_creds" not in st.session_state or "sheet_id" not in st.session_state:
            st.warning("Please set up Google Sheets integration in the 'Google Sheets Setup' tab to view historical data.")
            return
        
        # Connect to Google Sheets and load data
        gc = connect_to_gsheets()
        if not gc:
            st.error("Failed to connect to Google Sheets. Please check your credentials in the 'Google Sheets Setup' tab.")
            return
        
        # Load data from Google Sheets
        data = load_data_from_gsheets(gc, st.session_state.sheet_id)
        
        if data.empty:
            st.warning("No data found in the Google Sheet. Please add some entries first.")
            return
        
        # Convert Date column to datetime
        if 'Date' in data.columns:
            data['Date'] = pd.to_datetime(data['Date'])
        
        # Filters in sidebar
        st.sidebar.markdown("### Data Filters")
        
        # Time period selection
        period = st.sidebar.radio("Select Time Period", ["Daily", "Weekly", "Monthly"], index=0)
        period = period.lower()  # Convert to lowercase for function calls
        
        # Performance metrics selection
        metrics_view = st.sidebar.radio("Performance View", ["All Data", "Top Performers", "Low Performers"])
        
        # Date range filter
        min_date = data['Date'].min().date()
        max_date = data['Date'].max().date()
        
        date_range = st.sidebar.date_input(
            "Select Date Range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )
        
        # Handle both single date and date range selections
        if isinstance(date_range, tuple) and len(date_range) == 2:
            start_date, end_date = date_range
        else:
            start_date = end_date = date_range
        
        # Filter data by date range
        filtered_data = data[(data['Date'].dt.date >= start_date) & 
                            (data['Date'].dt.date <= end_date)]
                            
        # Apply performance filter
        if metrics_view == "Top Performers" and not filtered_data.empty:
            if period == "daily":
                # Get top 25% revenue days
                threshold = filtered_data['Revenue'].quantile(0.75)
                filtered_data = filtered_data[filtered_data['Revenue'] >= threshold]
                st.info(f"Showing top performers with revenue ≥ ₦{threshold:,.2f}")
            else:
                # For weekly/monthly, we'll filter after aggregation
                st.info("Showing top 25% performing periods by revenue")
        elif metrics_view == "Low Performers" and not filtered_data.empty:
            if period == "daily":
                # Get bottom 25% revenue days
                threshold = filtered_data['Revenue'].quantile(0.25)
                filtered_data = filtered_data[filtered_data['Revenue'] <= threshold]
                st.info(f"Showing low performers with revenue ≤ ₦{threshold:,.2f}")
            else:
                # For weekly/monthly, we'll filter after aggregation
                st.info("Showing bottom 25% performing periods by revenue")
        
        # Display metrics
        display_period_metrics(filtered_data, period)
        
        # Display historical data
        st.markdown("---")
        display_historical_data(filtered_data, period)
        
        # Visualize trends
        st.markdown("---")
        st.markdown("<h3 class='sub-header'>Financial Trends</h3>", unsafe_allow_html=True)
        visualize_trends(filtered_data, period)
        
        # Add export functionality
        st.markdown("---")
        st.markdown("<h3 class='sub-header'>Export Data</h3>", unsafe_allow_html=True)
        
        export_format = st.radio("Export Format", ["CSV", "Excel"], horizontal=True)
        
        if st.button("Export Filtered Data"):
            if export_format == "CSV":
                csv = filtered_data.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"foobr_financial_data_{period}_{start_date}_to_{end_date}.csv",
                    mime="text/csv"
                )
            else:
                # For Excel export
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    filtered_data.to_excel(writer, sheet_name=f'{period.capitalize()} Data', index=False)
                excel_data = output.getvalue()
                st.download_button(
                    label="Download Excel",
                    data=excel_data,
                    file_name=f"foobr_financial_data_{period}_{start_date}_to_{end_date}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
