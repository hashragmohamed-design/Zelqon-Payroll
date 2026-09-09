from datetime import date, datetime
import io
from fpdf import FPDF
import pandas as pd
import streamlit as st
from streamlit_gsheets import GSheetsConnection

# --- Page Configuration ---
st.set_page_config(
    page_title="Zelqon Foods | HR & Payroll", page_icon="📋", layout="wide"
)

st.title("Zelqon Foods HR & Payroll System")
st.caption("Fuvahmulah, Maldives | Cloud Persistence via Google Sheets")

# --- Google Sheets Connection ---
conn = st.connection("gsheets", type=GSheetsConnection)


def load_staff_data():
  try:
    df = conn.read(worksheet="Staff", ttl=0)
    if df is None or df.empty:
      return pd.DataFrame(
          columns=[
              "Staff ID",
              "Name",
              "Base Salary (MVR)",
              "Standard Monthly Days",
          ]
      )
    for col in [
        "Staff ID",
        "Name",
        "Base Salary (MVR)",
        "Standard Monthly Days",
    ]:
      if col not in df.columns:
        df[col] = ""
    return df.dropna(how="all")
  except Exception:
    return pd.DataFrame(
        columns=[
            "Staff ID",
            "Name",
            "Base Salary (MVR)",
            "Standard Monthly Days",
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
              "Status",
              "Overtime Hours",
              "Notes",
          ]
      )
    for col in [
        "Date",
        "Staff ID",
        "Name",
        "Status",
        "Overtime Hours",
        "Notes",
    ]:
      if col not in df.columns:
        df[col] = ""
    return df.dropna(how="all")
  except Exception:
    return pd.DataFrame(
        columns=[
            "Date",
            "Staff ID",
            "Name",
            "Status",
            "Overtime Hours",
            "Notes",
        ]
    )


# --- Offline CSV Backup (Sidebar) ---
with st.sidebar:
  st.title("Zelqon Foods")
  st.caption("Fuvahmulah, Maldives")
  st.divider()
  st.subheader("💾 Cloud Data Backup")
  st.caption("Export offline copies of your Google Sheets database.")

  staff_backup_df = load_staff_data()
  if not staff_backup_df.empty:
    csv_staff = staff_backup_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Download Staff (CSV)",
        data=csv_staff,
        file_name=f"Zelqon_Staff_Backup_{date.today()}.csv",
        mime="text/csv",
        use_container_width=True,
    )

  att_backup_df = load_attendance_data()
  if not att_backup_df.empty:
    csv_att = att_backup_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Download Attendance (CSV)",
        data=csv_att,
        file_name=f"Zelqon_Attendance_Backup_{date.today()}.csv",
        mime="text/csv",
        use_container_width=True,
    )


# --- Payslip PDF Generator ---
class PayslipPDF(FPDF):

  def header(self):
    self.set_font("Helvetica", "B", 15)
    self.cell(0, 8, "ZELQON FOODS", align="C", new_x="LMARGIN", new_y="NEXT")
    self.set_font("Helvetica", "", 9)
    self.cell(
        0,
        5,
        "Fuvahmulah City, Republic of Maldives",
        align="C",
        new_x="LMARGIN",
        new_y="NEXT",
    )
    self.cell(
        0,
        5,
        "CONFIDENTIAL EMPLOYEE PAYSLIP",
        align="C",
        new_x="LMARGIN",
        new_y="NEXT",
    )
    self.line(10, 27, 200, 27)
    self.ln(6)

  def footer(self):
    self.set_y(-25)
    self.set_font("Helvetica", "I", 8)
    self.cell(
        0,
        5,
        "This is an official computer-generated payroll record for Zelqon"
        " Foods.",
        align="C",
        new_x="LMARGIN",
        new_y="NEXT",
    )


