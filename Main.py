import streamlit as st
import pandas as pd
from datetime import datetime

# Load data
nhanvien_df = pd.read_excel('NhanVien.xlsx')
kpitarget_df = pd.read_excel('KPItarget.xlsx')
registration_file = 'Registration.xlsx'

# Helper function to check login
def check_login(username, password):
    print("Entered Username:", username)
    print("Entered Password:", password)
    user = nhanvien_df[(nhanvien_df['taiKhoan'] == username) & (nhanvien_df['matKhau'] == password)]
    return user if not user.empty else None


# User session
if 'user' not in st.session_state:
    st.session_state['user'] = None

# Login section
if not st.session_state['user']:
    st.title("Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        user = check_login(username, password)
        if user is not None:
            st.session_state['user'] = user
            st.success("Logged in successfully")
        else:
            st.error("Invalid username or password")
else:
    user_info = st.session_state['user'].iloc[0]
    st.write(f"Welcome, {user_info['tenNhanVien']}")

    # Select and Register Target
    st.title("Choose a Target and Register")
    target = st.selectbox("Select a Target", kpitarget_df['Target'].tolist())
    max_reg = kpitarget_df[kpitarget_df['Target'] == target]['MaxReg'].values[0]
    if st.button("Register"):
        # Check current registration count
        if registration_file in st.session_state:
            registration_df = st.session_state[registration_file]
        else:
            registration_df = pd.read_excel(registration_file) if registration_file else pd.DataFrame()

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
            registration_df.to_excel(registration_file, index=False)
            st.success("Registration successful!")
        else:
            st.warning("Registration limit reached for this target.")

    # Admin view
    if user_info['chucVu'] == 'admin':
        st.title("Admin: Registration List")
        st.write(registration_df)
        st.download_button(
            label="Download Registration List",
            data=registration_df.to_csv(index=False),
            file_name='Registration.csv'
        )
