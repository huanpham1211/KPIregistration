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

# User session
if 'user' not in st.session_state:
    st.session_state['user'] = None

# Login section
if st.session_state['user'] is None:
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        user = check_login(username, password)
        if user is not None:
            # Store only essential information in session state
            st.session_state['user'] = {
                "maNVYT": user.iloc[0]["maNVYT"],
                "tenNhanVien": user.iloc[0]["tenNhanVien"],
                "chucVu": user.iloc[0]["chucVu"]
            }
            st.success("Logged in successfully")
            st.experimental_rerun()  # Force a rerun to display logged-in content
        else:
            st.error("Invalid username or password")
else:
    user_info = st.session_state['user']
    st.write(f"Welcome, {user_info['tenNhanVien']}")

    # Display registered targets for the current user
    registration_df = st.session_state['registration_df']
    user_registrations = registration_df[registration_df['maNVYT'] == user_info['maNVYT']]
    if not user_registrations.empty:
        st.write("Your Registered Targets:")
        st.write(user_registrations[['Target', 'TimeStamp']])
    else:
        st.write("You have not registered for any targets.")

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

    # Show remaining slots and allow multiple selection
    targets_to_register = st.multiselect(
        "Select Targets (remaining slots shown in parentheses):",
        [f"{target} ({remaining_slots} left)" for target, remaining_slots in target_slots.items() if remaining_slots > 0]
    )

    # Extract the selected targets' names (without remaining slots info)
    selected_targets = [target.split(" (")[0] for target in targets_to_register]

    # Register button with confirmation
    if st.button("Register") and selected_targets:
        confirm = st.warning("Are you sure you want to register for these targets?", icon="⚠️")
        if st.button("Yes, Register"):
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
            st.success("Registration successful!")
        else:
            st.warning("Registration canceled.")

    # Admin view
    if user_info['chucVu'] == 'admin':
        st.title("Admin: Registration List")
        st.write(registration_df)
        st.download_button(
            label="Download Registration List",
            data=registration_df.to_csv(index=False),
            file_name='Registration.csv'
        )
