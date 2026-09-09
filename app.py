from datetime import date, datetime
import io
import time
from fpdf import FPDF
import pandas as pd
import streamlit as st
from streamlit_gsheets import GSheetsConnection

# --- Page Configuration & Executive Styling ---
st.set_page_config(
    page_title="Zelqon Foods | HR & Payroll", page_icon="🏢", layout="wide"
)

# Targeted, Safe Corporate Styling
st.markdown("""
    <style>
        #MainMenu {visibility: hidden !important;}
        footer {visibility: hidden !important;}
        header {visibility: hidden !important;}
        [data-testid="stToolbar"] {display: none !important;}
        [data-testid="stAppDeployButton"] {display: none !important;}
        [data-testid="stViewerBadge"] {display: none !important;}
        [data-testid="stElementToolbar"] {display: none !important;}

        .zelqon-hero-card {
            background: linear-gradient(135deg, #0F172A 0%, #1E3A8A 100%);
            padding: 1.75rem 2rem;
            border-radius: 12px;
            color: #FFFFFF;
            margin-bottom: 1.5rem;
            box-shadow: 0 4px 14px 0 rgba(15, 23, 42, 0.15);
        }
        .zelqon-badge {
            display: inline-block;
            background-color: rgba(255, 255, 255, 0.15);
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 0.75rem;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            font-weight: 600;
            color: #93C5FD;
            margin-bottom: 0.5rem;
        }
        .zelqon-hero-title {
            font-size: 1.85rem;
            font-weight: 700;
            margin: 0;
            color: #FFFFFF;
            letter-spacing: -0.02em;
        }
        .zelqon-hero-subtitle {
            font-size: 0.9rem;
            color: #CBD5E1;
            margin-top: 4px;
            margin-bottom: 0;
        }
    </style>
""", unsafe_allow_html=True)


# --- User Authentication System ---
USER_CREDENTIALS = {
    "admin": {
        "password": st.secrets.get("credentials", {}).get("admin", {}).get("password", "zelqon2026"),
        "role": "Admin",
        "name": "Zelqon Management",
    },
    "kitchen": {
        "password": st.secrets.get("credentials", {}).get("kitchen", {}).get("password", "food123"),
        "role": "Staff",
        "name": "Fuvahmulah Kitchen Crew",
    },
}

if "auth_status" not in st.session_state:
  st.session_state.auth_status = False
  st.session_state.current_user = None
  st.session_state.current_role = None
  st.session_state.current_name = None

def verify_login(username, password):
  user_entry = USER_CREDENTIALS.get(username.strip().lower())
  if user_entry and user_entry["password"] == password:
    return True, user_entry["role"], user_entry["name"]
  return False, None, None

# --- Login Gate ---
if not st.session_state.auth_status:
  st.write("")
  st.write("")
  col_pad_left, col_login, col_pad_right = st.columns([1, 1.2, 1])
  with col_login:
    with st.container(border=True):
      st.markdown(
          "<div style='text-align: center; margin-bottom: 1rem;'>"
          "<span style='font-size: 0.8rem; font-weight: 700; letter-spacing: 0.1em; color: #2563EB;'>ZELQON FOODS</span>"
          "<h2 style='margin: 0.2rem 0; font-weight: 700;'>Operations Access</h2>"
          "<p style='font-size: 0.85rem; color: #64748B;'>Fuvahmulah City, Republic of Maldives</p>"
          "</div>",
          unsafe_allow_html=True,
      )
      st.divider()
      with st.form("zelqon_login_form"):
        login_user = st.text_input("Username", placeholder="e.g. admin or kitchen")
        login_pass = st.text_input("Password", type="password", placeholder="Enter authorization key")
        st.write("")
        submit_login = st.form_submit_button("Authorize Session", type="primary", use_container_width=True)
        if submit_login:
          success, role, name = verify_login(login_user, login_pass)
          if success:
            st.session_state.auth_status = True
            st.session_state.current_user = login_user.strip().lower()
            st.session_state.current_role = role
            st.session_state.current_name = name
            st.rerun()
          else:
            st.error("Authentication failed: Check credentials.")
  st.stop()


# =========================================================
# CLOUD DATABASE CONNECTORS (ENTERPRISE RETRY LOGIC)
# =========================================================
conn = st.connection("gsheets", type=GSheetsConnection)

def robust_read(worksheet_name, retries=3):
    """Intercepts network drops and safely retries the Google Sheets connection."""
    for attempt in range(retries):
        try:
            return conn.read(worksheet=worksheet_name, ttl=0)
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2) # Pause for 2 seconds before retrying
            else:
                raise e

def robust_update(worksheet_name, data, retries=3):
    """Safely commits data to Google Sheets with automatic retry."""
    for attempt in range(retries):
        try:
            conn.update(worksheet=worksheet_name, data=data)
            return
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2)
            else:
                st.error(f"Network Timeout: Failed to sync with Google Sheets after {retries} attempts. Please check your connection.")
                raise e

@st.cache_data(ttl=600)
def load_staff_data():
  try:
    df = robust_read("Staff")
    expected_cols = {"Staff ID": "ZF-001", "Name": "", "Role": "Semi-Cooked Processing", "Base Salary (MVR)": 4500.0, "Standard Monthly Days": 30, "Bank Account": "", "Pension Enrolled": "No"}
    if df is None or df.empty:
      return pd.DataFrame(columns=list(expected_cols.keys()))
    for col, default_val in expected_cols.items():
      if col not in df.columns: df[col] = default_val
    return df.dropna(subset=["Staff ID", "Name"])
  except Exception:
    return pd.DataFrame(columns=["Staff ID", "Name", "Role", "Base Salary (MVR)", "Standard Monthly Days", "Bank Account", "Pension Enrolled"])

