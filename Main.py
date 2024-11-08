import streamlit as st
import pandas as pd
from datetime import datetime

# Load data only once into session state
if 'nhanvien_df' not in st.session_state:
    st.session_state['nhanvien_df'] = pd.read_excel('NhanVien.xlsx')

if 'kpitarget_df' not in st.session_state:
    st.session_state['kpitarget_df'] = pd.read_excel('KPItarget.xlsx')

if 'registration_df' not in st.session_state:
    try:
        st.session_state['registration_df'] = pd.read_excel('Registration.xlsx')
    except FileNotFoundError:
        st.session_state['registration_df'] = pd.DataFrame(columns=["maNVYT", "tenNhanVien", "Target", "TimeStamp"])

# Helper function to check login
def check_login(username, password):
    nhanvien_df = st.session_state['nhanvien_df']
    user = nhanvien_df[(nhanvien_df['taiKhoan'].astype(str) == str(username)) & 
                       (nhanvien_df['matKhau'].astype(str) == str(password))]
    return user if not user.empty else None

# Initialize user login status in session state
if 'is_logged_in' not in st.session_state:
    st.session_state['is_logged_in'] = False

# Initialize registration confirmation flag
if 'registration_confirmed' not in st.session_state:
    st.session_state['registration_confirmed'] = False

# Login section
if not st.session_state['is_logged_in']:
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    if st.button("Login"):
        user = check_login(username, password)
        if user is not None:
            # Set user details in session state and login status
            st.session_state['user_info'] = {
                "maNVYT": user.iloc[0]["maNVYT"],
                "tenNhanVien": user.iloc[0]["tenNhanVien"],
                "chucVu": user.iloc[0]["chucVu"]
            }
            st.session_state['is_logged_in'] = True
            st.success("Logged in successfully")
        else:
            st.error("Invalid username or password")

# Only display the main content if the user is logged in
if st.session_state['is_logged_in']:
    user_info = st.session_state['user_info']
    st.write(f"Welcome, {user_info['tenNhanVien']}")

    # Display registered targets for the current user
    registration_df = st.session_state['registration_df']
    user_registrations = registration_df[registration_df['maNVYT'] == user_info['maNVYT']]
    
    st.write("Your Registered Targets:")
    if not user_registrations.empty:
        st.write(user_registrations[['Target', 'TimeStamp']])
    else:
        st.write("You have not registered for any targets.")

    # Get a list of targets the user has already registered
    registered_targets = user_registrations['Target'].tolist()

    # Select and Register Target
    st.title("Choose Targets and Register")
    kpitarget_df = st.session_state['kpitarget_df']

    # Calculate remaining registration slots for each target
    target_slots = {}
    for _, row in kpitarget_df.iterrows():
        target = row['Target']
        max_reg = row['MaxReg']
        registered_count = registration_df[registration_df['Target'] == target].shape[0]
        remaining_slots = max_reg - registered_count
        target_slots[target] = remaining_slots

    # Show remaining slots and allow multiple selection, but disable registered targets
    available_targets = [
        f"{target} ({remaining_slots} left)" 
        for target, remaining_slots in target_slots.items() 
        if remaining_slots > 0 and target not in registered_targets
    ]
    
    targets_to_register = st.multiselect(
        "Select Targets (remaining slots shown in parentheses):",
        available_targets
    )

    # Extract the selected targets' names (without remaining slots info)
    selected_targets = [target.split(" (")[0] for target in targets_to_register]

    # Confirmation dialog before registration
    if selected_targets:
        confirmation = st.radio("Are you sure you want to register for the selected targets?", ("No", "Yes"))
        
        if confirmation == "Yes" and st.button("Confirm Registration"):
            # Create new registration entries
            new_registrations = []
            for target in selected_targets:
                new_registrations.append({
                    'maNVYT': user_info['maNVYT'],
                    'tenNhanVien': user_info['tenNhanVien'],
                    'Target': target,
                    'TimeStamp': datetime.now()
                })

            # Append new entries to the DataFrame
            registration_df = pd.concat([registration_df, pd.DataFrame(new_registrations)], ignore_index=True)
            st.session_state['registration_df'] = registration_df  # Update session state
            registration_df.to_excel('Registration.xlsx', index=False)
            st.session_state['registration_confirmed'] = True  # Set confirmation flag to refresh content

    # Refresh content after registration
