import streamlit as st
import pandas as pd
import datetime
import io
import os
import json

# Set page configuration
st.set_page_config(
    page_title="Foobr Financial Dashboard",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Data persistence functions
def save_data_to_file(data):
    """Save DataFrame to local file for persistence."""
    # Convert to records format for simpler serialization
    if not data.empty:
        # Ensure date is converted to string for JSON serialization
        data_copy = data.copy()
        if 'Date' in data_copy.columns and pd.api.types.is_datetime64_any_dtype(data_copy['Date']):
            data_copy['Date'] = data_copy['Date'].dt.strftime('%Y-%m-%d')
        
        records = data_copy.to_dict('records')
        with open('foobr_financial_data.json', 'w') as f:
            json.dump(records, f)
    else:
        # Create empty file if no data
        with open('foobr_financial_data.json', 'w') as f:
            json.dump([], f)
    
    # Debug info
    st.session_state['debug_message'] = f"Data saved: {len(data)} records"
            
def load_data_from_file():
    """Load DataFrame from local file."""
    try:
        if os.path.exists('foobr_financial_data.json'):
            with open('foobr_financial_data.json', 'r') as f:
                records = json.load(f)
            
            if records:
                df = pd.DataFrame(records)
                if 'Date' in df.columns:
                    df['Date'] = pd.to_datetime(df['Date'])
                st.session_state['debug_message'] = f"Loaded {len(df)} records from file"
                return df
            else:
                st.session_state['debug_message'] = "File exists but contains no records"
        else:
            st.session_state['debug_message'] = "File does not exist yet"
    except Exception as e:
        st.session_state['debug_message'] = f"Error loading data: {e}"
    
    return pd.DataFrame()

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
    .debug-info {
        font-size: 0.8rem;
        color: #888;
        margin-top: 1rem;
    }
    .success-message {
        padding: 1rem;
        background-color: #d4edda;
        color: #155724;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .nav-button {
        margin-top: 1rem;
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
    
    # Convert Date to datetime to ensure consistency
    df['Date'] = pd.to_datetime(df['Date'])
    
    # Initialize financial_data in session state if not exists
    if 'financial_data' not in st.session_state or st.session_state.financial_data is None:
        st.session_state.financial_data = df
    else:
        # Check if entry for this date already exists
        existing_data = st.session_state.financial_data
        
        # Ensure Date column is datetime for comparison
        if 'Date' in existing_data.columns and not pd.api.types.is_datetime64_any_dtype(existing_data['Date']):
            existing_data['Date'] = pd.to_datetime(existing_data['Date'])
        
        # Find matching dates to update
        matching_dates = existing_data['Date'] == pd.to_datetime(formatted_date) if 'Date' in existing_data.columns else []
        date_exists = any(matching_dates) if isinstance(matching_dates, pd.Series) else False
        
        if date_exists:
            # Update existing entry
            existing_data.loc[matching_dates] = df.values
            st.session_state.financial_data = existing_data
        else:
            # Append new entry
            st.session_state.financial_data = pd.concat([existing_data, df], ignore_index=True)
    
    # Save to persistent storage
    save_data_to_file(st.session_state.financial_data)
    
    # Return CSV data for download
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
    elif period == 'day':
        today = pd.Timestamp.today().normalize()
        return data[data['Date'] == today]
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

def switch_to_data_storage_tab():
    """Helper function to switch to the Data Storage tab."""
    st.session_state.active_tab = "Data Storage"

# Main application
def main():
    # Initialize debug message if not present
    if 'debug_message' not in st.session_state:
        st.session_state['debug_message'] = "App initialized"
    
    # Load persistent data into session state FIRST THING when app starts
    if 'financial_data' not in st.session_state:
        st.session_state.financial_data = load_data_from_file()
    
    # Initialize active tab if not present
    if 'active_tab' not in st.session_state:
        st.session_state.active_tab = "Daily Entry"
    
    # Display app title
    st.markdown("<h1 class='main-header'>Foobr Financial Dashboard</h1>", unsafe_allow_html=True)
    
    # Top navigation using tabs
    tab1, tab2, tab3 = st.tabs(["Daily Entry", "Saved Financial Records", "Data Storage"])
    
    # Daily Entry Page
    with tab1:
        st.markdown("<h3 class='subheader'>Daily Financial Entry</h3>", unsafe_allow_html=True)
        
        # Add date selection
        selected_day = st.selectbox("Select Day", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
        report_date = st.date_input("Select Date", datetime.date.today())
        
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
        col_btn1, col_btn2, col_btn3 = st.columns(3)
        with col_btn1:
            calculate_button = st.button("Calculate", use_container_width=True)
        
        with col_btn3:
            go_to_storage_button = st.button("Go to Data Storage", 
                                          on_click=switch_to_data_storage_tab,
                                          use_container_width=True)
        
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
                # Collect values even if Calculate wasn't clicked
                save_data = {
                    'Starting Balance': starting_balance,
                    'Bike Repairs': bike_repairs,
                    'Fuel': fuel,
                    'Airtime': airtime,
                    'End of Day Balance': end_of_day_balance,
                    'Payout': payout,
                    'Orders': orders
                }

                # Recalculate results from raw input
                results = calculate_financials(
                    starting_balance, bike_repairs, fuel, airtime,
                    end_of_day_balance, payout, orders
                )
                save_data.update(results)

                # Save to session and file
                csv_data = save_to_csv(save_data, report_date)
                st.session_state.financial_data = load_data_from_file()  # Reload to include saved entry
                st.success(f"✅ Data for {report_date.strftime('%B %d, %Y')} saved successfully!")
                
                # Store success message for data storage tab
                st.session_state.last_saved_date = report_date.strftime('%B %d, %Y')
                st.session_state.show_storage_success = True
                
                st.download_button(
                    label="⬇️ Download Daily Report",
                    data=csv_data,
                    file_name=f"foobr_financial_data_{report_date.strftime('%Y-%m-%d')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )

    # Historical Data Page
    with tab2:
        st.markdown("<h3 class='subheader'>Saved Financial Records</h3>", unsafe_allow_html=True)
        
        # Get data from session state (saved financial records)
        if 'financial_data' in st.session_state and not st.session_state.financial_data.empty:
            data = st.session_state.financial_data
            
            # Ensure Date column is datetime
            if 'Date' in data.columns and not pd.api.types.is_datetime64_any_dtype(data['Date']):
                data['Date'] = pd.to_datetime(data['Date'])
        else:
            # Try loading from file again as a backup
            data = load_data_from_file()
            if not data.empty:
                st.session_state.financial_data = data
                
        # Button to force refresh data from file
        if st.button("Refresh Data From File"):
            fresh_data = load_data_from_file()
            st.session_state.financial_data = fresh_data
            data = fresh_data
            st.success(f"Data refreshed! Loaded {len(data)} records.")
                
        # Option to upload previous records
        with st.expander("Upload Previous Records"):
            uploaded_file = st.file_uploader("Upload financial data CSV", type="csv")
            if uploaded_file is not None:
                imported_data = load_data_from_csv(uploaded_file)
                if not imported_data.empty:
                    if 'financial_data' not in st.session_state or st.session_state.financial_data.empty:
                        st.session_state.financial_data = imported_data
                    else:
                        # Convert dates for proper comparison
                        if 'Date' in imported_data.columns:
                            imported_data['Date'] = pd.to_datetime(imported_data['Date'])
                        
                        if 'Date' in st.session_state.financial_data.columns:
                            st.session_state.financial_data['Date'] = pd.to_datetime(st.session_state.financial_data['Date'])
                            
                        # Merge data, keeping only unique dates
                        combined = pd.concat([st.session_state.financial_data, imported_data])
                        st.session_state.financial_data = combined.drop_duplicates(subset=['Date']).reset_index(drop=True)
                    
                    # Save to persistent storage
                    save_data_to_file(st.session_state.financial_data)
                    data = st.session_state.financial_data
                    st.success(f"Loaded {len(imported_data)} records from CSV file.")
        
        if data is None or data.empty:
            st.info("No financial records found. Add entries in the Daily Entry tab to see them here.")
        else:
            # Display data summaries by period
            period = st.radio("Filter by:", ["All", "This Week", "This Month"], horizontal=True)
            filtered_data = filter_data_by_period(data, period.lower().replace("this ", ""))
            st.markdown("### Financial Records Summary")
            
            # Ensure Date column is datetime
            if 'Date' in data.columns and not pd.api.types.is_datetime64_any_dtype(data['Date']):
                data['Date'] = pd.to_datetime(data['Date'])
                
            # Get weekly and monthly data
            weekly_data = filter_data_by_period(data, 'week')
            monthly_data = filter_data_by_period(data, 'month')
            
            # Generate summaries
            all_time_summary = generate_summary(data)
            weekly_summary = generate_summary(weekly_data)
            monthly_summary = generate_summary(monthly_data)
            
            # Display summary tiles
            summary_col1, summary_col2, summary_col3 = st.columns(3)
            
            with summary_col1:
                st.markdown("#### This Week")
                st.metric("Records", len(weekly_data))
                st.metric("Revenue", f"₦{weekly_summary.get('Total Revenue', 0):,.2f}")
                st.metric("Orders", f"{weekly_summary.get('Total Orders', 0)}")
                with st.container():
                    if not weekly_data.empty:
                        weekly_csv = weekly_data.to_csv(index=False)
                        st.download_button(
                            label="Export Weekly Records (CSV)",
                            data=weekly_csv,
                            file_name=f"foobr_financial_data_weekly.csv",
                            mime="text/csv",
                            use_container_width=True
                        )
            
            with summary_col2:
                st.markdown("#### This Month")
                st.metric("Records", len(monthly_data))
                st.metric("Revenue", f"₦{monthly_summary.get('Total Revenue', 0):,.2f}")
                st.metric("Orders", f"{monthly_summary.get('Total Orders', 0)}")
                with st.container():
                    if not monthly_data.empty:
                        monthly_csv = monthly_data.to_csv(index=False)
                        st.download_button(
                            label="Export Monthly Records (CSV)",
                            data=monthly_csv,
                            file_name=f"foobr_financial_data_monthly.csv",
                            mime="text/csv",
                            use_container_width=True
                        )
            
            with summary_col3:
                st.markdown("#### All Time")
                st.metric("Records", len(data))
                st.metric("Revenue", f"₦{all_time_summary.get('Total Revenue', 0):,.2f}")
                st.metric("Orders", f"{all_time_summary.get('Total Orders', 0)}")
                with st.container():
                    if not data.empty:
                        all_csv = data.to_csv(index=False)
                        st.download_button(
                            label="Export All Records (CSV)",
                            data=all_csv,
                            file_name=f"foobr_financial_data_all_time.csv",
                            mime="text/csv",
                            use_container_width=True
                        )
            
            # Display all records in a table
            st.markdown("---")
            st.subheader("All Financial Records")
            
            # Format display data
            display_df = filtered_data.copy()
            if not display_df.empty and 'Date' in display_df.columns:
                display_df['Date'] = display_df['Date'].dt.strftime('%b %d, %Y')
                display_df = display_df.sort_values('Date', ascending=False)
            
            # Show the data table
            st.dataframe(display_df)
    
    # New Data Storage Tab
    with tab3:
        st.markdown("<h3 class='subheader'>Data Storage</h3>", unsafe_allow_html=True)
        
        # Show success message if applicable
        if st.session_state.get('show_storage_success', False):
            st.markdown(f"""
            <div class='success-message'>
                ✅ Data for {st.session_state.get('last_saved_date', 'today')} was saved successfully!
                The data is now available for export below.
            </div>
            """, unsafe_allow_html=True)
            # Reset flag to avoid showing on refresh
            st.session_state.show_storage_success = False
        
        # Get data from session state
        if 'financial_data' in st.session_state and not st.session_state.financial_data.empty:
            data = st.session_state.financial_data
            
            # Ensure Date column is datetime
            if 'Date' in data.columns and not pd.api.types.is_datetime64_any_dtype(data['Date']):
                data['Date'] = pd.to_datetime(data['Date'])
        else:
            # Try loading from file again as a backup
            data = load_data_from_file()
            if not data.empty:
                st.session_state.financial_data = data
        
        if data is None or data.empty:
            st.info("No stored financial records found. Add entries in the Daily Entry tab to store them here.")
        else:
            # Select export period
            st.markdown("### Export Financial Data")
            export_period = st.radio(
                "Select export period:",
                ["Daily", "Weekly", "Monthly", "All Time"],
                horizontal=True
            )
            
            # Filter data based on selected period
            period_mapping = {
                "Daily": "day",
                "Weekly": "week",
                "Monthly": "month",
                "All Time": "all"
            }
            filtered_data = filter_data_by_period(data, period_mapping[export_period])
            
            # Show data preview
            st.subheader(f"{export_period} Data Preview")
            
            # Format display data
            display_df = filtered_data.copy()
            if not display_df.empty and 'Date' in display_df.columns:
                display_df['Date'] = display_df['Date'].dt.strftime('%b %d, %Y')
                display_df = display_df.sort_values('Date', ascending=False)
            
            # Show preview with max 5 rows
            preview_rows = min(5, len(display_df))
            st.dataframe(display_df.head(preview_rows))
            
            # Show record count
            st.info(f"Total records for {export_period.lower()} period: {len(filtered_data)}")
            
            # Export options
            st.subheader("Export Options")
            
            export_col1, export_col2 = st.columns(2)
            
            with export_col1:
                if not filtered_data.empty:
                    csv_data = filtered_data.to_csv(index=False)
                    st.download_button(
                        label=f"📥 Export {export_period} Data as CSV",
                        data=csv_data,
                        file_name=f"foobr_financial_{export_period.lower().replace(' ', '_')}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
            
            with export_col2:
                if not filtered_data.empty:
                    # Create Excel format
                    buffer = io.BytesIO()
                    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                        filtered_data.to_excel(writer, sheet_name='Financial Data', index=False)
                    buffer.seek(0)
                    
                    st.download_button(
                        label=f"📊 Export {export_period} Data as Excel",
                        data=buffer,
                        file_name=f"foobr_financial_{export_period.lower().replace(' ', '_')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
            
            # Data summary metrics
            if not filtered_data.empty:
                st.markdown("### Data Summary")
                
                # Calculate summary stats
                summary = generate_summary(filtered_data)
                
                # Display metrics in columns
                metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
                
                with metric_col1:
                    st.metric("Total Revenue", f"₦{summary.get('Total Revenue', 0):,.2f}")
                
                with metric_col2:
                    st.metric("Total Orders", f"{summary.get('Total Orders', 0)}")
                
                with metric_col3:
                    st.metric("Avg Order Value", f"₦{summary.get('Average Order Value', 0):,.2f}")
                
                with metric_col4:
                    st.metric("Avg Daily Revenue", f"₦{summary.get('Average Daily Revenue', 0):,.2f}")
                
                # Additional data management options
                st.markdown("### Data Management")
                
                # Create columns for data management options
                mgmt_col1, mgmt_col2 = st.columns(2)
                
                with mgmt_col1:
                    # Backup data option
                    st.markdown("#### Backup Data")
                    st.markdown("Create a complete backup of all your financial records.")
                    
                    if st.button("Create Full Backup", use_container_width=True):
                        # Create backup with timestamp
                        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                        backup_filename = f"foobr_financial_backup_{timestamp}.csv"
                        
                        backup_csv = data.to_csv(index=False)
                        st.download_button(
                            label="⬇️ Download Backup File",
                            data=backup_csv,
                            file_name=backup_filename,
                            mime="text/csv",
                            use_container_width=True
                        )
                        st.success(f"Backup created successfully! Contains {len(data)} records.")
                
                with mgmt_col2:
                    # Data cleanup options
                    st.markdown("#### Filter Data")
                    st.markdown("View and export data for a specific date range.")
                    
                    # Date range selector
                    start_date = st.date_input("Start Date", 
                                              value=datetime.date.today() - datetime.timedelta(days=30),
                                              key="date_range_start")
                    end_date = st.date_input("End Date", 
                                            value=datetime.date.today(),
                                            key="date_range_end")
                    
                    # Filter button
                    if st.button("Filter by Date Range", use_container_width=True):
                        # Convert dates to pandas datetime
                        start_dt = pd.Timestamp(start_date)
                        end_dt = pd.Timestamp(end_date) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)  # Include end date fully
                        
                        # Apply filter
                        date_filtered = data[(data['Date'] >= start_dt) & (data['Date'] <= end_dt)]
                        
                        if date_filtered.empty:
                            st.warning("No records found for the selected date range.")
                        else:
                            st.success(f"Found {len(date_filtered)} records between {start_date} and {end_date}.")
                            
                            # Format for display
                            display_filtered = date_filtered.copy()
                            display_filtered['Date'] = display_filtered['Date'].dt.strftime('%b %d, %Y')
                            
                            # Show preview
                            st.dataframe(display_filtered)
                            
                            # Export option
                            filtered_csv = date_filtered.to_csv(index=False)
                            date_range_str = f"{start_date.strftime('%Y%m%d')}_to_{end_date.strftime('%Y%m%d')}"
                            
                            st.download_button(
                                label="Export Filtered Data",
                                data=filtered_csv,
                                file_name=f"foobr_financial_{date_range_str}.csv",
                                mime="text/csv",
                                use_container_width=True
                            )
                
                # Advanced data storage options
                with st.expander("Advanced Data Options"):
                    adv_col1, adv_col2 = st.columns(2)
                    
                    with adv_col1:
                        st.markdown("#### Import & Merge Data")
                        st.markdown("Import data from another CSV file and merge with existing records.")
                        
                        uploaded_merge = st.file_uploader("Upload CSV to merge", type="csv", key="merge_uploader")
                        if uploaded_merge is not None:
                            imported_data = load_data_from_csv(uploaded_merge)
                            if not imported_data.empty:
                                if st.button("Merge with Existing Data"):
                                    # Convert dates for proper comparison
                                    if 'Date' in imported_data.columns:
                                        imported_data['Date'] = pd.to_datetime(imported_data['Date'])
                                    
                                    if 'Date' in data.columns:
                                        data['Date'] = pd.to_datetime(data['Date'])
                                        
                                    # Create combined dataset
                                    combined = pd.concat([data, imported_data])
                                    # Drop duplicates by date
                                    deduped = combined.drop_duplicates(subset=['Date']).reset_index(drop=True)
                                    
                                    # Update session state and save
                                    st.session_state.financial_data = deduped
                                    save_data_to_file(deduped)
                                    
                                    st.success(f"Successfully merged data! New total: {len(deduped)} records.")
                    
                    with adv_col2:
                        st.markdown("#### Data Cleanup")
                        st.markdown("Options for cleaning up or resetting your data.")
                        
                        if st.button("Deduplicate Records"):
                            if 'Date' in data.columns:
                                data['Date'] = pd.to_datetime(data['Date'])
                                
                            # Count before deduplication
                            count_before = len(data)
                            
                            # Deduplicate
                            deduped = data.drop_duplicates(subset=['Date']).reset_index(drop=True)
                            
                            # Count after deduplication
                            count_after = len(deduped)
                            dupes_removed = count_before - count_after
                            
                            if dupes_removed > 0:
                                # Update session state and save
                                st.session_state.financial_data = deduped
                                save_data_to_file(deduped)
                                st.success(f"Removed {dupes_removed} duplicate records!")
                            else:
                                st.info("No duplicate records found.")
                
                # About this feature
                with st.expander("About the Data Storage Feature"):
                    st.markdown("""
                    ### About Data Storage
                    
                    This feature allows you to:
                    
                    - Store daily financial entries automatically
                    - Export data in different time periods (daily, weekly, monthly)
                    - Create full backups of your financial records
                    - Filter data by custom date ranges
                    - Import and merge data from other sources
                    - Clean up duplicate records
                    
                    **Data Storage Location:** All data is stored locally in a file called `foobr_financial_data.json`.
                    
                    **Data Privacy:** Your financial data never leaves your computer and is not shared with any third parties.
                    """)
    
    # Run the application
if __name__ == "__main__":
    main()