@st.cache_data(ttl=600)
def load_attendance_data():
  try:
    df = robust_read("Attendance")
    expected_cols = {"Date": str(date.today()), "Staff ID": "ZF-001", "Name": "", "Station": "Semi-Cooked Processing", "Status": "Present", "Overtime Hours": 0.0, "Notes": ""}
    if df is None or df.empty:
      return pd.DataFrame(columns=list(expected_cols.keys()))
    for col, default_val in expected_cols.items():
      if col not in df.columns: df[col] = default_val
    return df.dropna(subset=["Date", "Name"])
  except Exception:
    return pd.DataFrame(columns=["Date", "Staff ID", "Name", "Station", "Status", "Overtime Hours", "Notes"])

@st.cache_data(ttl=600)
def load_advances_data():
  try:
    df = robust_read("Advances")
    expected_cols = {"Staff ID": "ZF-001", "Name": "", "Total Loan (MVR)": 0.0, "Monthly Installment (MVR)": 0.0, "Remaining Balance (MVR)": 0.0}
    if df is None or df.empty:
      return pd.DataFrame(columns=list(expected_cols.keys()))
    for col, default_val in expected_cols.items():
      if col not in df.columns: df[col] = default_val
    return df.dropna(subset=["Staff ID", "Name"])
  except Exception:
    return pd.DataFrame(columns=["Staff ID", "Name", "Total Loan (MVR)", "Monthly Installment (MVR)", "Remaining Balance (MVR)"])


# --- Payslip PDF Engine ---
class PayslipPDF(FPDF):
  def header(self):
    self.set_font("Helvetica", "B", 15)
    self.cell(0, 7, "ZELQON FOODS", align="C", new_x="LMARGIN", new_y="NEXT")
    self.set_font("Helvetica", "", 8)
    self.cell(0, 4, "Fuvahmulah City, Republic of Maldives | Semi-Cooked Operations", align="C", new_x="LMARGIN", new_y="NEXT")
    self.set_font("Helvetica", "B", 9)
    self.cell(0, 5, "OFFICIAL SALARY DISBURSEMENT SLIP", align="C", new_x="LMARGIN", new_y="NEXT")
    self.line(10, 24, 200, 24)
    self.ln(4)

  def footer(self):
    self.set_y(-20)
    self.set_font("Helvetica", "I", 8)
    self.cell(0, 4, "Maldives Employment Act & Pension Act Compliant Record | Generated by Zelqon Enterprise HR", align="C", new_x="LMARGIN", new_y="NEXT")