def generate_payslip_bytes(
    emp_name,
    staff_id,
    period_str,
    base_salary,
    days_present,
    days_absent,
    ot_hours,
    ot_pay,
    deductions,
    net_pay,
):
  pdf = PayslipPDF()
  pdf.add_page()
  pdf.set_auto_page_break(auto=True, margin=15)

  # Employee Details Box
  pdf.set_fill_color(245, 245, 245)
  pdf.rect(10, 32, 190, 22, "F")
  pdf.set_xy(12, 34)
  pdf.set_font("Helvetica", "B", 10)
  pdf.cell(30, 5, "Employee Name:")
  pdf.set_font("Helvetica", "", 10)
  pdf.cell(65, 5, str(emp_name))
  pdf.set_font("Helvetica", "B", 10)
  pdf.cell(25, 5, "Staff ID:")
  pdf.set_font("Helvetica", "", 10)
  pdf.cell(70, 5, str(staff_id), new_x="LMARGIN", new_y="NEXT")

  pdf.set_x(12)
  pdf.set_font("Helvetica", "B", 10)
  pdf.cell(30, 5, "Pay Period:")
  pdf.set_font("Helvetica", "", 10)
  pdf.cell(65, 5, str(period_str))
  pdf.set_font("Helvetica", "B", 10)
  pdf.cell(25, 5, "Currency:")
  pdf.set_font("Helvetica", "", 10)
  pdf.cell(70, 5, "Maldivian Rufiyaa (MVR)", new_x="LMARGIN", new_y="NEXT")

  pdf.ln(10)

  # Attendance Breakdown
  pdf.set_font("Helvetica", "B", 11)
  pdf.cell(0, 6, "1. Attendance Summary", new_x="LMARGIN", new_y="NEXT")
  pdf.set_font("Helvetica", "", 10)
  pdf.cell(
      0,
      5,
      f"Days Worked / Present: {days_present:.1f} days",
      new_x="LMARGIN",
      new_y="NEXT",
  )
  pdf.cell(
      0,
      5,
      f"Unpaid Absences: {days_absent:.1f} days",
      new_x="LMARGIN",
      new_y="NEXT",
  )
  pdf.cell(
      0,
      5,
      f"Recorded Overtime: {ot_hours:.1f} hours",
      new_x="LMARGIN",
      new_y="NEXT",
  )

  pdf.ln(6)

  # Financial Table Header
  pdf.set_font("Helvetica", "B", 11)
  pdf.cell(0, 6, "2. Earnings & Deductions", new_x="LMARGIN", new_y="NEXT")
  pdf.set_font("Helvetica", "B", 10)
  pdf.set_fill_color(230, 230, 230)
  pdf.cell(130, 7, "Description", border=1, fill=True)
  pdf.cell(60, 7, "Amount (MVR)", border=1, fill=True, align="R")
  pdf.ln(7)

  # Financial Rows
  pdf.set_font("Helvetica", "", 10)
  pdf.cell(130, 7, "Base Monthly Salary", border=1)
  pdf.cell(60, 7, f"{base_salary:,.2f}", border=1, align="R")
  pdf.ln(7)

  pdf.cell(130, 7, f"Overtime Allowance ({ot_hours:.1f} hrs @ 1.25x)", border=1)
  pdf.cell(60, 7, f"+{ot_pay:,.2f}", border=1, align="R")
  pdf.ln(7)

  pdf.cell(130, 7, f"Unpaid Absence Deductions ({days_absent:.1f} days)", border=1)
  pdf.cell(60, 7, f"-{deductions:,.2f}", border=1, align="R")
  pdf.ln(7)

  # Net Total
  pdf.set_font("Helvetica", "B", 11)
  pdf.set_fill_color(240, 240, 240)
  pdf.cell(130, 8, "NET TAKE-HOME PAYOUT", border=1, fill=True)
  pdf.cell(60, 8, f"MVR {net_pay:,.2f}", border=1, fill=True, align="R")
  pdf.ln(18)

  # Signature Lines
  pdf.set_font("Helvetica", "", 9)
  pdf.cell(90, 4, "_____________________________", new_x="NONE")
  pdf.cell(10, 4, "")
  pdf.cell(90, 4, "_____________________________", new_x="LMARGIN", new_y="NEXT")

  pdf.cell(90, 4, "Employer / Manager Signature", new_x="NONE")
  pdf.cell(10, 4, "")
  pdf.cell(
      90, 4, "Employee Signature (Acknowledged)", new_x="LMARGIN", new_y="NEXT"
  )

  return bytes(pdf.output())


