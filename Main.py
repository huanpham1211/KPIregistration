import streamlit as st
import pandas as pd
from datetime import datetime
import json
import pytz
from google.oauth2 import service_account
from googleapiclient.discovery import build
import time

# Google Sheets document IDs and ranges
KPI_SHEET_ID = '1f38fTxOkuP2PFKDSyrxp1aRXi8iz9rZqMJesDkJjC14'
KPI_SHEET_RANGE = 'Sheet1'

REGISTRATION_SHEET_ID = '1Cq6J5gOqErerq4M4JqkwiE5aOC-bg1s6uqPB41_DzXs'
REGISTRATION_SHEET_RANGE = 'Sheet1'

NHANVIEN_SHEET_ID = '1kzfwjA0nVLFoW8T5jroLyR2lmtdZp8eaYH-_Pyb0nbk'
NHANVIEN_SHEET_RANGE = 'Sheet1'

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
st.set_page_config(layout="wide")
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
        headers = values[0]
        data = values[1:]
        return pd.DataFrame(data, columns=headers)

# Function to append data to a Google Sheet
def append_to_sheet(sheet_id, range_name, values):
    body = {'values': values}
    sheets_service.spreadsheets().values().append(
        spreadsheetId=sheet_id,
        range=range_name,
        valueInputOption="USER_ENTERED",
        insertDataOption="INSERT_ROWS",
        body=body
    ).execute()

# Load Google Sheets data into Streamlit session state
if 'nhanvien_df' not in st.session_state:
    st.session_state['nhanvien_df'] = fetch_sheet_data(NHANVIEN_SHEET_ID, NHANVIEN_SHEET_RANGE)

if 'kpitarget_df' not in st.session_state:
    st.session_state['kpitarget_df'] = fetch_sheet_data(KPI_SHEET_ID, KPI_SHEET_RANGE)

if 'registration_df' not in st.session_state:
    st.session_state['registration_df'] = fetch_sheet_data(REGISTRATION_SHEET_ID, REGISTRATION_SHEET_RANGE)

# Helper function to check login
def check_login(username, password):
    nhanvien_df = st.session_state['nhanvien_df']
    user = nhanvien_df[(nhanvien_df['taiKhoan'].astype(str) == str(username)) & 
                       (nhanvien_df['matKhau'].astype(str) == str(password))]
    return user if not user.empty else None

# Function to display the user's registered targets
import streamlit as st

def display_user_registrations():
    # Fetch the latest registration data
    st.session_state['registration_df'] = fetch_sheet_data(REGISTRATION_SHEET_ID, REGISTRATION_SHEET_RANGE)
    registration_df = st.session_state['registration_df']

    # Convert maNVYT to string format for consistency
    registration_df['maNVYT'] = registration_df['maNVYT'].astype(str)
    user_nvyt = str(st.session_state['user_info']['maNVYT'])

    # Filter user's registrations based on maNVYT
    user_registrations = registration_df[registration_df['maNVYT'] == user_nvyt]

    st.write("### Chỉ tiêu đã đăng ký:")

    if not user_registrations.empty:
        # Rename columns for better readability
        user_registrations = user_registrations.rename(columns={'Target': 'Chỉ tiêu', 'TimeStamp': 'Thời gian đăng ký'})

        # Apply CSS for wrapping text in the table
        st.markdown("""
            <style>
                .stDataFrame { width: 100% !important; } /* Makes table wider */
                .dataframe th { text-align: center !important; font-size: 16px !important; }
                .dataframe td { word-wrap: break-word !important; white-space: normal !important; font-size: 14px !important; }
            </style>
        """, unsafe_allow_html=True)

        # Display the dataframe
        st.dataframe(
            user_registrations[['Chỉ tiêu', 'Thời gian đăng ký']],
            width=1200,  # Adjusted for wider table
            hide_index=True  # Hides the default index column
        )
    else:
        st.info("Bạn chưa đăng ký chỉ tiêu nào!")





