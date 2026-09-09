from datetime import date, datetime
import hashlib
import io
from fpdf import FPDF
import pandas as pd
import streamlit as st
from streamlit_gsheets import GSheetsConnection

# --- Page Configuration ---
st.set_page_config(
    page_title="Zelqon Foods | HR & Payroll", page_icon="🍳", layout="wide"
)

# --- User Authentication System ---
USER_CREDENTIALS = {
    "admin": {
        "password": (
            st.secrets.get("credentials", {})
            .get("admin", {})
            .get("password", "zelqon2026")
        ),
        "role": "Admin",
        "name": "Zelqon Management",
    },
    "kitchen": {
        "password": (
            st.secrets.get("credentials", {})
            .get("kitchen", {})
            .get("password", "food123")
        ),
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


# --- Login Screen Gate ---
if not st.session_state.auth_status:
  col_pad_left, col_login, col_pad_right = st.columns([1, 2, 1])

  with col_login:
    st.write("")
    st.write("")
    st.markdown("### 🔐 Zelqon Foods HR Portal")
    st.caption("Fuvahmulah, Maldives | Secure Authentication Required")

    with st.form("zelqon_login_form"):
      login_user = st.text_input(
          "Username", placeholder="e.g. admin or kitchen"
      )
      login_pass = st.text_input("Password", type="password")
      submit_login = st.form_submit_button(
          "Sign In to Operations", type="primary", use_container_width=True
      )

      if submit_login:
        success, role, name = verify_login(login_user, login_pass)
        if success:
          st.session_state.auth_status = True
          st.session_state.current_user = login_user.strip().lower()
          st.session_state.current_role = role
          st.session_state.current_name = name
          st.rerun()
        else:
          st.error("Invalid username or password. Please check your credentials.")

  st.stop()  # Halts execution so unauthenticated users cannot view data or sheets

# =========================================================
# AUTHENTICATED APP ENGINE
# =========================================================

conn = st.connection("gsheets", type=GSheetsConnection)


def load_staff_data():
  try:
    df = conn.read(worksheet="Staff", ttl=0)
    if df is None or df.empty:
      return pd.DataFrame(
          columns=[
              "Staff ID",
              "Name",
              "Role",
              "Base Salary (MVR)",
              "Standard Monthly Days",
              "Bank Account",
              "Pension Enrolled",
          ]
      )
    expected_cols = {
        "Staff ID": "ZF-001",
        "Name": "",
        "Role": "Semi-Cooked Processing",
        "Base Salary (MVR)": 4500.0,
        "Standard Monthly Days": 26,
        "Bank Account": "",
        "Pension Enrolled": "No",
    }
    for col, default_val in expected_cols.items():
      if col not in df.columns:
        df[col] = default_val
    return df.dropna(subset=["Staff ID", "Name"])
  except Exception:
    return pd.DataFrame(
        columns=[
            "Staff ID",
            "Name",
            "Role",
            "Base Salary (MVR)",
            "Standard Monthly Days",
            "Bank Account",
            "Pension Enrolled",
        ]
    )


def load_attendance_data():
  try:
    df = conn.read(worksheet="Attendance", ttl=0)
    if df is None or df.empty:
      return pd.DataFrame(
          columns=[
              "Date",
              "Staff ID",
              "Name",
              "Station",
              "Status",
              "Overtime Hours",
              "Notes",
          ]
      )
    expected_cols = {
        "Date": str(date.today()),
        "Staff ID": "ZF-001",
        "Name": "",
        "Station": "Semi-Cooked Processing",
        "Status": "Present",
        "Overtime Hours": 0.0,
        "Notes": "",
    }
    for col, default_val in expected_cols.items():
      if col not in df.columns:
        df[col] = default_val
    return df.dropna(subset=["Date", "Name"])
  except Exception:
    return pd.DataFrame(
        columns=[
            "Date",
            "Staff ID",
            "Name",
            "Station",
            "Status",
            "Overtime Hours",
            "Notes",
        ]
    )


# --- Payslip PDF Engine ---
class PayslipPDF(FPDF):

  def header(self):
    self.set_font("Helvetica", "B", 15)
    self.cell(0, 7, "ZELQON FOODS", align="C", new_x="LMARGIN", new_y="NEXT")
    self.set_font("Helvetica", "", 8)
    self.cell(
        0,
        4,
        "Fuvahmulah City, Republic of Maldives | Registration: Semi-Cooked"
        " Operations",
        align="C",
        new_x="LMARGIN",
        new_y="NEXT",
    )
    self.set_font("Helvetica", "B", 9)
    self.cell(
        0,
        5,
        "OFFICIAL SALARY DISBURSEMENT SLIP",
        align="C",
        new_x="LMARGIN",
        new_y="NEXT",
    )
    self.line(10, 24, 200, 24)
    self.ln(4)

  def footer(self):
    self.set_y(-20)
    self.set_font("Helvetica", "I", 8)
    self.cell(
        0,
        4,
        "Maldives Employment Act & Pension Act Compliant Record | Generated by"
        " Zelqon HR",
        align="C",
        new_x="LMARGIN",
        new_y="NEXT",
    )


def generate_payslip_bytes(
    emp_name,
    staff_id,
    role,
    bank_acc,
    period_str,
    base_salary,
    days_present,
    days_absent,
    leave_days,
    ot_hours,
    ot_pay,
    ramazan_allowance,
    other_allowances,
    absence_deduction,
    salary_advance,
    pension_employee,
    pension_employer,
    net_pay,
):
  pdf = PayslipPDF()
  pdf.add_page()
  pdf.set_auto_page_break(auto=True, margin=12)

  # Employee Summary Box
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
  pdf.cell(
      70,
      4,
      str(bank_acc) if bank_acc else "Cash Payment",
      new_x="LMARGIN",
      new_y="NEXT",
  )

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

  # Attendance Section
  pdf.set_font("Helvetica", "B", 10)
  pdf.cell(0, 5, "1. Monthly Duty & Attendance", new_x="LMARGIN", new_y="NEXT")
  pdf.set_font("Helvetica", "", 9)
  pdf.cell(63, 4, f"Days Worked: {days_present:.1f}", border=0, align="L")
  pdf.cell(63, 4, f"Approved Leaves: {leave_days:.1f}", border=0, align="L")
  pdf.cell(
      64,
      4,
      f"Unexcused Absences: {days_absent:.1f}",
      border=0,
      align="L",
      new_x="LMARGIN",
      new_y="NEXT",
  )
  pdf.cell(
      0,
      4,
      f"Recorded Overtime Hours: {ot_hours:.1f} hrs",
      new_x="LMARGIN",
      new_y="NEXT",
  )

  pdf.ln(5)

  # Financial Breakdown Table
  pdf.set_font("Helvetica", "B", 10)
  pdf.cell(
      0,
      5,
      "2. Itemized Earnings & Deductions",
      new_x="LMARGIN",
      new_y="NEXT",
  )

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
  add_table_row(
      f"Overtime Allowance ({ot_hours:.1f} hrs @ 1.25x)", ot_pay, prefix="+"
  )
  if ramazan_allowance > 0:
    add_table_row(
        "Mandatory Ramazan Allowance (Legal)", ramazan_allowance, prefix="+"
    )
  if other_allowances > 0:
    add_table_row(
        "Special / Production Allowances", other_allowances, prefix="+"
    )

  if absence_deduction > 0:
    add_table_row(
        f"Absence Deductions ({days_absent:.1f} days)",
        absence_deduction,
        prefix="-",
    )
  if salary_advance > 0:
    add_table_row("Mid-Month Salary Advance Repayment", salary_advance, prefix="-")
  if pension_employee > 0:
    add_table_row(
        "Maldives Retirement Pension (MRPS - 7% Employee)",
        pension_employee,
        prefix="-",
    )

  # Total Row
  pdf.set_fill_color(240, 242, 245)
  pdf.set_font("Helvetica", "B", 10)
  pdf.cell(130, 7, "TOTAL NET DISBURSEMENT", border=1, fill=True)
  pdf.cell(60, 7, f"MVR {net_pay:,.2f}", border=1, fill=True, align="R")
  pdf.ln(9)

  # Pension Employer Note
  if pension_employer > 0:
    pdf.set_font("Helvetica", "I", 8)
    pdf.cell(
        0,
        4,
        f"* Employer Pension Contribution: MVR {pension_employer:,.2f} (7%"
        " Zelqon Foods direct contribution to MRPS).",
        new_x="LMARGIN",
        new_y="NEXT",
    )
    pdf.ln(4)

  # Signatures
  pdf.ln(10)
  pdf.set_font("Helvetica", "", 8)
  pdf.cell(90, 4, "___________________________________")
  pdf.cell(10, 4, "")
  pdf.cell(
      90, 4, "___________________________________", new_x="LMARGIN", new_y="NEXT"
  )

  pdf.cell(90, 4, "Authorized Officer / Zelqon Management")
  pdf.cell(10, 4, "")
  pdf.cell(
      90, 4, "Employee Signature / Acknowledgment", new_x="LMARGIN", new_y="NEXT"
  )

  return bytes(pdf.output())


# --- Sidebar Setup ---
with st.sidebar:
  st.title("Zelqon Foods")
  st.caption("Fuvahmulah, Maldives | Semi-Cooked Division")
  st.divider()

  # Active User Badge
  st.markdown(f"👤 **User:** {st.session_state.current_name}")
  st.markdown(f"🏷️ **Access Level:** `{st.session_state.current_role}`")

  if st.button("🚪 Sign Out", use_container_width=True, type="secondary"):
    st.session_state.auth_status = False
    st.session_state.current_user = None
    st.session_state.current_role = None
    st.session_state.current_name = None
    st.rerun()

  # Backups reserved for Managers
  if st.session_state.current_role == "Admin":
    st.divider()
    st.subheader("💾 Offline Backups")
    staff_backup = load_staff_data()
    if not staff_backup.empty:
      st.download_button(
          label="📥 Staff (CSV)",
          data=staff_backup.to_csv(index=False).encode("utf-8"),
          file_name=f"Zelqon_Staff_Backup_{date.today()}.csv",
          mime="text/csv",
          use_container_width=True,
      )
    att_backup = load_attendance_data()
    if not att_backup.empty:
      st.download_button(
          label="📥 Attendance (CSV)",
          data=att_backup.to_csv(index=False).encode("utf-8"),
          file_name=f"Zelqon_Attendance_Backup_{date.today()}.csv",
          mime="text/csv",
          use_container_width=True,
      )

# --- App Navigation by Role ---
st.title("Zelqon Foods Operations & Payroll")

if st.session_state.current_role == "Admin":
  tab_att, tab_dir, tab_pay = st.tabs([
      "📅 Daily Attendance and Shift Logging",
      "👥 Workforce Directory",
      "💰 Payroll & Payslips",
  ])
else:
  tab_att, = st.tabs(["📅 Daily Attendance and Shift Logging"])
  st.caption("Kitchen Staff Mode: Daily logs enabled. Financial modules hidden.")

# =========================================================
# TAB 1: DAILY ATTENDANCE AND SHIFT LOGGING
# =========================================================
with tab_att:
  st.subheader("Daily Attendance and Shift Logging")

  staff_df = load_staff_data()
  if staff_df.empty or "Name" not in staff_df.columns:
    st.warning("No staff members registered in the database yet.")
  else:
    with st.expander("⚡ Batch Action: Mark All Active Staff 'Present' Today"):
      batch_col1, batch_col2 = st.columns([2, 1])
      with batch_col1:
        batch_date = st.date_input(
            "Batch Attendance Date",
            value=date.today(),
            key="batch_att_date",
        )
      with batch_col2:
        st.write("")
        st.write("")
        if st.button("Mark All Present", type="primary"):
          current_att = load_attendance_data()
          new_batch_rows = []
          for _, emp in staff_df.iterrows():
            new_batch_rows.append({
                "Date": str(batch_date),
                "Staff ID": emp["Staff ID"],
                "Name": emp["Name"],
                "Station": emp.get("Role", "Semi-Cooked Processing"),
                "Status": "Present",
                "Overtime Hours": 0.0,
                "Notes": "Auto Batch Check-In",
            })
          batch_df = pd.DataFrame(new_batch_rows)
          updated_att = (
              pd.concat([current_att, batch_df], ignore_index=True)
              if not current_att.empty
              else batch_df
          )
          conn.update(worksheet="Attendance", data=updated_att)
          st.cache_data.clear()
          st.success(
              f"Logged Present for all {len(staff_df)} members on"
              f" {batch_date}!"
          )
          st.rerun()

    st.markdown("#### Individual Shift Entry")
    with st.form("single_attendance_form", clear_on_submit=True):
      c1, c2, c3 = st.columns(3)
      with c1:
        shift_date = st.date_input("Shift Date", value=date.today())
      with c2:
        selected_emp = st.selectbox("Staff Member", options=staff_df["Name"])
      with c3:
        station_options = [
            "Semi-Cooked Processing",
            "Packaging & Sealing",
            "Fuvahmulah Distribution",
            "Kitchen Cleaning & Prep",
        ]
        selected_station = st.selectbox(
            "Production Station", options=station_options
        )

      c4, c5 = st.columns(2)
      with c4:
        status_options = [
            "Present",
            "Half Day",
            "Annual Leave",
            "Sick Leave",
            "Family Leave",
            "Unexcused Absent",
        ]
        status = st.selectbox("Duty Status", options=status_options)
      with c5:
        ot_hours = st.number_input(
            "Overtime Worked (Hours)",
            min_value=0.0,
            max_value=12.0,
            value=0.0,
            step=0.5,
        )

      shift_notes = st.text_input("Shift Operational Notes")
      submit_shift = st.form_submit_button(
          "💾 Record Shift Entry", type="primary"
      )

      if submit_shift:
        current_att = load_attendance_data()
        emp_id = (
            staff_df[staff_df["Name"] == selected_emp]["Staff ID"].values[0]
            if not staff_df[staff_df["Name"] == selected_emp].empty
            else "ZF-000"
        )

        new_entry = pd.DataFrame([{
            "Date": str(shift_date),
            "Staff ID": str(emp_id),
            "Name": str(selected_emp),
            "Station": str(selected_station),
            "Status": str(status),
            "Overtime Hours": float(ot_hours),
            "Notes": str(shift_notes),
        }])

        updated_att = (
            pd.concat([current_att, new_entry], ignore_index=True)
            if not current_att.empty
            else new_entry
        )
        conn.update(worksheet="Attendance", data=updated_att)
        st.cache_data.clear()
        st.success(f"Shift recorded for {selected_emp} on {shift_date}.")
        st.rerun()

  st.divider()

  st.subheader("Manage Logged Shifts")
  att_records = load_attendance_data()
  if not att_records.empty:
    valid_att = att_records.dropna(subset=["Date", "Name"]).copy()
    if not valid_att.empty:
      st.dataframe(valid_att, use_container_width=True, hide_index=True)

      shift_options = {
          f"{row['Date']} | {row['Name']} ({row['Status']}) @ {row['Station']} -"
          f" {row['Overtime Hours']}h OT": idx
          for idx, row in valid_att.iterrows()
      }

      del_col1, del_col2 = st.columns([3, 1])
      with del_col1:
        selected_shift_to_delete = st.selectbox(
            "Select record to remove:",
            options=list(shift_options.keys()),
            key="delete_shift_select",
        )
      with del_col2:
        st.write("")
        st.write("")
        if st.button("🗑️ Delete Shift", type="secondary"):
          row_to_drop = shift_options[selected_shift_to_delete]
          remaining_att = att_records.drop(index=row_to_drop).reset_index(
              drop=True
          )

          if remaining_att.empty:
            remaining_att = pd.DataFrame(
                columns=[
                    "Date",
                    "Staff ID",
                    "Name",
                    "Station",
                    "Status",
                    "Overtime Hours",
                    "Notes",
                ]
            )

          conn.update(worksheet="Attendance", data=remaining_att)
          st.cache_data.clear()
          st.success("Record deleted successfully.")
          st.rerun()

# =========================================================
# TAB 2: WORKFORCE DIRECTORY (ADMIN ONLY)
# =========================================================
if st.session_state.current_role == "Admin":
  with tab_dir:
    st.subheader("Workforce Management & Job Roles")
    dir_col1, dir_col2 = st.columns([1, 1])

    with dir_col1:
      st.markdown("#### Add New Team Member")
      staff_df = load_staff_data()

      next_id_num = 1
      if not staff_df.empty and "Staff ID" in staff_df.columns:
        existing_ids = staff_df["Staff ID"].dropna().astype(str).tolist()
        numeric_ids = [
            int(x.replace("ZF-", ""))
            for x in existing_ids
            if x.startswith("ZF-") and x.replace("ZF-", "").isdigit()
        ]
        if numeric_ids:
          next_id_num = max(numeric_ids) + 1
      auto_id = f"ZF-{next_id_num:03d}"

      with st.form("new_employee_form", clear_on_submit=True):
        st.text_input("Assigned Staff ID", value=auto_id, disabled=True)
        new_name = st.text_input("Full Legal Name")
        new_role = st.selectbox(
            "Primary Kitchen Assignment",
            options=[
                "Semi-Cooked Processing",
                "Packaging & Quality",
                "Fuvahmulah Delivery & Sales",
                "Kitchen Supervision",
            ],
        )
        new_salary = st.number_input(
            "Base Monthly Salary (MVR)",
            min_value=1000.0,
            value=5000.0,
            step=250.0,
        )
        new_days = st.number_input(
            "Standard Work Days / Month", min_value=15, max_value=31, value=26
        )
        new_bank = st.text_input(
            "BML Account Number (Optional)",
            placeholder="e.g. 7730000123456",
        )
        new_pension = st.selectbox(
            "Enroll in Maldives Retirement Pension (MRPS)?",
            options=["No", "Yes"],
        )

        submit_new_staff = st.form_submit_button(
            "💾 Register Staff Member", type="primary"
        )

        if submit_new_staff:
          if not new_name.strip():
            st.error("Employee name is required.")
          else:
            new_row = pd.DataFrame([{
                "Staff ID": auto_id,
                "Name": new_name.strip(),
                "Role": new_role,
                "Base Salary (MVR)": float(new_salary),
                "Standard Monthly Days": int(new_days),
                "Bank Account": str(new_bank).strip(),
                "Pension Enrolled": str(new_pension),
            }])
            updated_staff = (
                pd.concat([staff_df, new_row], ignore_index=True)
                if not staff_df.empty
                else new_row
            )
            conn.update(worksheet="Staff", data=updated_staff)
            st.cache_data.clear()
            st.success(f"Registered {new_name} ({auto_id}) successfully!")
            st.rerun()

    with dir_col2:
      st.markdown("#### Active Team Directory")
      staff_df = load_staff_data()
      if not staff_df.empty:
        st.dataframe(staff_df, use_container_width=True, hide_index=True)

        st.markdown("#### Remove Staff Member")
        staff_to_delete = st.selectbox(
            "Select employee to remove:",
            options=staff_df["Name"].tolist(),
            key="delete_staff_box",
        )
        if st.button("⚠️ Delete Member from Cloud", type="secondary"):
          remaining = staff_df[
              staff_df["Name"] != staff_to_delete
          ].reset_index(drop=True)
          if remaining.empty:
            remaining = pd.DataFrame(
                columns=[
                    "Staff ID",
                    "Name",
                    "Role",
                    "Base Salary (MVR)",
                    "Standard Monthly Days",
                    "Bank Account",
                    "Pension Enrolled",
                ]
            )
          conn.update(worksheet="Staff", data=remaining)
          st.cache_data.clear()
          st.warning(f"Removed {staff_to_delete} from Zelqon Foods database.")
          st.rerun()
      else:
        st.info("Directory is currently empty.")

# =========================================================
# TAB 3: PAYROLL & COMPLIANCE (ADMIN ONLY)
# =========================================================
if st.session_state.current_role == "Admin":
  with tab_pay:
    st.subheader("Maldives Compliant Payroll Calculation")

    staff_df = load_staff_data()
    att_df = load_attendance_data()

    if staff_df.empty:
      st.info("Please register team members in the Workforce Directory first.")
    else:
      p_col1, p_col2, p_col3 = st.columns(3)
      with p_col1:
        months_list = [
            "January",
            "February",
            "March",
            "April",
            "May",
            "June",
            "July",
            "August",
            "September",
            "October",
            "November",
            "December",
        ]
        active_m_idx = datetime.now().month - 1
        selected_month_name = st.selectbox(
            "Payroll Month", options=months_list, index=active_m_idx
        )
        selected_month_num = months_list.index(selected_month_name) + 1
      with p_col2:
        selected_year = st.selectbox(
            "Payroll Year", options=[2025, 2026, 2027], index=1
        )
      with p_col3:
        st.write("")
        st.write("")
        include_ramazan = st.checkbox(
            "Apply Legal Ramazan Allowance (MVR 3,000)", value=False
        )

      period_label = f"{selected_month_name} {selected_year}"

      if not att_df.empty and "Date" in att_df.columns:
        att_df["Parsed_Date"] = pd.to_datetime(
            att_df["Date"], errors="coerce"
        )
        period_att = att_df[
            (att_df["Parsed_Date"].dt.month == selected_month_num)
            & (att_df["Parsed_Date"].dt.year == selected_year)
        ]
      else:
        period_att = pd.DataFrame()

      st.divider()
      st.markdown("#### Monthly Adjustments (Advances & Production Bonuses)")
      st.caption(
          "Enter one-off island advances or kitchen bonuses for this month."
      )

      advances_dict = {}
      bonuses_dict = {}

      for idx, emp in staff_df.iterrows():
        emp_name = emp["Name"]
        with st.expander(f"Adjustments: {emp_name}"):
          adv_val = st.number_input(
              f"Salary Advance Deductions (MVR) - {emp_name}",
              min_value=0.0,
              value=0.0,
              step=100.0,
              key=f"adv_{emp['Staff ID']}",
          )
          bon_val = st.number_input(
              f"Production / Food Allowance (MVR) - {emp_name}",
              min_value=0.0,
              value=0.0,
              step=100.0,
              key=f"bon_{emp['Staff ID']}",
          )
          advances_dict[emp_name] = adv_val
          bonuses_dict[emp_name] = bon_val

      payroll_list = []
      bml_transfer_list = []

      for _, emp in staff_df.iterrows():
        name = emp["Name"]
        staff_id = emp["Staff ID"]
        role = emp.get("Role", "Kitchen Operations")
        bank_acc = emp.get("Bank Account", "")
        base_sal = float(emp["Base Salary (MVR)"])
        std_days = (
            float(emp["Standard Monthly Days"])
            if emp["Standard Monthly Days"]
            else 26.0
        )
        is_pension = str(emp.get("Pension Enrolled", "No")).strip().lower() in [
            "yes",
            "true",
            "1",
        ]

        daily_rate = base_sal / std_days
        hourly_rate = daily_rate / 8.0

        present_count = 0.0
        leave_count = 0.0
        absent_count = 0.0
        ot_hours_total = 0.0

        if not period_att.empty:
          records = period_att[period_att["Name"] == name]
          for _, row in records.iterrows():
            st_val = str(row["Status"])
            if st_val == "Present":
              present_count += 1.0
            elif st_val == "Half Day":
              present_count += 0.5
              absent_count += 0.5
            elif st_val in ["Annual Leave", "Sick Leave", "Family Leave"]:
              leave_count += 1.0
              present_count += 1.0
            elif st_val == "Unexcused Absent":
              absent_count += 1.0

            try:
              ot_hours_total += float(row["Overtime Hours"])
            except (ValueError, TypeError):
              pass

        ot_payout = ot_hours_total * hourly_rate * 1.25
        absence_deduction = absent_count * daily_rate

        ramazan_amt = 3000.0 if include_ramazan else 0.0
        extra_allowance = bonuses_dict.get(name, 0.0)
        advance_deduction = advances_dict.get(name, 0.0)

        pension_ee = (base_sal * 0.07) if is_pension else 0.0
        pension_er = (base_sal * 0.07) if is_pension else 0.0

        net_payout = (
            base_sal
            + ot_payout
            + ramazan_amt
            + extra_allowance
            - absence_deduction
            - advance_deduction
            - pension_ee
        )

        payroll_list.append({
            "Staff ID": staff_id,
            "Name": name,
            "Role": role,
            "Bank Account": bank_acc,
            "Base Salary": base_sal,
            "Present": present_count,
            "Absences": absent_count,
            "OT (Hrs)": ot_hours_total,
            "OT Pay": ot_payout,
            "Ramazan": ramazan_amt,
            "Bonuses": extra_allowance,
            "Absence Deduct": absence_deduction,
            "Advances": advance_deduction,
            "Pension (7%)": pension_ee,
            "Net Payout (MVR)": net_payout,
            "Employer Pension": pension_er,
        })

        bml_transfer_list.append({
            "Staff ID": staff_id,
            "Beneficiary Name": name,
            "Account Number": bank_acc if bank_acc else "CASH_PAYMENT",
            "Disbursement Amount (MVR)": round(net_payout, 2),
            "Payment Reference": f"Salary {period_label}",
        })

      payroll_df = pd.DataFrame(payroll_list)

      st.divider()
      st.markdown(f"#### Complete Payroll Ledger — {period_label}")
      st.dataframe(
          payroll_df.style.format({
              "Base Salary": "{:,.2f}",
              "Present": "{:.1f}",
              "Absences": "{:.1f}",
              "OT (Hrs)": "{:.1f}",
              "OT Pay": "{:,.2f}",
              "Ramazan": "{:,.2f}",
              "Bonuses": "{:,.2f}",
              "Absence Deduct": "{:,.2f}",
              "Advances": "{:,.2f}",
              "Pension (7%)": "{:,.2f}",
              "Net Payout (MVR)": "{:,.2f}",
              "Employer Pension": "{:,.2f}",
          }),
          use_container_width=True,
          hide_index=True,
      )

      st.markdown("#### Bank / BML Bulk Transfer Export")
      bml_df = pd.DataFrame(bml_transfer_list)
      bml_csv = bml_df.to_csv(index=False).encode("utf-8")
      st.download_button(
          label=f"📥 Download Bank Transfer File ({period_label} CSV)",
          data=bml_csv,
          file_name=f"Zelqon_Bank_Transfer_{period_label.replace(' ', '_')}.csv",
          mime="text/csv",
          type="secondary",
      )

      st.divider()

      st.subheader("Individual Monthly Payslip Generator")
      chosen_person = st.selectbox(
          "Select Employee to Export Payslip:",
          options=payroll_df["Name"].tolist(),
      )

      target = payroll_df[payroll_df["Name"] == chosen_person].iloc[0]

      c_met1, c_met2, c_met3, c_met4 = st.columns(4)
      c_met1.metric("Base Pay", f"MVR {target['Base Salary']:,.2f}")
      c_met2.metric(
          "OT + Allowances",
          f"MVR {(target['OT Pay'] + target['Ramazan'] + target['Bonuses']):,.2f}",
      )
      c_met3.metric(
          "Total Deductions",
          f"MVR {(target['Absence Deduct'] + target['Advances'] + target['Pension (7%)']):,.2f}",
      )
      c_met4.metric("Net Salary", f"MVR {target['Net Payout (MVR)']:,.2f}")

      payslip_pdf = generate_payslip_bytes(
          emp_name=target["Name"],
          staff_id=target["Staff ID"],
          role=target["Role"],
          bank_acc=target["Bank Account"],
          period_str=period_label,
          base_salary=target["Base Salary"],
          days_present=target["Present"],
          days_absent=target["Absences"],
          leave_days=0.0,
          ot_hours=target["OT (Hrs)"],
          ot_pay=target["OT Pay"],
          ramazan_allowance=target["Ramazan"],
          other_allowances=target["Bonuses"],
          absence_deduction=target["Absence Deduct"],
          salary_advance=target["Advances"],
          pension_employee=target["Pension (7%)"],
          pension_employer=target["Employer Pension"],
          net_pay=target["Net Payout (MVR)"],
      )

      pdf_filename = f"Payslip_{target['Name'].replace(' ', '_')}_{period_label.replace(' ', '_')}.pdf"

      st.download_button(
          label=f"📥 Download {target['Name']}'s Official Payslip (PDF)",
          data=payslip_pdf,
          file_name=pdf_filename,
          mime="application/pdf",
          type="primary",
      )