# --- Navigation Tabs ---
tab_att, tab_dir, tab_pay = st.tabs(
    ["📅 Attendance Register", "👥 Workforce Directory", "💰 Payroll & Payslips"]
)

# ==========================================
# TAB 1: ATTENDANCE REGISTER
# ==========================================
with tab_att:
  st.subheader("Daily Attendance & Shift Entry")

  staff_df = load_staff_data()

  if staff_df.empty or "Name" not in staff_df.columns:
    st.warning(
        "Please register at least one employee in the 'Workforce Directory' tab"
        " first."
    )
  else:
    staff_names = staff_df["Name"].dropna().tolist()

    with st.form("attendance_form", clear_on_submit=True):
      col_date, col_staff = st.columns(2)
      with col_date:
        shift_date = st.date_input("Shift Date", value=date.today())
      with col_staff:
        selected_emp = st.selectbox("Staff Member", options=staff_names)

      col_status, col_ot = st.columns(2)
      with col_status:
        status = st.selectbox(
            "Shift Status",
            options=["Present", "Half Day", "Absent", "Paid Leave"],
        )
      with col_ot:
        ot_hours = st.number_input(
            "Overtime Hours", min_value=0.0, max_value=12.0, value=0.0, step=0.5
        )

      notes = st.text_input("Shift Notes (Optional)")
      submit_shift = st.form_submit_button(
          "💾 Save Shift to Google Sheets", type="primary"
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
            "Status": str(status),
            "Overtime Hours": float(ot_hours),
            "Notes": str(notes),
        }])

        updated_att = (
            pd.concat([current_att, new_entry], ignore_index=True)
            if not current_att.empty
            else new_entry
        )

        conn.update(worksheet="Attendance", data=updated_att)
        st.cache_data.clear()
        st.success(
            f"Logged shift for {selected_emp} on {shift_date} successfully!"
        )
        st.rerun()

  st.divider()

  # --- Manage & Delete Logged Shifts Section ---
  st.subheader("Manage Logged Shifts")
  att_records = load_attendance_data()

  if not att_records.empty:
    valid_att = att_records.dropna(subset=["Date", "Name"]).copy()

    if not valid_att.empty:
      st.dataframe(valid_att, use_container_width=True, hide_index=True)

      shift_options = {
          f"{row['Date']} | {row['Name']} ({row['Status']}) - {row['Overtime Hours']}h OT": idx
          for idx, row in valid_att.iterrows()
      }

      col_select, col_action = st.columns([3, 1])
      with col_select:
        shift_to_delete = st.selectbox(
            "Select shift record to remove:",
            options=list(shift_options.keys()),
            key="delete_shift_box",
        )
      with col_action:
        st.write("")
        st.write("")
        if st.button("🗑️ Delete Shift", type="secondary"):
          row_to_drop = shift_options[shift_to_delete]
          remaining_att = att_records.drop(index=row_to_drop).reset_index(
              drop=True
          )

          if remaining_att.empty:
            remaining_att = pd.DataFrame(
                columns=[
                    "Date",
                    "Staff ID",
                    "Name",
                    "Status",
                    "Overtime Hours",
                    "Notes",
                ]
            )

          conn.update(worksheet="Attendance", data=remaining_att)
          st.cache_data.clear()
          st.success("Shift record successfully deleted from Google Sheets.")
          st.rerun()
    else:
      st.info("No recorded shifts found in database.")
  else:
    st.info("No attendance records logged yet.")