def generate_payslip_bytes(emp_name, staff_id, role, bank_acc, period_str, base_salary, days_present, days_absent, leave_days, ot_hours, ot_pay, ramazan_allowance, other_allowances, absence_deduction, salary_advance, pension_employee, pension_employer, net_pay, annual_bal, sick_bal, family_bal, remaining_loan_bal=0.0):
  pdf = PayslipPDF()
  pdf.add_page()
  pdf.set_auto_page_break(auto=True, margin=12)

  pdf.set_fill_color(245, 247, 250)
  pdf.rect(10, 27, 190, 24, "F")
  pdf.set_xy(12, 29)
  pdf.set_font("Helvetica", "B", 9)
  pdf.cell(28, 4, "Employee Name:")
  pdf.set_font("Helvetica", "", 9)
  pdf.cell(67, 4, str(emp_name))
  pdf.set_font("Helvetica", "B", 9)
  pdf.cell(25, 4, "Staff ID:")
  pdf.set_font("Helvetica", "", 9)
  pdf.cell(70, 4, str(staff_id), new_x="LMARGIN", new_y="NEXT")
  pdf.set_x(12)
  pdf.set_font("Helvetica", "B", 9)
  pdf.cell(28, 4, "Station / Role:")
  pdf.set_font("Helvetica", "", 9)
  pdf.cell(67, 4, str(role))
  pdf.set_font("Helvetica", "B", 9)
  pdf.cell(25, 4, "Bank Account:")
  pdf.set_font("Helvetica", "", 9)
  pdf.cell(70, 4, str(bank_acc) if bank_acc else "Cash Payment", new_x="LMARGIN", new_y="NEXT")
  pdf.set_x(12)
  pdf.set_font("Helvetica", "B", 9)
  pdf.cell(28, 4, "Pay Period:")
  pdf.set_font("Helvetica", "", 9)
  pdf.cell(67, 4, str(period_str))
  pdf.set_font("Helvetica", "B", 9)
  pdf.cell(25, 4, "Currency:")
  pdf.set_font("Helvetica", "", 9)
  pdf.cell(70, 4, "Maldivian Rufiyaa (MVR)", new_x="LMARGIN", new_y="NEXT")
  pdf.ln(8)

  pdf.set_font("Helvetica", "B", 10)
  pdf.cell(0, 5, "1. Monthly Duty & Attendance", new_x="LMARGIN", new_y="NEXT")
  pdf.set_font("Helvetica", "", 9)
  pdf.cell(63, 4, f"Days Worked: {days_present:.1f}", border=0, align="L")
  pdf.cell(63, 4, f"Approved Leaves: {leave_days:.1f}", border=0, align="L")
  pdf.cell(64, 4, f"Unexcused Absences: {days_absent:.1f}", border=0, align="L", new_x="LMARGIN", new_y="NEXT")
  pdf.cell(0, 4, f"Recorded Overtime Hours: {ot_hours:.1f} hrs", new_x="LMARGIN", new_y="NEXT")
  pdf.ln(1)
  
  pdf.set_font("Helvetica", "I", 8)
  pdf.cell(0, 4, f"* Remaining Yearly Leave Quotas: Annual ({annual_bal:.0f}d) | Sick ({sick_bal:.0f}d) | Family ({family_bal:.0f}d)", new_x="LMARGIN", new_y="NEXT")
  pdf.ln(4)

  pdf.set_font("Helvetica", "B", 10)
  pdf.cell(0, 5, "2. Itemized Earnings & Deductions", new_x="LMARGIN", new_y="NEXT")
  pdf.set_fill_color(230, 235, 240)
  pdf.set_font("Helvetica", "B", 9)
  pdf.cell(130, 6, "Description", border=1, fill=True)
  pdf.cell(60, 6, "Amount (MVR)", border=1, fill=True, align="R")
  pdf.ln(6)
  pdf.set_font("Helvetica", "", 9)

  def add_table_row(desc, amount, prefix=""):
    pdf.cell(130, 5, desc, border=1)
    amt_str = f"{prefix}{amount:,.2f}" if amount > 0 else "0.00"
    pdf.cell(60, 5, amt_str, border=1, align="R")
    pdf.ln(5)

  add_table_row("Basic Monthly Salary", base_salary)
  add_table_row(f"Overtime Allowance ({ot_hours:.1f} hrs @ 1.25x)", ot_pay, prefix="+")
  if ramazan_allowance > 0: add_table_row("Mandatory Ramazan Allowance (Legal)", ramazan_allowance, prefix="+")
  if other_allowances > 0: add_table_row("Production Bonus / Special Allowances", other_allowances, prefix="+")
  if absence_deduction > 0: add_table_row(f"Absence Deductions ({days_absent:.1f} days)", absence_deduction, prefix="-")
  if salary_advance > 0: add_table_row("Loan / Advance Repayment Installment", salary_advance, prefix="-")
  if pension_employee > 0: add_table_row("Maldives Retirement Pension (MRPS - 7% Employee)", pension_employee, prefix="-")

  pdf.set_fill_color(240, 242, 245)
  pdf.set_font("Helvetica", "B", 10)
  pdf.cell(130, 7, "TOTAL NET DISBURSEMENT", border=1, fill=True)
  pdf.cell(60, 7, f"MVR {net_pay:,.2f}", border=1, fill=True, align="R")
  pdf.ln(9)

  if pension_employer > 0 or remaining_loan_bal > 0:
    pdf.set_font("Helvetica", "I", 8)
    if pension_employer > 0:
        pdf.cell(0, 4, f"* Employer Pension Contribution: MVR {pension_employer:,.2f} (7% Zelqon Foods direct contribution to MRPS).", new_x="LMARGIN", new_y="NEXT")
    if remaining_loan_bal > 0:
        pdf.cell(0, 4, f"* Outstanding Loan/Advance Balance remaining after this deduction: MVR {remaining_loan_bal:,.2f}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

  pdf.ln(10)
  pdf.set_font("Helvetica", "", 8)
  pdf.cell(90, 4, "___________________________________")
  pdf.cell(10, 4, "")
  pdf.cell(90, 4, "___________________________________", new_x="LMARGIN", new_y="NEXT")
  pdf.cell(90, 4, "Authorized Officer / Zelqon Management")
  pdf.cell(10, 4, "")
  pdf.cell(90, 4, "Employee Signature / Acknowledgment", new_x="LMARGIN", new_y="NEXT")

  return bytes(pdf.output())


# --- Sidebar Setup ---
with st.sidebar:
  st.markdown("### 🏢 Zelqon Foods")
  st.caption("Operations & HR Control System")
  st.divider()
  with st.container(border=True):
    st.markdown(f"👤 **Operator:**<br>`{st.session_state.current_name}`", unsafe_allow_html=True)
    st.markdown(f"🛡️ **Access Clearance:** `{st.session_state.current_role}`")
    st.write("")
    if st.button("🚪 End Secure Session", use_container_width=True, type="secondary"):
      st.session_state.auth_status = False
      st.session_state.current_user = None
      st.session_state.current_role = None
      st.session_state.current_name = None
      st.rerun()

  if st.session_state.current_role == "Admin":
    st.divider()
    st.markdown("#### 💾 Database Exports")
    staff_backup = load_staff_data()
    if not staff_backup.empty:
      st.download_button("📥 Export Personnel (CSV)", data=staff_backup.to_csv(index=False).encode("utf-8"), file_name=f"Zelqon_Staff_{date.today()}.csv", mime="text/csv", use_container_width=True)
    att_backup = load_attendance_data()
    if not att_backup.empty:
      st.download_button("📥 Export Attendance (CSV)", data=att_backup.to_csv(index=False).encode("utf-8"), file_name=f"Zelqon_Attendance_{date.today()}.csv", mime="text/csv", use_container_width=True)

# --- Executive Dashboard Hero Banner ---
st.markdown("""
    <div class="zelqon-hero-card">
        <span class="zelqon-badge">Zelqon Foods Enterprise Hub</span>
        <h1 class="zelqon-hero-title">Workforce & Operations Portal</h1>
        <p class="zelqon-hero-subtitle">Fuvahmulah City, Republic of Maldives &bull; Semi-Cooked Processing Operations</p>
    </div>
""", unsafe_allow_html=True)

if st.session_state.current_role == "Admin":
  tab_att, tab_dir, tab_leave, tab_pay, tab_analytics = st.tabs([
      "🕒 Attendance",
      "👥 Directory",
      "📊 Leaves",
      "💼 Payroll",
      "📈 Analytics"
  ])
else:
  tab_att, = st.tabs(["🕒 Daily Attendance & Shifts"])
  st.info("ℹ️ **Kitchen Staff Mode:** Shift logging active. Management records and financial ledgers are locked.")

# =========================================================
# TAB 1: DAILY ATTENDANCE AND SHIFT LOGGING
# =========================================================
with tab_att:
  staff_df = load_staff_data()
  if staff_df.empty or "Name" not in staff_df.columns:
    st.warning("⚠️ No personnel registered in the database. Please add staff in the Workforce Directory.")
  else:
    with st.container(border=True):
      st.markdown("#### ⚡ Quick Batch Duty Log")
      st.caption("Instantly mark all registered active kitchen team members as 'Present'.")
      batch_col1, batch_col2 = st.columns([2, 1])
      with batch_col1:
        batch_date = st.date_input("Select Attendance Date", value=date.today(), key="batch_att_date")
      with batch_col2:
        st.write("")
        st.write("")
        if st.button("Commit Batch Present", type="primary", use_container_width=True):
          current_att = load_attendance_data()
          new_batch_rows = []
          for _, emp in staff_df.iterrows():
            new_batch_rows.append({"Date": str(batch_date), "Staff ID": emp["Staff ID"], "Name": emp["Name"], "Station": emp.get("Role", "Semi-Cooked Processing"), "Status": "Present", "Overtime Hours": 0.0, "Notes": "Auto Batch Check-In"})
          batch_df = pd.DataFrame(new_batch_rows)
          updated_att = pd.concat([current_att, batch_df], ignore_index=True) if not current_att.empty else batch_df
          robust_update("Attendance", data=updated_att)
          st.cache_data.clear()
          st.success(f"Recorded Present status for {len(staff_df)} members on {batch_date}.")
          st.rerun()

    st.write("")
    with st.container(border=True):
      st.markdown("#### 📝 Record Individual Shift")
      st.caption("Log daily attendance status, workstation assignments, overtime hours, and notes.")
      with st.form("single_attendance_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1: shift_date = st.date_input("Shift Date", value=date.today())
        with c2: selected_emp = st.selectbox("Staff Member", options=staff_df["Name"])
        with c3: selected_station = st.selectbox("Assigned Station", options=["Semi-Cooked Processing", "Packaging & Sealing", "Fuvahmulah Distribution", "Kitchen Cleaning & Prep"])

        c4, c5 = st.columns(2)
        with c4: status = st.selectbox("Duty Status", options=["Present", "Half Day", "Annual Leave", "Sick Leave", "Family Leave", "Unexcused Absent"])
        with c5: ot_hours = st.number_input("Overtime Worked (Hours)", min_value=0.0, max_value=12.0, value=0.0, step=0.5)

        shift_notes = st.text_input("Shift Notes (Optional)")
        submit_shift = st.form_submit_button("💾 Save Shift Entry", type="primary")

        if submit_shift:
          current_att = load_attendance_data()
          emp_id = staff_df[staff_df["Name"] == selected_emp]["Staff ID"].values[0] if not staff_df[staff_df["Name"] == selected_emp].empty else "ZF-000"
          new_entry = pd.DataFrame([{"Date": str(shift_date), "Staff ID": str(emp_id), "Name": str(selected_emp), "Station": str(selected_station), "Status": str(status), "Overtime Hours": float(ot_hours), "Notes": str(shift_notes)}])
          updated_att = pd.concat([current_att, new_entry], ignore_index=True) if not current_att.empty else new_entry
          robust_update("Attendance", data=updated_att)
          st.cache_data.clear()
          st.success(f"Shift successfully logged for {selected_emp}.")
          st.rerun()

    st.write("")
    with st.container(border=True):
      st.markdown("#### 🛠️ Shift Ledger Management")
      st.caption("Inspect real-time entries and void erroneous records from the cloud cache.")
      att_records = load_attendance_data()
      if not att_records.empty:
        valid_att = att_records.dropna(subset=["Date", "Name"]).copy()
        if not valid_att.empty:
          st.dataframe(valid_att, use_container_width=True, hide_index=True)
          shift_options = {f"{row['Date']} | {row['Name']} ({row['Status']}) @ {row['Station']} - {row['Overtime Hours']}h OT": idx for idx, row in valid_att.iterrows()}
          del_col1, del_col2 = st.columns([3, 1])
          with del_col1: selected_shift_to_delete = st.selectbox("Select historical entry to void:", options=list(shift_options.keys()), key="delete_shift_select")
          with del_col2:
            st.write("")
            st.write("")
            if st.button("🗑️ Void Entry", type="secondary", use_container_width=True):
              row_to_drop = shift_options[selected_shift_to_delete]
              remaining_att = att_records.drop(index=row_to_drop).reset_index(drop=True)
              if remaining_att.empty: remaining_att = pd.DataFrame(columns=["Date", "Staff ID", "Name", "Station", "Status", "Overtime Hours", "Notes"])
              robust_update("Attendance", data=remaining_att)
              st.cache_data.clear()
              st.success("Entry voided and synced.")
              st.rerun()

# =========================================================
# TAB 2: WORKFORCE DIRECTORY (ADMIN ONLY)
# =========================================================
if st.session_state.current_role == "Admin":
  with tab_dir:
    dir_col1, dir_col2 = st.columns([1, 1])
    with dir_col1:
      with st.container(border=True):
        st.markdown("#### ➕ Register New Team Member")
        staff_df = load_staff_data()
        next_id_num = 1
        if not staff_df.empty and "Staff ID" in staff_df.columns:
          existing_ids = staff_df["Staff ID"].dropna().astype(str).tolist()
          numeric_ids = [int(x.replace("ZF-", "")) for x in existing_ids if x.startswith("ZF-") and x.replace("ZF-", "").isdigit()]
          if numeric_ids: next_id_num = max(numeric_ids) + 1
        auto_id = f"ZF-{next_id_num:03d}"

        with st.form("new_employee_form", clear_on_submit=True):
          st.text_input("Assigned Staff ID", value=auto_id, disabled=True)
          new_name = st.text_input("Full Legal Name")
          new_role = st.selectbox("Primary Operational Role", options=["Semi-Cooked Processing", "Packaging & Quality", "Fuvahmulah Delivery & Sales", "Kitchen Supervision"])
          new_salary = st.number_input("Base Monthly Salary (MVR)", min_value=1000.0, value=5000.0, step=250.0)
          new_days = st.number_input("Standard Work Days / Month", min_value=30, max_value=30, value=30, disabled=True) # Lock applied
          new_bank = st.text_input("Bank Account Number (Optional)", placeholder="e.g. BML 7730000123456")
          new_pension = st.selectbox("Enroll in Maldives Pension (MRPS)?", options=["No", "Yes"])
          submit_new_staff = st.form_submit_button("💾 Register Personnel", type="primary")

          if submit_new_staff:
            if not new_name.strip(): st.error("Personnel full name is required.")
            else:
              new_row = pd.DataFrame([{"Staff ID": auto_id, "Name": new_name.strip(), "Role": new_role, "Base Salary (MVR)": float(new_salary), "Standard Monthly Days": int(new_days), "Bank Account": str(new_bank).strip(), "Pension Enrolled": str(new_pension)}])
              updated_staff = pd.concat([staff_df, new_row], ignore_index=True) if not staff_df.empty else new_row
              robust_update("Staff", data=updated_staff)
              st.cache_data.clear()
              st.success(f"Registered {new_name} ({auto_id}) successfully!")
              st.rerun()

    with dir_col2:
      with st.container(border=True):
        st.markdown("#### 📋 Active Personnel Directory")
        if not staff_df.empty:
          st.dataframe(staff_df, use_container_width=True, hide_index=True)
          st.divider()
          st.markdown("##### Remove Personnel Record")
          staff_to_delete = st.selectbox("Select employee to purge from system:", options=staff_df["Name"].tolist(), key="delete_staff_box")
          if st.button("⚠️ Purge from Database", type="secondary"):
            remaining = staff_df[staff_df["Name"] != staff_to_delete].reset_index(drop=True)
            if remaining.empty: remaining = pd.DataFrame(columns=["Staff ID", "Name", "Role", "Base Salary (MVR)", "Standard Monthly Days", "Bank Account", "Pension Enrolled"])
            robust_update("Staff", data=remaining)
            st.cache_data.clear()
            st.warning(f"Purged {staff_to_delete} from database.")
            st.rerun()
        else:
          st.info("No personnel currently registered.")

# =========================================================
# TAB 3: LEAVE MANAGEMENT (ADMIN ONLY)
# =========================================================
if st.session_state.current_role == "Admin":
  with tab_leave:
    with st.container(border=True):
      st.markdown("#### 📊 Legal Leave Quota Utilization")
      current_year = date.today().year
      st.caption(f"Maldives Employment Act legal tracking for fiscal year **{current_year}**.")
      staff_df = load_staff_data()
      att_df = load_attendance_data()
      if staff_df.empty: st.info("Register staff in the Workforce Directory to initialize leave tracking.")
      else:
        if not att_df.empty and "Date" in att_df.columns:
          att_df["Parsed_Date"] = pd.to_datetime(att_df["Date"], errors="coerce")
          yearly_att = att_df[att_df["Parsed_Date"].dt.year == current_year]
        else:
          yearly_att = pd.DataFrame()
        leave_records = []
        for _, emp in staff_df.iterrows():
          name = emp["Name"]
          ann_used, sick_used, fam_used = 0, 0, 0
          if not yearly_att.empty:
            emp_att = yearly_att[yearly_att["Name"] == name]
            ann_used = len(emp_att[emp_att["Status"] == "Annual Leave"])
            sick_used = len(emp_att[emp_att["Status"] == "Sick Leave"])
            fam_used = len(emp_att[emp_att["Status"] == "Family Leave"])
          leave_records.append({"Personnel": name, "Annual Remaining (30)": max(0, 30 - ann_used), "Sick Remaining (30)": max(0, 30 - sick_used), "Family Remaining (10)": max(0, 10 - fam_used), "Annual Used": ann_used, "Sick Used": sick_used, "Family Used": fam_used})
        leave_df = pd.DataFrame(leave_records)
        st.dataframe(leave_df, use_container_width=True, hide_index=True, column_config={"Personnel": st.column_config.TextColumn("Personnel"), "Annual Remaining (30)": st.column_config.ProgressColumn("Annual Remaining (30d)", format="%d days", min_value=0, max_value=30), "Sick Remaining (30)": st.column_config.ProgressColumn("Sick Remaining (30d)", format="%d days", min_value=0, max_value=30), "Family Remaining (10)": st.column_config.ProgressColumn("Family Remaining (10d)", format="%d days", min_value=0, max_value=10)})
        st.info("💡 **Automation Logic:** The system scans the shift log for the current calendar year. Marking a shift as 'Sick Leave' automatically deducts from their quota. Balances auto-reset on January 1st.")

# =========================================================
# TAB 4: PAYROLL & COMPLIANCE (ADMIN ONLY)
# =========================================================
if st.session_state.current_role == "Admin":
  with tab_pay:
    staff_df = load_staff_data()
    att_df = load_attendance_data()
    adv_df = load_advances_data()

    if staff_df.empty:
      st.info("Awaiting staff registration to initialize the payroll engine.")
    else:
      with st.container(border=True):
        st.markdown("#### ⚙️ Fiscal Payroll Parameters")
        p_col1, p_col2, p_col3 = st.columns(3)
        with p_col1:
          months_list = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
          active_m_idx = datetime.now().month - 1
          selected_month_name = st.selectbox("Operating Month", options=months_list, index=active_m_idx)
          selected_month_num = months_list.index(selected_month_name) + 1
        with p_col2:
          selected_year = st.selectbox("Operating Year", options=[2025, 2026, 2027], index=1)
        with p_col3:
          st.write("")
          st.write("")
          include_ramazan = st.checkbox("Apply Mandatory Ramazan Allowance (MVR 3,000)", value=False)
        period_label = f"{selected_month_name} {selected_year}"

        if not att_df.empty and "Date" in att_df.columns:
          att_df["Parsed_Date"] = pd.to_datetime(att_df["Date"], errors="coerce")
          period_att = att_df[(att_df["Parsed_Date"].dt.month == selected_month_num) & (att_df["Parsed_Date"].dt.year == selected_year)]
          yearly_att = att_df[att_df["Parsed_Date"].dt.year == selected_year]
        else:
          period_att = pd.DataFrame()
          yearly_att = pd.DataFrame()

      st.write("")
      
      # ROLLING LOAN MANAGER
      with st.expander("💳 Manage Rolling Loans & Advances (Multi-Month)", expanded=False):
        st.markdown("##### ➕ Issue New Loan")
        with st.form("new_loan_form", clear_on_submit=True):
          l_c1, l_c2, l_c3 = st.columns(3)
          with l_c1: loan_emp = st.selectbox("Staff Member", options=staff_df["Name"])
          with l_c2: loan_amt = st.number_input("Total Loan Amount (MVR)", min_value=0.0, step=500.0)
          with l_c3: loan_install = st.number_input("Monthly Deduction Installment (MVR)", min_value=0.0, step=100.0)
          if st.form_submit_button("Issue Loan", type="primary"):
            emp_id_val = staff_df[staff_df["Name"] == loan_emp]["Staff ID"].values[0]
            new_loan = pd.DataFrame([{"Staff ID": emp_id_val, "Name": loan_emp, "Total Loan (MVR)": loan_amt, "Monthly Installment (MVR)": loan_install, "Remaining Balance (MVR)": loan_amt}])
            updated_adv = pd.concat([adv_df, new_loan], ignore_index=True) if not adv_df.empty else new_loan
            robust_update("Advances", data=updated_adv)
            st.cache_data.clear()
            st.success(f"Loan of MVR {loan_amt} issued to {loan_emp}.")
            st.rerun()
            
        st.divider()
        st.markdown("##### 📋 Active Loan Ledgers")
        if not adv_df.empty:
            active_loans = adv_df[adv_df["Remaining Balance (MVR)"] > 0]
            if not active_loans.empty:
                st.dataframe(active_loans, use_container_width=True, hide_index=True)
                st.info("💡 The system will automatically deduct the Monthly Installment during payroll processing below if a balance exists.")
                
                c_commit, c_void = st.columns(2)
                
                with c_commit:
                    st.markdown("##### ✅ Commit Repayment")
                    st.caption("Manually deduct the installment from the balance.")
                    loan_to_pay = st.selectbox("Select Employee:", options=active_loans["Name"].tolist(), key="commit_loan")
                    if st.button("Commit Deduction", type="secondary", use_container_width=True):
                        idx_to_update = adv_df[adv_df["Name"] == loan_to_pay].index[-1]
                        installment = float(adv_df.at[idx_to_update, "Monthly Installment (MVR)"])
                        current_bal = float(adv_df.at[idx_to_update, "Remaining Balance (MVR)"])
                        adv_df.at[idx_to_update, "Remaining Balance (MVR)"] = max(0.0, current_bal - installment)
                        robust_update("Advances", data=adv_df)
                        st.cache_data.clear()
                        st.success(f"Deducted MVR {installment} from {loan_to_pay}'s loan balance.")
                        st.rerun()
                        
                with c_void:
                    st.markdown("##### 🗑️ Void Active Loan")
                    st.caption("Mistake in issuing? Void the ledger entirely.")
                    
                    # Create a dictionary to map the display string back to the exact dataframe index
                    loan_options = {f"{row['Name']} | Bal: MVR {row['Remaining Balance (MVR)']}": idx for idx, row in active_loans.iterrows()}
                    
                    loan_to_delete = st.selectbox("Select ledger to void:", options=list(loan_options.keys()), key="void_loan")
                    if st.button("Void Ledger", type="secondary", use_container_width=True):
                        row_to_drop = loan_options[loan_to_delete]
                        remaining_adv = adv_df.drop(index=row_to_drop).reset_index(drop=True)
                        if remaining_adv.empty: 
                            remaining_adv = pd.DataFrame(columns=["Staff ID", "Name", "Total Loan (MVR)", "Monthly Installment (MVR)", "Remaining Balance (MVR)"])
                        robust_update("Advances", data=remaining_adv)
                        st.cache_data.clear()
                        st.warning("Loan ledger voided and removed from database.")
                        st.rerun()
            else:
                st.info("No active loans.")
        else:
            st.info("No loans issued yet.")

      st.write("")

      with st.container(border=True):
        st.markdown("#### 🛠️ Monthly Adjustments & Piece-Rate Bonuses")
        st.caption("Apply manual additions, or calculate bonuses based on units produced.")
        bonuses_dict = {}

        for idx, emp in staff_df.iterrows():
          emp_name = emp["Name"]
          with st.expander(f"Bonuses for: {emp_name}"):
            b_c1, b_c2, b_c3 = st.columns(3)
            with b_c1:
                bonus_type = st.selectbox(f"Bonus Type", options=["Fixed Amount", "Piece-Rate (Per Unit)"], key=f"btype_{emp['Staff ID']}")
            with b_c2:
                if bonus_type == "Fixed Amount":
                    bon_val = st.number_input(f"Fixed Bonus (MVR)", min_value=0.0, value=0.0, step=100.0, key=f"fbon_{emp['Staff ID']}")
                    bonuses_dict[emp_name] = bon_val
                else:
                    units_prod = st.number_input(f"Units Produced", min_value=0, value=0, step=1, key=f"units_{emp['Staff ID']}")
            with b_c3:
                if bonus_type == "Piece-Rate (Per Unit)":
                    rate_per_unit = st.number_input(f"Rate Per Unit (MVR)", min_value=0.0, value=0.0, step=1.0, key=f"rate_{emp['Staff ID']}")
                    bonuses_dict[emp_name] = (units_prod * rate_per_unit)

      # --- Execute Calculations ---
      payroll_list = []
      bml_transfer_list = []

      for _, emp in staff_df.iterrows():
        name = emp["Name"]
        staff_id = emp["Staff ID"]
        role = emp.get("Role", "Kitchen Operations")
        
        bank_raw = emp.get("Bank Account", "")
        if pd.isna(bank_raw) or str(bank_raw).strip().lower() in ["nan", "none", ""]: bank_acc = ""
        else: bank_acc = str(bank_raw).strip()
            
        base_sal = float(emp["Base Salary (MVR)"])
        std_days = 30.0 # STRICT 30-DAY OVERRIDE
        is_pension = str(emp.get("Pension Enrolled", "No")).strip().lower() in ["yes", "true", "1"]

        daily_rate = base_sal / std_days
        hourly_rate = daily_rate / 8.0

        present_count = 0.0
        leave_count = 0.0
        manual_absent_count = 0.0
        ot_hours_total = 0.0

        if not period_att.empty:
          records = period_att[period_att["Name"] == name]
          for _, row in records.iterrows():
            st_val = str(row["Status"])
            if st_val == "Present": present_count += 1.0
            elif st_val == "Half Day":
              present_count += 0.5
              manual_absent_count += 0.5
            elif st_val in ["Annual Leave", "Sick Leave", "Family Leave"]:
              leave_count += 1.0
              present_count += 1.0
            elif st_val == "Unexcused Absent": manual_absent_count += 1.0
            try: ot_hours_total += float(row["Overtime Hours"])
            except: pass

        auto_absent_count = max(0.0, std_days - present_count)
        final_absences = max(manual_absent_count, auto_absent_count)
        
        ann_used, sick_used, fam_used = 0, 0, 0
        if not yearly_att.empty:
          y_rec = yearly_att[yearly_att["Name"] == name]
          ann_used = len(y_rec[y_rec["Status"] == "Annual Leave"])
          sick_used = len(y_rec[y_rec["Status"] == "Sick Leave"])
          fam_used = len(y_rec[y_rec["Status"] == "Family Leave"])

        ann_bal = max(0, 30 - ann_used)
        sick_bal = max(0, 30 - sick_used)
        fam_bal = max(0, 10 - fam_used)

        ot_payout = ot_hours_total * hourly_rate * 1.25
        absence_deduction = final_absences * daily_rate
        ramazan_amt = 3000.0 if include_ramazan else 0.0
        extra_allowance = bonuses_dict.get(name, 0.0)
        
        # Advance / Loan Auto-Pull Logic
        advance_deduction = 0.0
        remaining_loan_bal = 0.0
        if not adv_df.empty:
            emp_loans = adv_df[(adv_df["Name"] == name) & (adv_df["Remaining Balance (MVR)"] > 0)]
            if not emp_loans.empty:
                last_loan_idx = emp_loans.index[-1]
                bal = float(emp_loans.at[last_loan_idx, "Remaining Balance (MVR)"])
                install = float(emp_loans.at[last_loan_idx, "Monthly Installment (MVR)"])
                advance_deduction = min(bal, install)
                remaining_loan_bal = max(0.0, bal - advance_deduction)

        pension_ee = (base_sal * 0.07) if is_pension else 0.0
        pension_er = (base_sal * 0.07) if is_pension else 0.0

        net_payout = (base_sal + ot_payout + ramazan_amt + extra_allowance - absence_deduction - advance_deduction - pension_ee)

        payroll_list.append({"Staff ID": staff_id, "Name": name, "Role": role, "Bank Account": bank_acc, "Base Salary": base_sal, "Present": present_count, "Leave Count": leave_count, "Absences": final_absences, "OT (Hrs)": ot_hours_total, "OT Pay": ot_payout, "Ramazan": ramazan_amt, "Bonuses": extra_allowance, "Absence Deduct": absence_deduction, "Advances": advance_deduction, "Remaining Loan Bal": remaining_loan_bal, "Pension (7%)": pension_ee, "Net Payout (MVR)": net_payout, "Employer Pension": pension_er, "Ann_Bal": ann_bal, "Sick_Bal": sick_bal, "Fam_Bal": fam_bal})
        bml_transfer_list.append({"Staff ID": staff_id, "Beneficiary Name": name, "Account Number": bank_acc if bank_acc else "CASH_PAYMENT", "Disbursement Amount (MVR)": round(net_payout, 2), "Payment Reference": f"Salary {period_label}"})

      payroll_df = pd.DataFrame(payroll_list)

      st.write("")
      with st.container(border=True):
        st.markdown(f"#### 💰 Master Payroll Ledger — {period_label}")
        st.dataframe(payroll_df.drop(columns=["Role", "Bank Account", "Ann_Bal", "Sick_Bal", "Fam_Bal", "Employer Pension", "Remaining Loan Bal"]).style.format({"Base Salary": "{:,.2f}", "Present": "{:.1f}", "Absences": "{:.1f}", "OT (Hrs)": "{:.1f}", "OT Pay": "{:,.2f}", "Ramazan": "{:,.2f}", "Bonuses": "{:,.2f}", "Absence Deduct": "{:,.2f}", "Advances": "{:,.2f}", "Pension (7%)": "{:,.2f}", "Net Payout (MVR)": "{:,.2f}"}), use_container_width=True, hide_index=True)
        st.divider()
        bml_df = pd.DataFrame(bml_transfer_list)
        bml_csv = bml_df.to_csv(index=False).encode("utf-8")
        st.download_button(label=f"📥 Download Bank Transfer File ({period_label} CSV)", data=bml_csv, file_name=f"Zelqon_Bank_Transfer_{period_label.replace(' ', '_')}.csv", mime="text/csv", type="secondary")

      st.write("")
      with st.container(border=True):
        st.markdown("#### 📄 Certified Payslip Generation")
        chosen_person = st.selectbox("Select personnel to generate official payslip:", options=payroll_df["Name"].tolist())
        target = payroll_df[payroll_df["Name"] == chosen_person].iloc[0]

        with st.container(border=True):
          c_met1, c_met2, c_met3, c_met4 = st.columns(4)
          c_met1.metric("Base Pay", f"MVR {target['Base Salary']:,.2f}")
          c_met2.metric("Additions", f"MVR {(target['OT Pay'] + target['Ramazan'] + target['Bonuses']):,.2f}")
          c_met3.metric("Deductions", f"MVR {(target['Absence Deduct'] + target['Advances'] + target['Pension (7%)']):,.2f}")
          c_met4.metric("Net Salary", f"MVR {target['Net Payout (MVR)']:,.2f}")

        payslip_pdf = generate_payslip_bytes(emp_name=target["Name"], staff_id=target["Staff ID"], role=target["Role"], bank_acc=target["Bank Account"], period_str=period_label, base_salary=target["Base Salary"], days_present=target["Present"], days_absent=target["Absences"], leave_days=target["Leave Count"], ot_hours=target["OT (Hrs)"], ot_pay=target["OT Pay"], ramazan_allowance=target["Ramazan"], other_allowances=target["Bonuses"], absence_deduction=target["Absence Deduct"], salary_advance=target["Advances"], pension_employee=target["Pension (7%)"], pension_employer=target["Employer Pension"], net_pay=target["Net Payout (MVR)"], annual_bal=target["Ann_Bal"], sick_bal=target["Sick_Bal"], family_bal=target["Fam_Bal"], remaining_loan_bal=target["Remaining Loan Bal"])
        st.write("")
        st.download_button(label=f"📥 Download Certified Payslip for {target['Name']} (PDF)", data=payslip_pdf, file_name=f"Payslip_{target['Name'].replace(' ', '_')}_{period_label.replace(' ', '_')}.pdf", mime="application/pdf", type="primary")

# =========================================================
# TAB 5: FINANCIAL ANALYTICS DASHBOARD (ADMIN ONLY)
# =========================================================
if st.session_state.current_role == "Admin":
  with tab_analytics:
    st.subheader("📈 Labor Cost & Operations Analytics")
    st.caption("Visual breakdown of payroll liabilities and workforce metrics.")
    
    staff_df = load_staff_data()
    att_df = load_attendance_data()
    
    if staff_df.empty:
        st.info("Insufficient data to generate analytics.")
    else:
        a_col1, a_col2, a_col3 = st.columns(3)
        total_payroll = staff_df["Base Salary (MVR)"].sum()
        total_staff = len(staff_df)
        avg_salary = total_payroll / total_staff if total_staff > 0 else 0
        
        a_col1.metric("Active Workforce", f"{total_staff} Staff")
        a_col2.metric("Total Monthly Base Liability", f"MVR {total_payroll:,.2f}")
        a_col3.metric("Average Base Salary", f"MVR {avg_salary:,.2f}")
        
        st.divider()
        
        c_chart1, c_chart2 = st.columns(2)
        with c_chart1:
            st.markdown("##### 👥 Salary Distribution by Role")
            role_dist = staff_df.groupby("Role")["Base Salary (MVR)"].sum().reset_index()
            st.bar_chart(role_dist, x="Role", y="Base Salary (MVR)", color="#1E3A8A")
            
        with c_chart2:
            st.markdown("##### 🕒 All-Time Overtime by Employee")
            if not att_df.empty:
                ot_data = att_df.copy()
                ot_data["Overtime Hours"] = pd.to_numeric(ot_data["Overtime Hours"], errors='coerce').fillna(0)
                ot_dist = ot_data.groupby("Name")["Overtime Hours"].sum().reset_index()
                st.bar_chart(ot_dist, x="Name", y="Overtime Hours", color="#38BDF8")
            else:
                st.info("No attendance data logged for overtime tracking.")