# Function to display the registration form
def display_registration_form():
    user_info = st.session_state['user_info']
    kpitarget_df = st.session_state['kpitarget_df']
    registration_df = st.session_state['registration_df']
    nhanvien_df = st.session_state['nhanvien_df']

    # Normalize column names (strip spaces)
    kpitarget_df.columns = kpitarget_df.columns.str.strip()
    nhanvien_df.columns = nhanvien_df.columns.str.strip()

    # Ensure necessary columns exist
    required_columns = {'MucDo', 'ViTriViecLam', 'BoPhan', 'Target', 'MaxReg'}
    missing_columns = required_columns - set(kpitarget_df.columns)
    if missing_columns:
        st.error(f"Các cột bị thiếu trong KPI Target: {', '.join(missing_columns)}")
        return

    # Ensure nhanvien_df contains 'nhom' and 'BoPhan'
    if 'nhom' not in nhanvien_df.columns or 'BoPhan' not in nhanvien_df.columns:
        st.error("Thiếu cột 'nhom' hoặc 'BoPhan' trong danh sách nhân viên.")
        return

    # Get user's nhom and BoPhan from nhanvien_df
    user_record = nhanvien_df[nhanvien_df['maNVYT'] == user_info['maNVYT']]
    
    if user_record.empty:
        st.error("Không tìm thấy thông tin nhân viên.")
        return

    user_nhom = user_record['nhom'].values[0]
    user_bophan = user_record['BoPhan'].values[0]

    # Define sorted order for MucDo
    muc_do_order = ["Thường quy", "Trung bình", "Khó", "Rất khó"]

    # Define selection permissions based on nhom
    nhom_permissions = {
        "BCN": ["BCN", "QLKT", "QLCL", "NQL", "NV"],  # Can select all
        "QLKT": ["QLKT", "NQL", "NV"],  # Can select QLKT, NQL, NV
        "QLCL": ["QLCL", "NQL", "NV"],  # Can select QLCL, NQL, NV
        "NQL": ["NQL", "NV"],  # Can select NQL, NV
        "NV": ["NV"],  # Can only select NV
    }

    # Get valid positions based on nhom
    allowed_positions = nhom_permissions.get(user_nhom, [])

    # Calculate remaining registration slots for each target
    target_slots = {}

    for _, row in kpitarget_df.iterrows():
        target = row['Target']
        muc_do = row['MucDo']
        vi_tri = row['ViTriViecLam']
        bo_phan_target = row['BoPhan']  # This may contain multiple values like "SH,TSSS,HIV"
        max_reg = int(row['MaxReg'])
        registered_count = registration_df[registration_df['Target'] == target].shape[0]
        remaining_slots = max_reg - registered_count

        # Check if the user is eligible for the target
        can_select = False

        if user_bophan == "All":
            can_select = True  # "All" users can select any target
        else:
            # Handle multiple values in BoPhan
            target_departments = [bp.strip() for bp in str(bo_phan_target).split(",")]

            # 1️⃣ If ViTriViecLam is set but BoPhan is empty → Compare only ViTriViecLam
            if vi_tri and not bo_phan_target:
                if vi_tri in allowed_positions:
                    can_select = True

            # 2️⃣ If BoPhan is set but ViTriViecLam is empty → Compare only BoPhan
            elif bo_phan_target and not vi_tri:
                if user_bophan in target_departments:
                    can_select = True

            # 3️⃣ If both are set → Both must match
            elif vi_tri and bo_phan_target:
                if vi_tri in allowed_positions and user_bophan in target_departments:
                    can_select = True

        if can_select:
            if muc_do not in target_slots:
                target_slots[muc_do] = {}
            target_slots[muc_do][target] = remaining_slots

    # Determine already registered targets by the user
    registered_targets = registration_df[registration_df['maNVYT'] == str(user_info['maNVYT'])]['Target'].tolist()

    # Display available targets grouped by sorted MucDo
    st.write("### Chọn chỉ tiêu (Số vị trí còn lại):")
    selected_targets = []

    for muc_do in muc_do_order:
        if muc_do in target_slots:  # Only display existing categories
            st.subheader(f"Mức độ: {muc_do}")
    
            for target, remaining_slots in target_slots[muc_do].items():
                if remaining_slots > 0 and target not in registered_targets:
                    # Create two columns: One for text, one for checkbox
                    col1, col2 = st.columns([0.8, 0.2])  # Adjust ratio as needed
    
                    with col1:
                        st.markdown(f"**{target}** <span style='color: orange;'>({remaining_slots} vị trí trống còn lại)</span>", unsafe_allow_html=True)
    
                    with col2:
                        is_selected = st.checkbox("", key=f"target_{target}")  # Empty label for checkbox
    
                    if is_selected:
                        selected_targets.append(target)



    # Enforce a maximum of 2 registrations
    if len(registered_targets) + len(selected_targets) > 2:
        st.error("Bạn chỉ có thể đăng ký tối đa 2 chỉ tiêu.")
        return

    # Confirmation dialog before registration
    if selected_targets:
        confirmation = st.radio("Bạn có muốn đăng ký chỉ tiêu đã chọn (Lưu ý không thể hủy chỉ tiêu đã đăng ký)?", ("Không", "Có"))
    
        if confirmation == "Có" and st.button("Xác nhận đăng ký"):
            # Get Vietnam timezone-aware timestamp
            vietnam_tz = pytz.timezone("Asia/Ho_Chi_Minh")
            timestamp = datetime.now(vietnam_tz).strftime("%Y-%m-%d %H:%M:%S")
    
            # Convert maNVYT to a string to preserve leading zeros
            maNVYT_str = str(user_info['maNVYT'])
    
            # Prepare new registration entries
            new_registrations = [
                [
                    f"'{maNVYT_str}",  # Ensures Google Sheets treats it as text
                    user_info['tenNhanVien'],
                    target,
                    timestamp
                ]
                for target in selected_targets
            ]
    
            # Append to Google Sheets
            try:
                append_to_sheet(REGISTRATION_SHEET_ID, REGISTRATION_SHEET_RANGE, new_registrations)
                st.success("Đăng ký thành công!")
                st.session_state['page'] = "CHỈ TIÊU KPI ĐÃ ĐĂNG KÝ"
            except Exception as e:
                st.error(f"Lỗi khi ghi dữ liệu: {e}")