# ==========================================
# TAB 2: WORKFORCE DIRECTORY
# ==========================================
with tab_dir:
  st.subheader("Staff Member Registration")

  col_new_staff, col_curr_staff = st.columns([1, 1])

  with col_new_staff:
    st.markdown("#### Register New Staff")
    staff_df = load_staff_data()

    next_num = 1
    if not staff_df.empty and "Staff ID" in staff_df.columns:
      existing_ids = staff_df["Staff ID"].dropna().astype(str).tolist()
      id_numbers = [
          int(x.replace("ZF-", ""))
          for x in existing_ids
          if x.startswith("ZF-") and x.replace("ZF-", "").isdigit()
      ]
      if id_numbers:
        next_num = max(id_numbers) + 1
    generated_id = f"ZF-{next_num:03d}"

    with st.form("register_staff_form", clear_on_submit=True):
      st.text_input("Assigned Staff ID", value=generated_id, disabled=True)
      staff_name = st.text_input("Full Legal Name")
      base_salary = st.number_input(
          "Monthly Base Salary (MVR)",
          min_value=1000.0,
          value=4500.0,
          step=250.0,
      )
      std_days = st.number_input(
          "Standard Monthly Work Days", min_value=15, max_value=31, value=26
      )

      save_staff = st.form_submit_button(
          "💾 Save Member to Cloud", type="primary"
      )

      if save_staff:
        if not staff_name.strip():
          st.error("Please enter a valid staff name.")
        else:
          new_staff_row = pd.DataFrame([{
              "Staff ID": generated_id,
              "Name": staff_name.strip(),
              "Base Salary (MVR)": float(base_salary),
              "Standard Monthly Days": int(std_days),
          }])

          updated_directory = (
              pd.concat([staff_df, new_staff_row], ignore_index=True)
              if not staff_df.empty
              else new_staff_row
          )

          conn.update(worksheet="Staff", data=updated_directory)
          st.cache_data.clear()
          st.success(
              f"Added {staff_name.strip()} ({generated_id}) to Zelqon Foods"
              " Directory!"
          )
          st.rerun()

  with col_curr_staff:
    st.markdown("#### Registered Team")
    staff_df = load_staff_data()
    if not staff_df.empty:
      st.dataframe(staff_df, use_container_width=True, hide_index=True)

      st.markdown("#### Remove Staff Member")
      staff_to_remove = st.selectbox(
          "Select employee to remove:",
          options=staff_df["Name"].tolist(),
          key="remove_staff_select",
      )

      if st.button("⚠️ Execute Cloud Removal", type="secondary"):
        remaining_staff = staff_df[
            staff_df["Name"] != staff_to_remove
        ].reset_index(drop=True)
        if remaining_staff.empty:
          remaining_staff = pd.DataFrame(
              columns=[
                  "Staff ID",
                  "Name",
                  "Base Salary (MVR)",
                  "Standard Monthly Days",
              ]
          )

        conn.update(worksheet="Staff", data=remaining_staff)
        st.cache_data.clear()
        st.warning(f"Removed {staff_to_remove} from Google Sheets.")
        st.rerun()
    else:
      st.info("Workforce directory is currently empty.")


