import streamlit as st
import pandas as pd
from datetime import datetime
import io
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Google Sheets document ID (from your shared link)
SHEET_ID = '1f38fTxOkuP2PFKDSyrxp1aRXi8iz9rZqMJesDkJjC14'  # New spreadsheet ID
SHEET_RANGE = 'Sheet1'  # Replace with your sheet name if it's different

# Function to fetch data from Google Sheets
def fetch_sheet_data(sheet_id, range_name):
    result = sheets_service.spreadsheets().values().get(
        spreadsheetId=sheet_id,
        range=range_name
    ).execute()
    values = result.get('values', [])
    
    # Convert to DataFrame
    if not values:
        st.error("No data found.")
        return pd.DataFrame()  # Return empty DataFrame if no data
    else:
        # Convert list of lists to DataFrame
        headers = values[0]  # Use the first row as headers
        data = values[1:]  # Data starts from the second row
        return pd.DataFrame(data, columns=headers)

# Use the fetch function to load data into the app
kpitarget_df = fetch_sheet_data(SHEET_ID, SHEET_RANGE)
st.write(kpitarget_df)  # Display the data in the app
SHEET_RANGE = 'Sheet1'  # Replace with your sheet name if it's different

# Function to fetch data from Google Sheets
def fetch_sheet_data(sheet_id, range_name):
    result = sheets_service.spreadsheets().values().get(
        spreadsheetId=sheet_id,
        range=range_name
    ).execute()
    values = result.get('values', [])
    
    # Convert to DataFrame
    if not values:
        st.error("No data found.")
        return pd.DataFrame()  # Return empty DataFrame if no data
    else:
        # Convert list of lists to DataFrame
        headers = values[0]  # Use the first row as headers
        data = values[1:]  # Data starts from the second row
        return pd.DataFrame(data, columns=headers)

# Use the fetch function to load data into the app
kpitarget_df = fetch_sheet_data(SHEET_ID, SHEET_RANGE)
st.write(kpitarget_df)  # Display the data in the app

# Google Sheets range to read from (e.g., "Sheet1!A1:D")
SHEET_RANGE = 'Sheet1'  # Change this if your sheet name is different

# Load Google credentials from Streamlit Secrets
google_credentials = st.secrets["GOOGLE_CREDENTIALS"]
credentials_info = json.loads(google_credentials)

# Authenticate using the service account credentials
credentials = service_account.Credentials.from_service_account_info(
    credentials_info,
    scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
)

# Initialize the Google Sheets API client
sheets_service = build('sheets', 'v4', credentials=credentials)

# Function to fetch data from Google Sheets
def fetch_sheet_data(sheet_id, range_name):
    result = sheets_service.spreadsheets().values().get(
        spreadsheetId=sheet_id,
        range=range_name
    ).execute()
    values = result.get('values', [])
    
    # Convert to DataFrame
    if not values:
        st.error("No data found.")
        return pd.DataFrame()  # Return empty DataFrame if no data
    else:
        # Convert list of lists to DataFrame
        headers = values[0]  # Use the first row as headers
        data = values[1:]  # Data starts from the second row
        return pd.DataFrame(data, columns=headers)

# Load Google Sheets data into Streamlit session state
if 'nhanvien_df' not in st.session_state:
    st.session_state['nhanvien_df'] = pd.read_excel('NhanVien.xlsx')

if 'kpitarget_df' not in st.session_state:
    # Load from Google Sheets instead of local file
    st.session_state['kpitarget_df'] = fetch_sheet_data(SHEET_ID, SHEET_RANGE)

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

# Show the login section only if the user is not logged in
if not st.session_state['is_logged_in']:
    st.title("Đăng nhập")
    username = st.text_input("Tài khoản")
    password = st.text_input("Mật khẩu", type="password")
    
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
            st.success("Đăng nhập thành công")
        else:
            st.error("Sai tên tài khoản hoặc mật khẩu")

# Only display the main content if the user is logged in
if st.session_state['is_logged_in']:
    user_info = st.session_state['user_info']
    st.write(f"Welcome, {user_info['tenNhanVien']}")

    # Display registered targets for the current user
    registration_df = st.session_state['registration_df']
    user_registrations = registration_df[registration_df['maNVYT'] == user_info['maNVYT']]
    
    st.write("Chỉ tiêu đã đăng ký:")
    if not user_registrations.empty:
        st.write(user_registrations[['Target', 'TimeStamp']])
    else:
        st.write("Bạn chưa đăng ký chỉ tiêu nào!")

    # Get a list of targets the user has already registered
    registered_targets = user_registrations['Target'].tolist()

    # Select and Register Target
    st.title("Chọn chỉ tiêu và đăng ký")
    kpitarget_df = st.session_state['kpitarget_df']

    # Calculate remaining registration slots for each target
    target_slots = {}
    for _, row in kpitarget_df.iterrows():
        target = row['Target']
        max_reg = int(row['MaxReg'])
        registered_count = registration_df[registration_df['Target'] == target].shape[0]
        remaining_slots = max_reg - registered_count
        target_slots[target] = remaining_slots

    # Show remaining slots and allow multiple selection, but disable registered targets
    available_targets = [
        f"{target} ({remaining_slots} vị trí trống còn lại)" 
        for target, remaining_slots in target_slots.items() 
        if remaining_slots > 0 and target not in registered_targets
    ]
    
    targets_to_register = st.multiselect(
        "Chọn chỉ tiêu (Số vị trí còn lại):",
        available_targets
    )

    # Extract the selected targets' names (without remaining slots info)
    selected_targets = [target.split(" (")[0] for target in targets_to_register]

    # Confirmation dialog before registration
    if selected_targets:
        confirmation = st.radio("Bạn có muốn đăng ký chỉ tiêu đã chọn?", ("Không", "Có"))
        
        if confirmation == "Có" and st.button("Xác nhận đăng ký"):
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
    if st.session_state['registration_confirmed']:
        st.session_state['registration_confirmed'] = False  # Reset confirmation flag

    # Admin view
    if user_info['chucVu'] == 'admin':
        st.title("Admin: Danh sách chỉ tiêu đăng ký")
        st.write(registration_df)
          
        # Create a BytesIO object to store the Excel file in memory
        excel_data = io.BytesIO()
        registration_df.to_excel(excel_data, index=False, engine='openpyxl')
        excel_data.seek(0)  # Rewind the buffer

        # Use st.download_button to allow downloading the Excel file
        st.download_button(
            label="Download Registration List",
            data=excel_data,
            file_name='Registration.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