# Check for login and show the login section if the user is not logged in
if not st.session_state.get('is_logged_in', False):
    st.title("Đăng ký KPI - Khoa Xét nghiệm")
    username = st.text_input("Tài khoản", placeholder="e.g., 01234.bvhv")
    password = st.text_input("Mật khẩu", type="password")
    
    login_button = st.button("Login")
    if login_button:
        # Display loading message and check credentials
        with st.spinner("Logging in, please wait..."):
            time.sleep(1)  # Simulate loading time
            user = check_login(username, password)
            if user is not None:
                st.session_state['user_info'] = {
                    "maNVYT": user.iloc[0]["maNVYT"],
                    "tenNhanVien": user.iloc[0]["tenNhanVien"],
                    "chucVu": user.iloc[0]["chucVu"]
                }
                st.session_state['is_logged_in'] = True
                st.session_state['show_sidebar'] = True
                st.sidebar.success("Đăng nhập thành công")  # Show successful login in sidebar
                st.rerun()
            else:
                st.error("Sai tên tài khoản hoặc mật khẩu")
else:
    # Display sidebar after login
    if st.session_state.get('show_sidebar', False):
        # Sidebar navigation
        page = st.sidebar.radio("", ["CHỈ TIÊU KPI ĐÃ ĐĂNG KÝ", "ĐĂNG KÝ MỚI"])
        # Logout button
        if st.sidebar.button("Đăng xuất"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]  # Clear all session state keys
            st.sidebar.write("Bạn đã đăng xuất. Làm mới trang để đăng nhập lại.")
            st.stop()  # Stop the app to ensure the session is cleared
            st.rerun()
        # Display content based on selected tab
        if page == "CHỈ TIÊU KPI ĐÃ ĐĂNG KÝ":
            st.title("CHỈ TIÊU KPI ĐÃ ĐĂNG KÝ")
            display_user_registrations()
        elif page == "ĐĂNG KÝ MỚI":
            st.title("ĐĂNG KÝ MỚI")
            display_registration_form()

# Footer at the sidebar with developer information
st.sidebar.markdown("---")
st.sidebar.markdown("<div style='text-align: center; font-size: small;'>Developed by HuanPham</div>", unsafe_allow_html=True)
