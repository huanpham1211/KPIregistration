import streamlit as st
import pandas as pd
from datetime import datetime
import io
import json
import pytz
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Google Sheets document IDs and ranges
KPI_SHEET_ID = '1f38fTxOkuP2PFKDSyrxp1aRXi8iz9rZqMJesDkJjC14'  # ID for KPITarget Google Sheet
KPI_SHEET_RANGE = 'Sheet1'  # Replace with your sheet name

REGISTRATION_SHEET_ID = '1Cq6J5gOqErerq4M4JqkwiE5aOC-bg1s6uqPB41_DzXs'  # ID for Registration Google Sheet
REGISTRATION_SHEET_RANGE = 'Sheet1'  # Replace with the correct sheet name if different

# Load Google credentials from Streamlit Secrets
google_credentials = st.secrets["GOOGLE_CREDENTIALS"]
credentials_info = json.loads(google_credentials)

# Authenticate using the service account credentials
credentials = service_account.Credentials.from_service_account_info(
    credentials_info,
    scopes=["https://www.googleapis.com/auth/spreadsheets"]
)

# Initialize the Google Sheets API client
sheets_service = build('sheets', 'v4', credentials=credentials)

# Function to fetch data from a Google Sheet
def fetch_sheet_data(sheet_id, range_name):
    result = sheets_service.spreadsheets().values().get(
        spreadsheetId=sheet_id,
        range=range_name
    ).execute()
    values = result.get('values', [])
    
    # Convert to DataFrame
    if not values:
        st.error("No data found.")
        return pd.DataFrame()
    else:
        headers = values[0]  # First row as headers
        data = values[1:]  # Data starts from the second row
        return pd.DataFrame(data, columns=headers)

# Function to append data to a Google Sheet
def append_to_sheet(sheet_id, range_name, values):
    body = {
        'values': values
    }
    sheets_service.spreadsheets().values().append(
        spreadsheetId=sheet_id,
        range=range_name,
        valueInputOption="USER_ENTERED",
        insertDataOption="INSERT_ROWS",
        body=body
    ).execute()

# Load Google Sheets data into Streamlit session state
if 'nhanvien_df' not in st.session_state:
    st.session_state['nhanvien_df'] = pd.read_excel('NhanVien.xlsx')

if 'kpitarget_df' not in st.session_state:
    # Load from Google Sheets instead of local file
    st.session_state['kpitarget_df'] = fetch_sheet_data(KPI_SHEET_ID, KPI_SHEET_RANGE)

if 'registration_df' not in st.session_state:
    # Load registration data from Google Sheets
    st.session_state['registration_df'] = fetch_sheet_data(REGISTRATION_SHEET_ID, REGISTRATION_SHEET_RANGE)

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
            # Get Vietnam timezone-aware timestamp
            vietnam_tz = pytz.timezone("Asia/Ho_Chi_Minh")
            timestamp = datetime.now(vietnam_tz).strftime("%Y-%m-%d %H:%M:%S")

            # Prepare new registration entries
            new_registrations = [
                [user_info['maNVYT'], user_info['tenNhanVien'], target, timestamp]
                for target in selected_targets
            ]

            # Append to Google Sheets
            try:
                append_to_sheet(REGISTRATION_SHEET_ID, REGISTRATION_SHEET_RANGE, new_registrations)
                
                # Update session state registration DataFrame
                st.session_state['registration_df'] = fetch_sheet_data(REGISTRATION_SHEET_ID, REGISTRATION_SHEET_RANGE)
                st.success("Đăng ký thành công!")
            except Exception as e:
                st.error(f"Lỗi khi ghi dữ liệu vào Google Sheets: {e}")
