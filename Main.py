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
        else:
            st.error("Invalid username or password")
else:
    user_info = st.session_state['user']
    st.write(f"Welcome, {user_info['tenNhanVien']}")

    # Select and Register Target
    st.title("Choose a Target and Register")
    kpitarget_df = st.session_state['kpitarget_df']
    target = st.selectbox("Select a Target", kpitarget_df['Target'].tolist())
    max_reg = kpitarget_df[kpitarget_df['Target'] == target]['MaxReg'].values[0]

    if st.button("Register"):
        # Load registration DataFrame from session state
        registration_df = st.session_state['registration_df']

        # Check current registration count
        target_count = registration_df[registration_df['Target'] == target].shape[0]
        
        if target_count < max_reg:
            # Register user
            new_registration = {
                'maNVYT': user_info['maNVYT'],
                'tenNhanVien': user_info['tenNhanVien'],
                'Target': target,
                'TimeStamp': datetime.now()
            }
            registration_df = registration_df.append(new_registration, ignore_index=True)
            st.session_state['registration_df'] = registration_df  # Update session state
            registration_df.to_excel('Registration.xlsx', index=False)
            st.success("Registration successful!")
        else:
            st.warning("Registration limit reached for this target.")

    # Admin view
    if user_info['chucVu'] == 'admin':
        st.title("Admin: Registration List")
        registration_df = st.session_state['registration_df']
        st.write(registration_df)
        st.download_button(
            label="Download Registration List",
            data=registration_df.to_csv(index=False),
            file_name='Registration.csv'
        )