# ==========================================
# TAB 3: PAYROLL & PAYSLIPS
# ==========================================
with tab_pay:
  st.subheader("Payroll Calculation & Payslip Export")

  staff_df = load_staff_data()
  attendance_df = load_attendance_data()

  if staff_df.empty:
    st.info("Add team members in Workforce Directory to view payroll.")
  else:
    col_m, col_y = st.columns(2)
    with col_m:
      current_month = datetime.now().month
      month_names = [
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
      selected_month_name = st.selectbox(
          "Payroll Month", options=month_names, index=current_month - 1
      )
      selected_month_num = month_names.index(selected_month_name) + 1
    with col_y:
      selected_year = st.selectbox(
          "Payroll Year", options=[2025, 2026, 2027], index=1
      )

    period_display = f"{selected_month_name} {selected_year}"

    if not attendance_df.empty and "Date" in attendance_df.columns:
      attendance_df["Parsed_Date"] = pd.to_datetime(
          attendance_df["Date"], errors="coerce"
      )
      period_attendance = attendance_df[
          (attendance_df["Parsed_Date"].dt.month == selected_month_num)
          & (attendance_df["Parsed_Date"].dt.year == selected_year)
      ]
    else:
      period_attendance = pd.DataFrame()

    payroll_records = []

    for _, emp in staff_df.iterrows():
      emp_name = emp["Name"]
      emp_id = emp["Staff ID"]
      base_sal = float(emp["Base Salary (MVR)"])
      std_days = (
          float(emp["Standard Monthly Days"])
          if emp["Standard Monthly Days"]
          else 26.0
      )

      daily_wage = base_sal / std_days
      hourly_rate = daily_wage / 8.0

      present_count = 0.0
      absent_count = 0.0
      ot_hours_total = 0.0

      if not period_attendance.empty:
        emp_records = period_attendance[period_attendance["Name"] == emp_name]
        for _, rec in emp_records.iterrows():
          st_val = str(rec["Status"])
          if st_val == "Present":
            present_count += 1.0
          elif st_val == "Half Day":
            present_count += 0.5
            absent_count += 0.5
          elif st_val == "Absent":
            absent_count += 1.0
          elif st_val == "Paid Leave":
            present_count += 1.0

          try:
            ot_hours_total += float(rec["Overtime Hours"])
          except (ValueError, TypeError):
            pass

      ot_payout = ot_hours_total * hourly_rate * 1.25
      absence_deduction = absent_count * daily_wage
      net_payout = base_sal - absence_deduction + ot_payout

      payroll_records.append({
          "Staff ID": emp_id,
          "Name": emp_name,
          "Base Salary": base_sal,
          "Days Present": present_count,
          "Days Absent": absent_count,
          "OT Hours": ot_hours_total,
          "OT Pay (MVR)": ot_payout,
          "Deductions (MVR)": absence_deduction,
          "Net Payout (MVR)": net_payout,
      })

    payroll_summary_df = pd.DataFrame(payroll_records)

    st.markdown(f"#### Disbursement Overview — {period_display}")
    st.dataframe(
        payroll_summary_df.style.format({
            "Base Salary": "{:,.2f}",
            "Days Present": "{:.1f}",
            "Days Absent": "{:.1f}",
            "OT Hours": "{:.1f}",
            "OT Pay (MVR)": "{:,.2f}",
            "Deductions (MVR)": "{:,.2f}",
            "Net Payout (MVR)": "{:,.2f}",
        }),
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    # --- Payslip Download Section ---
    st.subheader("Individual Monthly Payslip Generator")
    chosen_employee = st.selectbox(
        "Select Employee to Export Payslip:",
        options=payroll_summary_df["Name"].tolist(),
    )

    target_emp_data = payroll_summary_df[
        payroll_summary_df["Name"] == chosen_employee
    ].iloc[0]

    stat_col1, stat_col2, stat_col3 = st.columns(3)
    stat_col1.metric("Base Pay", f"MVR {target_emp_data['Base Salary']:,.2f}")
    stat_col2.metric("Overtime Pay", f"MVR {target_emp_data['OT Pay (MVR)']:,.2f}")
    stat_col3.metric(
        "Net Take-Home", f"MVR {target_emp_data['Net Payout (MVR)']:,.2f}"
    )

    pdf_data = generate_payslip_bytes(
        emp_name=target_emp_data["Name"],
        staff_id=target_emp_data["Staff ID"],
        period_str=period_display,
        base_salary=target_emp_data["Base Salary"],
        days_present=target_emp_data["Days Present"],
        days_absent=target_emp_data["Days Absent"],
        ot_hours=target_emp_data["OT Hours"],
        ot_pay=target_emp_data["OT Pay (MVR)"],
        deductions=target_emp_data["Deductions (MVR)"],
        net_pay=target_emp_data["Net Payout (MVR)"],
    )

    clean_filename = (
        f"Payslip_{target_emp_data['Name'].replace(' ', '_')}_{period_display.replace(' ', '_')}.pdf"
    )

    st.download_button(
        label=f"📥 Download {target_emp_data['Name']}'s Payslip (PDF)",
        data=pdf_data,
        file_name=clean_filename,
        mime="application/pdf",
        type="primary",
    )
