import streamlit as st
import pandas as pd
from datetime import datetime
import numpy as np 

# Import functions from the modules
from projection_model import project_herd_yearly, calculate_error 
from db_manager import (
    add_new_cow, 
    log_event, 
    save_projection, 
    get_all_projections, 
    get_projection_data, 
    get_actual_herd_counts, # Function signature changed to accept csv_data
    get_all_cows
)

# --- App Configuration (Professional Look) ---
st.set_page_config(
    page_title="Cattle Projection System",
    page_icon="🐂",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- App Header ---
st.title("🐂 Fibonacci-based Cattle Herd Projection System")
st.caption(f"A professional tool for forecasting and management. Today is {datetime.now().strftime('%A, %B %d, %Y')}.")

# --- Top Horizontal Navigation ---
tab_projection, tab_logging, tab_comparison = st.tabs([
    "📈  Herd Projection", 
    "📝  Event Logging", 
    "📊  Comparison Report"
])


# --- 1. Herd Projection Page ---
with tab_projection:
    st.header("Herd Growth Forecasting")
    
    with st.container(border=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.subheader("1. Initial Herd Data")
            B0 = st.number_input("Initial Breeding Females (B0)", min_value=1, value=20, step=1, help="Adult females (>2 years)")
            Y0 = st.number_input("Initial Juvenile Females (Y0)", min_value=0, value=10, step=1, help="Young females (<2 years)")
        
        with col2:
            st.subheader("2. Model Parameters")
            C = st.slider("Female Calves per Breeder (C)", min_value=0.1, max_value=1.0, value=0.5, step=0.05, 
                          help="Female births per breeder per year.")
            m = st.slider("Annual Mortality Rate (m)", min_value=0.01, max_value=0.20, value=0.05, step=0.01,
                          help="Percentage of female herd that dies per year.")

        with col3:
            st.subheader("3. Simulation Range")
            years = st.number_input("Projection Horizon (Years)", min_value=1, max_value=20, value=10, step=1)
            st.markdown("---")
            
            if st.button("Run Projection and Save", type="primary", use_container_width=True):
                projection_df = project_herd_yearly(B0, Y0, C, m, years)
                save_projection(B0, Y0, C, m, projection_df) 
                st.session_state['last_projection'] = projection_df 
                st.success("Projection complete and saved to database!")

    # --- Projection Results ---
    if 'last_projection' in st.session_state:
        st.subheader("Projection Results")
        
        chart_tab, data_tab = st.tabs(["📈 Chart (Default)", "🗃️ Data Table"])
        
        with chart_tab:
            st.line_chart(
                st.session_state['last_projection'].set_index('Year'), 
                y=['Total Females (Projected)', 'Breeders (Projected)', 'Juveniles (Projected)'],
                color=["#007bff", "#28a745", "#ffc107"] 
            )
            st.caption("This chart displays the projected growth based on your parameters.")

        with data_tab:
            st.dataframe(st.session_state['last_projection'], use_container_width=True, hide_index=True)
            st.caption("This table shows the raw data for each projected year.")


# --- 2. Event Logging Page ---
with tab_logging:
    st.header("Cattle Event Recording")
    
    col_form, col_table = st.columns([1, 2])
    
    with col_form:
        st.subheader("Log a New Event")
        event_type = st.radio("Select Event Type", ["New Birth", "Death / Sale"], horizontal=True, label_visibility="collapsed")
        
        if event_type == "New Birth":
            with st.container(border=True):
                with st.form("new_birth_form", clear_on_submit=True):
                    st.markdown("**Log a New Calf**")
                    calf_id = st.text_input("New Calf ID (e.g., UEMBU-001)")
                    calf_sex = st.selectbox("Sex", ["Female", "Male"])
                    birth_date = st.date_input("Date of Birth", value=datetime.now())
                    mother_id = st.text_input("Mother ID (Optional)")
                    breed = st.text_input("Breed (Optional)")
                    
                    submitted = st.form_submit_button("Log Birth and Add Cow")
                    if submitted:
                        if not calf_id:
                            st.error("Calf ID is required.")
                        elif add_new_cow(calf_id, calf_sex, birth_date.strftime("%Y-%m-%d"), mother_id, breed):
                            log_event(calf_id, "Birth", f"Sex: {calf_sex}, Breed: {breed}")
                            st.success(f"Successfully logged new {calf_sex} calf: {calf_id}")
                        else:
                            st.error(f"Error: Cow ID '{calf_id}' already exists.")
                
        elif event_type == "Death / Sale":
            with st.container(border=True):
                with st.form("cull_form", clear_on_submit=True):
                    st.markdown("**Log Animal Exit**")
                    exit_type = st.selectbox("Exit Type", ["Death", "Sale"])
                    
                    active_cows_df = get_all_cows()
                    active_cows_df = active_cows_df[active_cows_df['status'] == 'Active']
                    cow_id_list = active_cows_df['cow_id'].tolist()
                    
                    if not cow_id_list:
                         st.warning("No active cows in herd to select.")
                         st.form_submit_button(disabled=True)
                    else:
                        cow_id_cull = st.selectbox("Select Cow ID", cow_id_list)
                        details = st.text_area("Reason/Notes (e.g., Illness, Sale Price)")
                        
                        submitted = st.form_submit_button(f"Log {exit_type} Event")
                        if submitted:
                            log_event(cow_id_cull, exit_type, details)
                            st.success(f"Successfully logged {exit_type} for Cow ID: {cow_id_cull}")

    with col_table:
        st.subheader("Current Active Herd")
        
        all_cows_df = get_all_cows()
        active_cows_df = all_cows_df[all_cows_df['status'] == 'Active'].copy()
        
        if active_cows_df.empty:
            st.info("No active cows found in the database. Use the form to log a new birth.")
        else:
            active_cows_df['birth_date'] = pd.to_datetime(active_cows_df['birth_date'])
            active_cows_df['Age (Years)'] = ((datetime.now() - active_cows_df['birth_date']).dt.days / 365.25).round(1)
            
            st.dataframe(
                active_cows_df[['cow_id', 'sex', 'birth_date', 'Age (Years)', 'mother_id', 'breed']],
                use_container_width=True,
                hide_index=True
            )


# --- 3. Comparison Report Page (With Uploader) ---
with tab_comparison:
    st.header("Model Validation: Projected vs. Actual")
    
    with st.container(border=True):
        st.subheader("Select Data for Comparison")
        
        col_select, col_upload = st.columns([1, 1])

        projections_df = get_all_projections()
        
        if projections_df.empty:
            st.warning("No projections found. Please run a projection on the '📈 Herd Projection' tab first.")
            st.stop() # Stop execution here if no projections exist

        with col_select:
            # Create a user-friendly dropdown
            proj_dict = projections_df.set_index('proj_id').to_dict('index')
            selection_options = {
                pid: f"ID {pid} | {data['run_date'].split(' ')[0]} | (B0: {data['B0_start']}, Y0: {data['Y0_start']})"
                for pid, data in proj_dict.items()
            }
            
            selected_id = st.selectbox(
                "1. Select a projection run to evaluate:", 
                options=selection_options.keys(),
                format_func=lambda x: selection_options[x],
                index=0
            )

        with col_upload:
            # --- FILE UPLOADER COMPONENT ---
            uploaded_file = st.file_uploader(
                "2. Upload Historical Data (CSV)",
                type=['csv'],
                help="Upload your historical herd count data (must contain 'Year' and 'Actual_Total' columns)."
            )
            
    # --- Check for uploaded file and proceed with comparison ---
    if selected_id:
        
        # 1. Retrieve saved projection data
        projected_df = get_projection_data(selected_id)
        years_horizon = projected_df['Year'].max()
        
        # 2. Retrieve actual data (passing uploaded file data)
        # Check if a file was uploaded, if so, get its raw bytes
        actual_data_bytes = uploaded_file.getvalue() if uploaded_file else None
        
        # Call the updated db_manager function
        actual_df = get_actual_herd_counts(years_horizon, actual_data_bytes)
        
        # Check if actual data was loaded successfully (i.e., not all NaN)
        # This check confirms the CSV was uploaded AND had the correct columns
        if actual_df['Actual_Total'].isnull().all() and uploaded_file:
             st.error("Error processing file. Please ensure your CSV contains 'Year' and 'Actual_Total' columns.")
             st.stop()
        elif actual_df['Actual_Total'].isnull().all() and not uploaded_file:
             st.info("Please upload a CSV file to compare your projection against historical data.")
             st.stop()
             
        # 3. Merge dataframes
        comparison_df = pd.merge(
            projected_df[['Year', 'Total Females (Projected)']], 
            actual_df[['Year', 'Actual Herd Size (Uploaded)']], # Note the column name change
            on='Year', 
            how='left' 
        ).rename(columns={'Actual Herd Size (Uploaded)': 'Actual Herd Size (Uploaded)'}) # Ensure final column name is clean
        
        # 4. Calculate Errors: Use only the years where Actual data is available (dropna)
        calc_df = comparison_df.dropna() 

        mae, mape = 0.0, 0.0
        if not calc_df.empty:
            projected_counts = calc_df['Total Females (Projected)'].tolist()
            # Use the merged column name for actual data
            actual_counts = calc_df['Actual Herd Size (Uploaded)'].tolist() 
            mae, mape = calculate_error(projected_counts, actual_counts)


        # 5. Display Metrics
        st.markdown("---")
        st.subheader("Model Accuracy Metrics")
        
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.metric("Mean Absolute Error (MAE)", f"{mae:.2f} Cows")
        with col_m2:
            st.metric("Mean Absolute Percentage Error (MAPE)", f"{mape:.2f} %")
        
        # 6. Display Chart & Table
        st.markdown("---")
        st.subheader("Comparison Chart")
        
        st.line_chart(
            comparison_df.set_index('Year'), 
            y=['Total Females (Projected)', 'Actual Herd Size (Uploaded)'], 
            color=["#007bff", "#dc3545"] 
        )
        
        with st.expander("Show Comparison Data Table"):
            st.dataframe(comparison_df, use_container_width=True, hide_index=True)
            st.caption(f"Comparison calculated over {len(calc_df)} years of available uploaded data.")
