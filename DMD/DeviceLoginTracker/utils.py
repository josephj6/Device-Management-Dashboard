import streamlit as st
import pandas as pd
from datetime import datetime
import user_agents
import hashlib

def parse_user_agent(user_agent_string):
    """Parse user agent string to get device information"""
    if not user_agent_string or user_agent_string == "Unknown Device":
        return {
            'browser': 'Unknown',
            'os': 'Unknown',
            'device': 'Unknown Device'
        }
    user_agent = user_agents.parse(user_agent_string)
    return {
        'browser': user_agent.browser.family,
        'os': user_agent.os.family,
        'device': user_agent.device.family if user_agent.device.family != 'Other' else 'Desktop'
    }

def hash_password(password):
    """Create a hash of the password"""
    return hashlib.sha256(password.encode()).hexdigest()

def initialize_data():
    """Initialize DataFrames for users, devices, and logs with file persistence"""
    import os
    
    # Check if users.csv exists, otherwise create with default admin
    if 'users' not in st.session_state:
        if os.path.exists('users.csv'):
            try:
                # Read with explicit data types to preserve leading zeros
                st.session_state.users = pd.read_csv('users.csv', dtype={'username': str})
                
                # Convert NaN values to empty strings where necessary
                for col in ['first_name', 'last_name']:
                    if col in st.session_state.users.columns:
                        st.session_state.users[col] = st.session_state.users[col].fillna('')
                
                # Ensure admin exists
                if '000001' not in st.session_state.users['username'].values:
                    admin_data = pd.DataFrame({
                        'username': ['000001'],
                        'password': [hash_password('222222222')],
                        'role': ['coach'],
                        'first_name': ['Jelisha'],
                        'last_name': ['Joseph']
                    })
                    st.session_state.users = pd.concat([st.session_state.users, admin_data], ignore_index=True)
                    # Save updated users to file
                    st.session_state.users.to_csv('users.csv', index=False)
                    
            except Exception as e:
                st.error(f"Error loading users: {e}")
                # Create default admin if loading fails
                users_data = {
                    'username': ['000001'],
                    'password': [hash_password('222222222')],
                    'role': ['coach'],
                    'first_name': ['Jelisha'],
                    'last_name': ['Joseph']
                }
                st.session_state.users = pd.DataFrame(users_data)
                # Save to file
                st.session_state.users.to_csv('users.csv', index=False)
        else:
            # Create only the main admin account with updated credentials
            users_data = {
                'username': ['000001'],
                'password': [hash_password('222222222')],
                'role': ['coach'],
                'first_name': ['Jelisha'],
                'last_name': ['Joseph']
            }
            st.session_state.users = pd.DataFrame(users_data)
            # Save to file
            st.session_state.users.to_csv('users.csv', index=False)

    # Load or create device assignments with file persistence
    if 'device_assignments' not in st.session_state:
        if os.path.exists('device_assignments.csv'):
            try:
                assignments = pd.read_csv('device_assignments.csv')
                # Convert datetime columns
                for col in ['checkout_time', 'checkin_time']:
                    if col in assignments.columns:
                        assignments[col] = pd.to_datetime(assignments[col])
                st.session_state.device_assignments = assignments
            except Exception:
                # Create empty DataFrame if loading fails
                st.session_state.device_assignments = pd.DataFrame(columns=[
                    'device_id', 'employee_name', 'checkout_time', 'checkin_time', 'device_type'
                ])
                # Save empty dataframe to file
                st.session_state.device_assignments.to_csv('device_assignments.csv', index=False)
        else:
            st.session_state.device_assignments = pd.DataFrame(columns=[
                'device_id', 'employee_name', 'checkout_time', 'checkin_time', 'device_type'
            ])
            # Save empty dataframe to file
            st.session_state.device_assignments.to_csv('device_assignments.csv', index=False)

def get_device_type(device_id):
    """Determine device type based on ID range"""
    device_id = int(device_id) if isinstance(device_id, str) else device_id
    if 1 <= device_id <= 35:
        return "Athlete Device"
    elif 36 <= device_id <= 50:
        return "Payment Terminal"
    return "Unknown"

def validate_user(username, password):
    """Validate user credentials and return role"""
    user_data = st.session_state.users
    # Ensure username is treated as string
    username = str(username)
    user = user_data[user_data['username'] == username]
    if not user.empty:
        if user.iloc[0]['password'] == hash_password(password):
            return True, user.iloc[0]['role']
    return False, None

def assign_device(username, device_id):
    """Assign a device to a user"""
    # Check if device is already assigned
    existing_assignment = st.session_state.device_assignments[
        (st.session_state.device_assignments['device_id'] == device_id) & 
        (st.session_state.device_assignments['checkin_time'].isna())
    ]

    if not existing_assignment.empty:
        return False, "Device is already checked out by another athlete"

    # Check if user already has a device of this type
    device_type = get_device_type(device_id)
    user_active_assignments = st.session_state.device_assignments[
        (st.session_state.device_assignments['employee_name'] == username) & 
        (st.session_state.device_assignments['checkin_time'].isna()) &
        (st.session_state.device_assignments['device_type'] == device_type)
    ]

    if not user_active_assignments.empty:
        return False, f"You already have a {device_type} checked out"

    # Create new assignment
    new_assignment = pd.DataFrame([{
        'device_id': device_id,
        'employee_name': username,
        'checkout_time': datetime.now(),
        'checkin_time': None,
        'device_type': get_device_type(device_id)
    }])

    st.session_state.device_assignments = pd.concat(
        [st.session_state.device_assignments, new_assignment],
        ignore_index=True
    )
    return True, f"Successfully checked out {device_type} #{device_id}"

def return_device(device_id):
    """Return a device"""
    # Find active assignment
    mask = (
        (st.session_state.device_assignments['device_id'] == device_id) & 
        (st.session_state.device_assignments['checkin_time'].isna())
    )

    if not mask.any():
        return False

    # Update checkin time
    st.session_state.device_assignments.loc[mask, 'checkin_time'] = datetime.now()
    return True

def get_active_assignments():
    """Get currently active device assignments"""
    return st.session_state.device_assignments[
        st.session_state.device_assignments['checkin_time'].isna()
    ]

def get_device_history():
    """Get complete device assignment history"""
    return st.session_state.device_assignments.sort_values(
        by=['checkout_time'], 
        ascending=False
    )