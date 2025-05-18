import streamlit as st
import pandas as pd
from datetime import datetime
import hashlib
from utils import (
    initialize_data, hash_password, parse_user_agent,
    return_device, get_active_assignments, get_device_history
)

# Initialize session state variables
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'current_user' not in st.session_state:
    st.session_state.current_user = None
if 'user_role' not in st.session_state:
    st.session_state.user_role = None
if 'user_added' not in st.session_state:
    st.session_state.user_added = False
if 'password_reset' not in st.session_state:
    st.session_state.password_reset = False
if 'edit_mode' not in st.session_state:
    st.session_state.edit_mode = False

# Detect if user is on mobile device
if 'is_mobile' not in st.session_state:
    try:
        user_agent = st.get_option('browser.serverAddress')
        ua_info = parse_user_agent(st.request_headers.get('User-Agent', ''))
        st.session_state.is_mobile = 'Mobile' in ua_info.get('device', '') or 'Tablet' in ua_info.get('device', '')
    except:
        # Set to False if detection fails
        st.session_state.is_mobile = False

# Page configuration must be the first Streamlit command
st.set_page_config(
    page_title="Device Login Tracker",
    page_icon="📱",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize data (after page config)
initialize_data()

# Add custom CSS with mobile and tablet optimizations
st.markdown("""
<style>
    /* Center content on all devices */
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        max-width: 1200px;
        margin-left: auto;
        margin-right: auto;
    }

    .floating-logout {
        position: fixed;
        bottom: 20px;
        right: 20px;
        z-index: 999;
    }
    .logout-btn {
        background-color: #f44336;
        color: white;
        padding: 10px 20px;
        border: none;
        border-radius: 5px;
        font-weight: bold;
        cursor: pointer;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        transition: all 0.3s;
    }
    .logout-btn:hover {
        background-color: #d32f2f;
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.3);
    }

    /* iPad/Tablet optimizations (768px - 1024px) */
    @media (min-width: 768px) and (max-width: 1024px) {
        .main .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
            padding-left: 2rem;
            padding-right: 2rem;
            max-width: 90%;
        }

        /* Ensure forms and inputs are properly sized on iPads */
        .stSelectbox, .stTextInput > div, .stDateInput > div, .stNumberInput > div {
            max-width: 100%;
        }

        /* Improve dataframe display on iPads */
        [data-testid="stDataFrame"] {
            width: 100%;
            overflow-x: auto;
        }
    }

    /* Mobile optimizations (smaller than 768px) */
    @media (max-width: 767px) {
        .main .block-container {
            padding-top: 0.5rem;
            padding-bottom: 0.5rem;
            padding-left: 0.5rem;
            padding-right: 0.5rem;
        }
        h1, h2, h3 {
            font-size: 1.5rem !important;
        }
        .stButton > button {
            width: 100%;
            min-height: 2.5rem;
        }
        .stSelectbox, .stTextInput > div, .stDateInput > div, .stNumberInput > div {
            width: 100%;
        }
        /* Improve touch targets for mobile */
        button, select, input {
            min-height: 44px !important;
        }
        /* Adjust column layouts on small screens */
        [data-testid="column"] {
            width: 100% !important;
            flex: 1 1 100% !important;
            min-width: 100% !important;
        }
        /* Make dataframes scrollable horizontally on mobile */
        [data-testid="stDataFrame"] {
            overflow-x: auto;
            -webkit-overflow-scrolling: touch;
        }
    }
</style>
""", unsafe_allow_html=True)

def athlete_device_checkout():
    """Interface for athletes to check out devices"""
    # Get the athlete's full name
    user_data = st.session_state.users[st.session_state.users['username'] == st.session_state.current_user]
    if not user_data.empty:
        full_name = f"{user_data.iloc[0]['first_name']} {user_data.iloc[0]['last_name']}"
    else:
        full_name = st.session_state.current_user

    st.markdown(f"## Welcome, {full_name}!")

    # Get athlete's active checkouts
    active_devices = get_active_assignments()
    athlete_active_devices = active_devices[active_devices['employee_name'] == st.session_state.current_user]

    # Show checked out devices
    if not athlete_active_devices.empty:
        st.subheader("Your Checked Out Devices")
        for _, row in athlete_active_devices.iterrows():
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                st.write(f"**Device:** {row['device_id']}")
            with col2:
                st.write(f"**Type:** {row['device_type']}")
            with col3:
                if st.button(f"Return Device {row['device_id']}"):
                    if return_device(row['device_id']):
                        st.success(f"Successfully returned {row['device_id']}")
                        st.rerun()

    # Checkout new device
    st.subheader("Check Out a Device")

    # Generate device lists
    athlete_devices = [str(i) for i in range(1, 36)]
    payment_terminals = [str(i) for i in range(36, 51)]

    # Get all currently checked out devices
    all_active_device_ids = active_devices['device_id'].tolist()

    # Filter available devices (remove ones already checked out)
    available_athlete_devices = [d for d in athlete_devices if d not in all_active_device_ids]
    available_payment_terminals = [d for d in payment_terminals if d not in all_active_device_ids]

    # Check if user already has devices checked out
    has_athlete_device = False
    has_payment_terminal = False

    if not athlete_active_devices.empty:
        for _, device in athlete_active_devices.iterrows():
            if device['device_type'] == "Athlete Device":
                has_athlete_device = True
            elif device['device_type'] == "Payment Terminal":
                has_payment_terminal = True

    # Create checkout form - responsive layout
    if st.session_state.get("is_mobile", False):
        # Stack vertically on mobile
        st.markdown("### Athlete Device")
        if not has_athlete_device and available_athlete_devices:
            athlete_device_id = st.selectbox(
                "Select Athlete Device (1-35)", 
                ["None"] + available_athlete_devices
            )
        elif has_athlete_device:
            st.info("You already have an Athlete Device checked out.")
            athlete_device_id = "None"
        else:
            st.warning("No Athlete Devices available.")
            athlete_device_id = "None"

        st.markdown("### Payment Terminal")
        if not has_payment_terminal and available_payment_terminals:
            payment_terminal_id = st.selectbox(
                "Select Payment Terminal (36-50)", 
                ["None"] + available_payment_terminals
            )
        elif has_payment_terminal:
            st.info("You already have a Payment Terminal checked out.")
            payment_terminal_id = "None"
        else:
            st.warning("No Payment Terminals available.")
            payment_terminal_id = "None"
    else:
        # Side by side on desktop
        col1, col2 = st.columns(2)

        # Athlete Device dropdown
        with col1:
            st.markdown("### Athlete Device")
            if not has_athlete_device and available_athlete_devices:
                athlete_device_id = st.selectbox(
                    "Select Athlete Device (1-35)", 
                    ["None"] + available_athlete_devices
                )
            elif has_athlete_device:
                st.info("You already have an Athlete Device checked out.")
                athlete_device_id = "None"
            else:
                st.warning("No Athlete Devices available.")
                athlete_device_id = "None"

        # Payment Terminal dropdown
        with col2:
            st.markdown("### Payment Terminal")
            if not has_payment_terminal and available_payment_terminals:
                payment_terminal_id = st.selectbox(
                    "Select Payment Terminal (36-50)", 
                    ["None"] + available_payment_terminals
                )
            elif has_payment_terminal:
                st.info("You already have a Payment Terminal checked out.")
                payment_terminal_id = "None"
            else:
                st.warning("No Payment Terminals available.")
                payment_terminal_id = "None"

    # Checkout button
    if athlete_device_id != "None" or payment_terminal_id != "None":
        if st.button("Check Out Selected Devices"):
            if athlete_device_id != "None":
                # Create new assignment for athlete device
                new_assignment = pd.DataFrame({
                    'device_id': [athlete_device_id],
                    'employee_name': [st.session_state.current_user],
                    'checkout_time': [datetime.now()],
                    'checkin_time': [None],
                    'device_type': ["Athlete Device"]
                })
                st.session_state.device_assignments = pd.concat(
                    [st.session_state.device_assignments, new_assignment], 
                    ignore_index=True
                )
                st.success(f"Successfully checked out Athlete Device #{athlete_device_id}")

            if payment_terminal_id != "None":
                # Create new assignment for payment terminal
                new_assignment = pd.DataFrame({
                    'device_id': [payment_terminal_id],
                    'employee_name': [st.session_state.current_user],
                    'checkout_time': [datetime.now()],
                    'checkin_time': [None],
                    'device_type': ["Payment Terminal"]
                })
                st.session_state.device_assignments = pd.concat(
                    [st.session_state.device_assignments, new_assignment], 
                    ignore_index=True
                )
                st.success(f"Successfully checked out Payment Terminal #{payment_terminal_id}")

            st.rerun()

def admin_device_overview():
    """Admin interface showing device status"""
    st.markdown("## Device Management Dashboard")

    # Tabs for different views - hide User Management for specialists
    if st.session_state.user_role == 'specialist':
        tab_personal, tab1, tab2 = st.tabs(["My Devices", "Active Checkouts", "History"])
    else:
        tab_personal, tab1, tab2, tab3 = st.tabs(["My Devices", "Active Checkouts", "History", "User Management"])

    # Get the admin's full name
    user_data = st.session_state.users[st.session_state.users['username'] == st.session_state.current_user]
    if not user_data.empty:
        full_name = f"{user_data.iloc[0]['first_name']} {user_data.iloc[0]['last_name']}"
    else:
        full_name = st.session_state.current_user

    # Personal device checkout tab - similar to athlete interface
    with tab_personal:
        st.markdown(f"## Welcome, {full_name}!")

        # Get coach/specialist's active checkouts
        active_devices = get_active_assignments()
        personal_devices = active_devices[active_devices['employee_name'] == st.session_state.current_user]

        # Show checked out devices
        if not personal_devices.empty:
            st.subheader("Your Checked Out Devices")
            for _, row in personal_devices.iterrows():
                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    st.write(f"**Device:** {row['device_id']}")
                with col2:
                    st.write(f"**Type:** {row['device_type']}")
                with col3:
                    if st.button(f"Return Device {row['device_id']}"):
                        if return_device(row['device_id']):
                            st.success(f"Successfully returned {row['device_id']}")
                            st.rerun()

        # Checkout new device
        st.subheader("Check Out a Device")

        # Generate device lists
        athlete_devices = [str(i) for i in range(1, 36)]
        payment_terminals = [str(i) for i in range(36, 51)]

        # Get all currently checked out devices
        all_active_device_ids = active_devices['device_id'].tolist()

        # Filter available devices (remove ones already checked out)
        available_athlete_devices = [d for d in athlete_devices if d not in all_active_device_ids]
        available_payment_terminals = [d for d in payment_terminals if d not in all_active_device_ids]

        # Check if user already has devices checked out
        has_athlete_device = False
        has_payment_terminal = False

        if not personal_devices.empty:
            for _, device in personal_devices.iterrows():
                if device['device_type'] == "Athlete Device":
                    has_athlete_device = True
                elif device['device_type'] == "Payment Terminal":
                    has_payment_terminal = True

        # Create checkout form - responsive layout
        if st.session_state.get("is_mobile", False):
            # Stack vertically on mobile
            st.markdown("### Athlete Device")
            if not has_athlete_device and available_athlete_devices:
                athlete_device_id = st.selectbox(
                    "Select Athlete Device (1-35)",
                    ["None"] + available_athlete_devices,
                    key="personal_athlete_device_mobile"
                )
            elif has_athlete_device:
                st.info("You already have an Athlete Device checked out.")
                athlete_device_id = "None"
            else:
                st.warning("No Athlete Devices available.")
                athlete_device_id = "None"

            st.markdown("### Payment Terminal")
            if not has_payment_terminal and available_payment_terminals:
                payment_terminal_id = st.selectbox(
                    "Select Payment Terminal (36-50)",
                    ["None"] + available_payment_terminals,
                    key="personal_payment_terminal_mobile"
                )
            elif has_payment_terminal:
                st.info("You already have a Payment Terminal checked out.")
                payment_terminal_id = "None"
            else:
                st.warning("No Payment Terminals available.")
                payment_terminal_id = "None"
        else:
            # Side by side on desktop
            col1, col2 = st.columns(2)

            # Athlete Device dropdown
            with col1:
                st.markdown("### Athlete Device")
                if not has_athlete_device and available_athlete_devices:
                    athlete_device_id = st.selectbox(
                        "Select Athlete Device (1-35)",
                        ["None"] + available_athlete_devices,
                        key="personal_athlete_device_desktop"
                    )
                elif has_athlete_device:
                    st.info("You already have an Athlete Device checked out.")
                    athlete_device_id = "None"
                else:
                    st.warning("No Athlete Devices available.")
                    athlete_device_id = "None"

            # Payment Terminal dropdown
            with col2:
                st.markdown("### Payment Terminal")
                if not has_payment_terminal and available_payment_terminals:
                    payment_terminal_id = st.selectbox(
                        "Select Payment Terminal (36-50)",
                        ["None"] + available_payment_terminals,
                        key="personal_payment_terminal_desktop"
                    )
                elif has_payment_terminal:
                    st.info("You already have a Payment Terminal checked out.")
                    payment_terminal_id = "None"
                else:
                    st.warning("No Payment Terminals available.")
                    payment_terminal_id = "None"

        # Checkout button
        if athlete_device_id != "None" or payment_terminal_id != "None":
            if st.button("Check Out Selected Devices", key="personal_checkout_button"):
                if athlete_device_id != "None":
                    # Create new assignment for athlete device
                    new_assignment = pd.DataFrame({
                        'device_id': [athlete_device_id],
                        'employee_name': [st.session_state.current_user],
                        'checkout_time': [datetime.now()],
                        'checkin_time': [None],
                        'device_type': ["Athlete Device"]
                    })
                    st.session_state.device_assignments = pd.concat(
                        [st.session_state.device_assignments, new_assignment],
                        ignore_index=True
                    )
                    st.success(f"Successfully checked out Athlete Device #{athlete_device_id}")

                if payment_terminal_id != "None":
                    # Create new assignment for payment terminal
                    new_assignment = pd.DataFrame({
                        'device_id': [payment_terminal_id],
                        'employee_name': [st.session_state.current_user],
                        'checkout_time': [datetime.now()],
                        'checkin_time': [None],
                        'device_type': ["Payment Terminal"]
                    })
                    st.session_state.device_assignments = pd.concat(
                        [st.session_state.device_assignments, new_assignment],
                        ignore_index=True
                    )
                    st.success(f"Successfully checked out Payment Terminal #{payment_terminal_id}")

                st.rerun()

    # This section has been removed (Athlete Checkout tab)

    with tab1:
        st.subheader("Active Devices")

        # Filter controls
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            # Get list of all active device IDs
            active_device_ids = ['All'] + sorted(active_devices['device_id'].unique().tolist())
            filter_device_id = st.selectbox("Filter by Device ID", active_device_ids)
        with col2:
            device_types = ['All'] + list(st.session_state.device_assignments['device_type'].unique())
            filter_device_type = st.selectbox("Filter by Device Type", device_types)
        with col3:
            # Create athlete list with names for better identification
            athlete_usernames = ['All'] + list(st.session_state.device_assignments['employee_name'].unique())
            athlete_options = ['All']

            # Add formatted options with names for all usernames except 'All'
            for username in athlete_usernames:
                if username != 'All':
                    user_data = st.session_state.users[st.session_state.users['username'] == username]
                    if not user_data.empty:
                        first_name = user_data.iloc[0]['first_name']
                        last_name = user_data.iloc[0]['last_name']
                        athlete_options.append(f"{username} - {first_name} {last_name}")

            filter_athlete = st.selectbox("Filter by Athlete", athlete_options)
            # Extract username from the selection for filtering
            if filter_athlete != 'All':
                filter_athlete_username = filter_athlete.split(" - ")[0]
            else:
                filter_athlete_username = 'All'

        # Get active assignments
        active_devices = get_active_assignments()

        if not active_devices.empty:
            # Apply filters
            if filter_device_id != 'All':
                active_devices = active_devices[active_devices['device_id'] == filter_device_id]
            if filter_device_type != 'All':
                active_devices = active_devices[active_devices['device_type'] == filter_device_type]
            if filter_athlete_username != 'All':
                active_devices = active_devices[active_devices['employee_name'] == filter_athlete_username]

            # Format for display
            display_df = active_devices.copy()
            display_df['checkout_time'] = display_df['checkout_time'].apply(
                lambda x: x.strftime("%Y-%m-%d %H:%M:%S") if pd.notna(x) else ""
            )

            # Add first and last name columns by looking up user data
            display_df['First Name'] = ""
            display_df['Last Name'] = ""

            # Populate first and last names for each row
            for idx, row in display_df.iterrows():
                user_data = st.session_state.users[st.session_state.users['username'] == row['employee_name']]
                if not user_data.empty:
                    display_df.at[idx, 'First Name'] = user_data.iloc[0]['first_name']
                    display_df.at[idx, 'Last Name'] = user_data.iloc[0]['last_name']

            display_df = display_df.rename(columns={
                'device_id': 'Device ID',
                'employee_name': 'Employee ID',
                'checkout_time': 'Checkout Time',
                'device_type': 'Device Type'
            })

            st.dataframe(display_df[['Device ID', 'Device Type', 'Employee ID', 'First Name', 'Last Name', 'Checkout Time']], use_container_width=True)

            # Add collapsible section for device management actions
            with st.expander("Device Management Actions"):
                management_tabs = st.tabs(["Assign Device", "Return Device"])

                # Tab for assigning devices to others
                with management_tabs[0]:
                    # Get all users from the system
                    all_users = st.session_state.users.copy()
                    user_options = [f"{row['username']} - {row['first_name']} {row['last_name']}" for _, row in all_users.iterrows()]

                    # Generate device lists
                    athlete_devices = [str(i) for i in range(1, 36)]
                    payment_terminals = [str(i) for i in range(36, 51)]

                    # Get all currently checked out devices
                    all_active_device_ids = active_devices['device_id'].tolist()

                    # Filter available devices (remove ones already checked out)
                    available_athlete_devices = [d for d in athlete_devices if d not in all_active_device_ids]
                    available_payment_terminals = [d for d in payment_terminals if d not in all_active_device_ids]

                    # Create assign form
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        selected_user = st.selectbox("Select User", user_options, key="assign_user_select")
                        # Extract username from selection
                        selected_username = selected_user.split(" - ")[0] if selected_user else ""

                    with col2:
                        device_type = st.selectbox("Device Type", ["Athlete Device", "Payment Terminal"], key="assign_device_type")

                        if device_type == "Athlete Device":
                            if available_athlete_devices:
                                device_id = st.selectbox("Select Device", available_athlete_devices, key="assign_athlete_device")
                            else:
                                st.warning("No Athlete Devices available")
                                device_id = None
                        else:
                            if available_payment_terminals:
                                device_id = st.selectbox("Select Device", available_payment_terminals, key="assign_payment_terminal")
                            else:
                                st.warning("No Payment Terminals available")
                                device_id = None

                    with col3:
                        st.write("")  # Space for alignment
                        st.write("")  # Space for alignment
                        if st.button("Assign Device") and device_id and selected_username:
                            # Create new assignment
                            new_assignment = pd.DataFrame({
                                'device_id': [device_id],
                                'employee_name': [selected_username],
                                'checkout_time': [datetime.now()],
                                'checkin_time': [None],
                                'device_type': [device_type]
                            })

                            st.session_state.device_assignments = pd.concat(
                                [st.session_state.device_assignments, new_assignment],
                                ignore_index=True
                            )

                            st.success(f"Successfully assigned {device_type} #{device_id} to {selected_username}")
                            st.rerun()

                # Tab for forcing return of devices
                with management_tabs[1]:
                    if active_devices.empty:
                        st.info("No devices currently checked out to return.")
                    else:
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            return_device_id = st.selectbox("Select Device to Return", active_devices['device_id'].tolist())
                        with col2:
                            st.write("")  # Space for alignment
                            if st.button("Return Device"):
                                if return_device(return_device_id):
                                    st.success(f"Successfully returned {return_device_id}")
                                    st.rerun()
        else:
            st.info("No devices are currently checked out.")

    with tab2:
        st.subheader("Device Checkout History")

        # Get all history data before defining filters
        history = get_device_history()

        # First expander for basic filters
        with st.expander("Basic Filters", expanded=False):
            # Responsive layout for filters - stack vertically on mobile
            if st.session_state.get("is_mobile", False):
                # Get list of all device IDs in system (1-50)
                all_device_ids = ['All'] + [str(i) for i in range(1, 51)]
                history_filter_device_id = st.selectbox("Filter History by Device ID", all_device_ids)
                history_device_types = ['All'] + list(st.session_state.device_assignments['device_type'].unique())
                history_filter_device_type = st.selectbox("Filter History by Device Type", history_device_types)
                # Create athlete list with names for better identification
                athlete_usernames = ['All'] + list(st.session_state.device_assignments['employee_name'].unique())
                history_athlete_options = ['All']

                # Add formatted options with names for all usernames except 'All'
                for username in athlete_usernames:
                    if username != 'All':
                        user_data = st.session_state.users[st.session_state.users['username'] == username]
                        if not user_data.empty:
                            first_name = user_data.iloc[0]['first_name']
                            last_name = user_data.iloc[0]['last_name']
                            history_athlete_options.append(f"{username} - {first_name} {last_name}")

                history_filter_athlete = st.selectbox("Filter History by Athlete", history_athlete_options)
                # Extract username from the selection for filtering
                if history_filter_athlete != 'All':
                    history_filter_athlete_username = history_filter_athlete.split(" - ")[0]
                else:
                    history_filter_athlete_username = 'All'
            else:
                # Desktop layout
                col1, col2, col3 = st.columns(3)
                with col1:
                    # Get list of all device IDs in history
                    history_device_ids = ['All'] + sorted(history['device_id'].unique().tolist())
                    history_filter_device_id = st.selectbox("Filter History by Device ID", history_device_ids)
                with col2:
                    history_device_types = ['All'] + list(st.session_state.device_assignments['device_type'].unique())
                    history_filter_device_type = st.selectbox("Filter History by Device Type", history_device_types)
                with col3:
                    # Create athlete list with names for better identification
                    athlete_usernames = ['All'] + list(st.session_state.device_assignments['employee_name'].unique())
                    history_athlete_options = ['All']

                    # Add formatted options with names for all usernames except 'All'
                    for username in athlete_usernames:
                        if username != 'All':
                            user_data = st.session_state.users[st.session_state.users['username'] == username]
                            if not user_data.empty:
                                first_name = user_data.iloc[0]['first_name']
                                last_name = user_data.iloc[0]['last_name']
                                history_athlete_options.append(f"{username} - {first_name} {last_name}")

                    history_filter_athlete = st.selectbox("Filter History by Athlete", history_athlete_options)
                    # Extract username from the selection for filtering
                    if history_filter_athlete != 'All':
                        history_filter_athlete_username = history_filter_athlete.split(" - ")[0]
                    else:
                        history_filter_athlete_username = 'All'

        # Separate expander for date filters
        with st.expander("Date Range Filters", expanded=False):
            # Date filter row
            date_col1, date_col2 = st.columns(2)
            with date_col1:
                st.subheader("Start Date/Time")
                start_date = st.date_input("Start Date", value=None)
                start_time_cols = st.columns(2)
                with start_time_cols[0]:
                    start_hour = st.number_input("Hour", min_value=0, max_value=23, value=0, step=1)
                with start_time_cols[1]:
                    start_minute = st.number_input("Minute", min_value=0, max_value=59, value=0, step=1)

            with date_col2:
                st.subheader("End Date/Time")
                end_date = st.date_input("End Date", value=None)
                end_time_cols = st.columns(2)
                with end_time_cols[0]:
                    end_hour = st.number_input("Hour", min_value=0, max_value=23, value=23, step=1)
                with end_time_cols[1]:
                    end_minute = st.number_input("Minute", min_value=0, max_value=59, value=59, step=1)

        # Get all history


        if not history.empty:
            # Apply filters
            if history_filter_device_id != 'All':
                history = history[history['device_id'] == history_filter_device_id]
            if history_filter_device_type != 'All':
                history = history[history['device_type'] == history_filter_device_type]
            if history_filter_athlete_username != 'All':
                history = history[history['employee_name'] == history_filter_athlete_username]

            # Apply date and time filters if selected
            if start_date:
                # Create a datetime with the specified date and time
                start_datetime = pd.Timestamp(
                    year=start_date.year,
                    month=start_date.month,
                    day=start_date.day,
                    hour=start_hour,
                    minute=start_minute
                )
                history = history[history['checkout_time'] >= start_datetime]

            if end_date:
                # Create a datetime with the specified date and time
                end_datetime = pd.Timestamp(
                    year=end_date.year,
                    month=end_date.month,
                    day=end_date.day,
                    hour=end_hour,
                    minute=end_minute
                )
                history = history[history['checkout_time'] <= end_datetime]

            # Format for display
            display_history = history.copy()
            display_history['checkout_time'] = display_history['checkout_time'].apply(
                lambda x: x.strftime("%Y-%m-%d %H:%M:%S") if pd.notna(x) else ""
            )
            display_history['checkin_time'] = display_history['checkin_time'].apply(
                lambda x: x.strftime("%Y-%m-%d %H:%M:%S") if pd.notna(x) else "Not returned"
            )

            # Add first and last name columns by looking up user data
            display_history['First Name'] = ""
            display_history['Last Name'] = ""

            # Populate first and last names for each row
            for idx, row in display_history.iterrows():
                user_data = st.session_state.users[st.session_state.users['username'] == row['employee_name']]
                if not user_data.empty:
                    display_history.at[idx, 'First Name'] = user_data.iloc[0]['first_name']
                    display_history.at[idx, 'Last Name'] = user_data.iloc[0]['last_name']

            display_history = display_history.rename(columns={
                'device_id': 'Device ID',
                'employee_name': 'Employee ID',
                'checkout_time': 'Checkout Time',
                'checkin_time': 'Check-in Time',
                'device_type': 'Device Type'
            })

            st.dataframe(
                display_history[['Device ID', 'Device Type', 'Employee ID', 'First Name', 'Last Name', 'Checkout Time', 'Check-in Time']],
                use_container_width=True
            )
        else:
            st.info("No device history available.")

    # Only run the User Management tab code if user is an admin and tab3 exists
    if st.session_state.user_role == 'coach' and 'tab3' in locals():
        with tab3:
            st.subheader("User Management Dashboard")

            # Copy the users DataFrame to avoid modifying the original during display
            users_df = st.session_state.users.copy()

            # Show users table first (most important)
            st.write("Current Users")
            # Convert passwords to masked display for security
            users_df['password_display'] = '********'

            # Create an editable dataframe
            edited_df = st.data_editor(
                users_df[['username', 'first_name', 'last_name', 'password_display', 'role']],
                column_config={
                    "username": "Employee ID",
                    "first_name": "First Name",
                    "last_name": "Last Name",
                    "password_display": st.column_config.TextColumn(
                        "Password",
                        help="Passwords are stored securely and not displayed in plain text",
                        disabled=True
                    ),
                    "role": st.column_config.SelectboxColumn(
                        "Role",
                        options=["coach", "athlete", "specialist"],
                        help="User role determines access level"
                    )
                },
                hide_index=True,
                num_rows="dynamic",
                key="user_table"
            )

            # Save changes button
            if st.button("Save User Changes", key="save_user_changes"):
                # Update first_name, last_name and role (but not password)
                for index, row in edited_df.iterrows():
                    if index < len(st.session_state.users):
                        st.session_state.users.loc[index, 'first_name'] = row['first_name']
                        st.session_state.users.loc[index, 'last_name'] = row['last_name']
                        st.session_state.users.loc[index, 'role'] = row['role']
                
                # Save users to file for persistence
                st.session_state.users.to_csv('users.csv', index=False)
                st.success("User information updated successfully!")

            # User action tabs in an expander to keep them hidden until needed
            with st.expander("User Management Actions"):
                user_actions = st.tabs(["Add User", "Reset Password", "Remove User"])

                # Tab 1: Add new user
                with user_actions[0]:
                    with st.form("add_user_form"):
                        # Use a form counter to reset the form
                        if 'add_user_form_counter' not in st.session_state:
                            st.session_state.add_user_form_counter = 0

                        # Generate unique keys for each input field
                        form_id = st.session_state.add_user_form_counter

                        new_username = st.text_input("Employee ID", max_chars=6, key=f"username_{form_id}")

                        # Validate that input is numeric and max 6 digits
                        if new_username and (not new_username.isdigit() or len(new_username) > 6):
                            st.error("Employee ID must be numeric and maximum 6 digits")

                        new_first_name = st.text_input("First Name", key=f"first_name_{form_id}")
                        new_last_name = st.text_input("Last Name", key=f"last_name_{form_id}")
                        new_password = st.text_input("Password", type="password", key=f"password_{form_id}")
                        confirm_password = st.text_input("Confirm Password", type="password", key=f"confirm_password_{form_id}")
                        new_role = st.selectbox("Role", ["athlete", "coach", "specialist"])

                        submit_button = st.form_submit_button("Add User")

                        if submit_button:
                            if not new_username or not new_password:
                                st.error("Employee ID and password are required.")
                            elif new_password != confirm_password:
                                st.error("Passwords do not match.")
                            elif new_username in st.session_state.users['username'].values:
                                st.error("Employee ID already exists.")
                            else:
                                # Add new user
                                new_user = pd.DataFrame({
                                    'username': [new_username],
                                    'password': [hash_password(new_password)],
                                    'role': [new_role],
                                    'first_name': [new_first_name],
                                    'last_name': [new_last_name]
                                })

                                st.session_state.users = pd.concat([st.session_state.users, new_user], ignore_index=True)
                                # Save users to file for persistence
                                st.session_state.users.to_csv('users.csv', index=False)
                                st.success(f"Added new user: {new_username}")

                                # Increment the form counter to generate new form keys on next render
                                st.session_state.add_user_form_counter += 1

                                # Using session state to control rerun
                                st.session_state.user_added = True
                                st.rerun()

                # Tab 2: Reset password
                with user_actions[1]:
                    # Use a form counter to reset the password form
                    if 'reset_pwd_form_counter' not in st.session_state:
                        st.session_state.reset_pwd_form_counter = 0

                    with st.form("reset_password_form"):
                        # Generate unique keys for each input field
                        pwd_form_id = st.session_state.reset_pwd_form_counter

                        username_to_reset = st.text_input("Employee ID", max_chars=6, key=f"username_reset_{pwd_form_id}")
                        new_pwd = st.text_input("New Password", type="password", key=f"new_pwd_{pwd_form_id}")
                        confirm_pwd = st.text_input("Confirm New Password", type="password", key=f"confirm_pwd_{pwd_form_id}")

                        reset_button = st.form_submit_button("Reset Password")

                        if reset_button:
                            if not username_to_reset:
                                st.error("Employee ID cannot be empty")
                            elif not new_pwd:
                                st.error("Password cannot be empty")
                            elif new_pwd != confirm_pwd:
                                st.error("Passwords do not match")
                            else:
                                # Find user and update password
                                user_idx = st.session_state.users.index[st.session_state.users['username'] == username_to_reset].tolist()
                                if user_idx:
                                    st.session_state.users.loc[user_idx[0], 'password'] = hash_password(new_pwd)
                                    # Save users to file for persistence
                                    st.session_state.users.to_csv('users.csv', index=False)
                                    st.success(f"Password reset for {username_to_reset}")

                                    # Increment the form counter to generate new form keys on next render
                                    st.session_state.reset_pwd_form_counter += 1

                                    # Using session state to control rerun
                                    st.session_state.password_reset = True
                                    st.rerun()
                                else:
                                    st.error(f"Employee ID {username_to_reset} not found.")

                # Tab 3: Remove employee
                with user_actions[2]:
                    col_input, col_button = st.columns([3, 1])

                    with col_input:
                        employee_to_remove = st.text_input("Employee ID For Removal", max_chars=6, key="employee_to_remove")

                    with col_button:
                        # Add some vertical space to align with the text input
                        st.write("")
                        st.write("")
                        if st.button("Remove Employee", key="remove_employee"):
                            if not employee_to_remove:
                                st.error("Please enter an Employee ID to remove.")
                            elif employee_to_remove not in st.session_state.users['username'].values:
                                st.error(f"Employee ID {employee_to_remove} not found.")
                            elif employee_to_remove == '000001':
                                st.error("Cannot remove the main administrator account.")
                            else:
                                # Get user info before removing
                                user_to_remove = st.session_state.users[st.session_state.users['username'] == employee_to_remove].iloc[0]
                                employee_name = f"{user_to_remove['first_name']} {user_to_remove['last_name']}"

                                # Remove the user
                                st.session_state.users = st.session_state.users[st.session_state.users['username'] != employee_to_remove]
                                # Save users to file for persistence
                                st.session_state.users.to_csv('users.csv', index=False)
                                st.success(f"Employee {employee_name} (ID: {employee_to_remove}) removed successfully!")
                                st.rerun()

def login_page():
    """Login page UI"""
    # Display the login form with custom styling
    st.markdown("""
    <style>
    .login-form {
        max-width: 400px;
        width: 90%;
        margin: 0 auto;
        padding: 20px;
        background-color: #ffffff;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-top: 20px;
    }
    .login-title {
        text-align: center;
        margin-bottom: 10px;
        color: #444444;
        font-size: 1.8rem;
    }
    .login-subtitle {
        text-align: center;
        margin-bottom: 15px;
        color: #6c757d;
        font-size: 18px;
    }
    /* iPad/Tablet optimizations for login (768px - 1024px) */
    @media (min-width: 768px) and (max-width: 1024px) {
        .login-form {
            max-width: 500px;
            width: 70%;
            padding: 30px;
            margin-top: 50px;
        }
        .login-title {
            font-size: 2rem !important;
        }
        .login-subtitle {
            font-size: 1.2rem !important;
        }
    }
    /* Mobile optimizations for login */
    @media (max-width: 767px) {
        .login-form {
            width: 95%;
            padding: 20px;
        }
        .login-title {
            font-size: 1.5rem !important;
        }
        .login-subtitle {
            font-size: 1rem !important;
        }
    }
    </style>
    <div class="login-form">
        <h1 class="login-title">Device Management</h1>
    </div>
    """, unsafe_allow_html=True)

    # Responsive layout - full width on mobile
    if st.session_state.get("is_mobile", False):
        col2 = st
    else:
        col1, col2, col3 = st.columns([1, 3, 1])

    with col2:
        st.markdown("<p class='login-subtitle'>Hello! Please Sign-In to Log Devices.</p>", unsafe_allow_html=True)
        st.write("")  # Add some space
        username = st.text_input("Employee ID")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            if not username or not password:
                st.error("Please enter both username and password")
                return

            # Check credentials
            hashed_pwd = hash_password(password)
            
            # Ensure username is treated as string to preserve leading zeros
            username_str = str(username).strip()
            
            # Debug: Show the input being processed
            st.info(f"Attempting login with ID: '{username_str}'")
            
            # Check if users dataframe is loaded correctly
            if 'users' not in st.session_state or st.session_state.users.empty:
                st.error("User database is not loaded correctly")
                initialize_data()  # Try to reinitialize data
                st.rerun()
                
            user_match = st.session_state.users[
                (st.session_state.users['username'] == username_str) & 
                (st.session_state.users['password'] == hashed_pwd)
            ]

            if not user_match.empty:
                st.success(f"Login successful!")
                st.session_state.authenticated = True
                st.session_state.current_user = username_str
                st.session_state.user_role = user_match.iloc[0]['role']
                st.rerun()
            else:
                # Debug info to help troubleshoot
                st.error("Invalid username or password")
                
                # Check if user exists but password doesn't match
                user_exists = username_str in st.session_state.users['username'].values
                if user_exists:
                    st.info(f"Note: User ID exists but password doesn't match. Please try again. The default admin password is '222222222'.")
                else:
                    st.info(f"Note: User ID '{username_str}' does not exist. Please check if you entered the correct Employee ID.")
                
                # Show admin credentials for convenience
                st.info("Admin login: ID '000001', Password '222222222'")
                    
                # Show all available usernames for debugging (remove in production)
                with st.expander("Available User IDs (for testing)"):
                    st.write(st.session_state.users[['username', 'role', 'first_name', 'last_name']])

def logout_user():
    """Handle user logout"""
    st.session_state.authenticated = False
    st.session_state.current_user = None
    st.session_state.user_role = None
    # Reset the logout_clicked flag
    if "logout_clicked" in st.session_state:
        del st.session_state.logout_clicked
    st.rerun()

# Handle component value for logout
if "logout_clicked" in st.session_state and st.session_state.logout_clicked:
    logout_user()

# Main app logic
if not st.session_state.authenticated:
    login_page()
else:
    # Hide sidebar
    st.markdown("""
    <style>
    [data-testid="stSidebar"] {
        display: none;
    }
    </style>
    """, unsafe_allow_html=True)

    # Display appropriate interface based on user role
    if st.session_state.user_role == 'athlete':
        athlete_device_checkout()
    elif st.session_state.user_role == 'coach' or st.session_state.user_role == 'specialist':
        admin_device_overview()

    # Create a container in the corner for the logout button
    logout_container = st.container()

    # Position the container with CSS
    st.markdown("""
    <style>
    [data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"]:last-child {
        position: fixed;
        bottom: 20px;
        right: 20px;
        z-index: 999;
    }

    /* Style the button */
    .stButton button {
        background-color: #f44336 !important;
        color: white !important;
        padding: 10px 20px !important;
        border: none !important;
        border-radius: 5px !important;
        font-weight: bold !important;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2) !important;
        transition: all 0.3s !important;
    }
    .stButton button:hover {
        background-color: #d32f2f !important;
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.3) !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # Add the logout button to the container
    with logout_container:
        if st.button("Logout"):
            logout_user()