import datetime
from fpdf import FPDF
import pandas as pd
import streamlit as st
from streamlit_gsheets import GSheetsConnection

st.set_page_config(
    page_title="Zelqon Foods | Operations & Payroll",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# --- PROFESSIONAL STYLING ---
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; }
    [data-testid="stAppViewContainer"] { background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%); color: #0f172a; }
    [data-testid="stHeader"] { background-color: rgba(248, 250, 252, 0.85); backdrop-filter: blur(8px); }
    .brand-hero {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        color: #ffffff; padding: 24px 28px; border-radius: 14px; margin-bottom: 24px;
        border: 1px solid #334155; box-shadow: 0 4px 12px rgba(15, 23, 42, 0.08);
    }
    .brand-hero h1 { color: #ffffff !important; font-size: 1.65rem; font-weight: 700; margin: 0; }
    .brand-hero p { color: #94a3b8 !important; font-size: 0.88rem; margin: 4px 0 0 0; }
    [data-testid="stForm"] { background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 22px; }
    .stButton>button {
        background: linear-gradient(135deg, #0d9488 0%, #0f766e 100%);
        color: #ffffff !important; font-weight: 600; border-radius: 8px; border: none; padding: 0.55rem 1.4rem;
    }
    [data-testid="stMetric"] { background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 16px 20px; }
    </style>
""",
    unsafe_allow_html=True,
)

# --- GOOGLE SHEETS LIVE CONNECTION ---
conn = st.connection("gsheets", type=GSheetsConnection)


def get_staff_data():
  try:
    df = conn.read(worksheet="Staff", ttl=0)
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


def get_attendance_data():
  try:
    df = conn.read(worksheet="Attendance", ttl=0)
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


# --- AUTHENTICATION ---
def check_password():
  if "password_correct" not in st.session_state:
    st.session_state.password_correct = False
  if st.session_state.password_correct:
    return True

  col_l, col_m, col_r = st.columns([1, 1.8, 1])
  with col_m:
    st.markdown("<br><br>", unsafe_allow_html=True)
    with st.form("login_form"):
      st.markdown("### 🔒 Zelqon Portal Access")
      pwd = st.text_input("Access Password", type="password")
      submit = st.form_submit_button("Authenticate")
      if submit:
        if pwd == "zelqon2026":
          st.session_state.password_correct = True
          st.rerun()
        else:
          st.error("Invalid credentials.")
  return False


if not check_password():
  st.stop()

# --- LOAD CLOUD DATA ---
staff_df = get_staff_data()
attendance_df = get_attendance_data()

# --- HEADER ---
st.markdown(
    """
    <div class="brand-hero">
        <h1>ZELQON FOODS</h1>
        <p>Permanent Cloud Operations Terminal • Fuvahmulah Division</p>
    </div>
    """,
    unsafe_allow_html=True,
)

tab1, tab2, tab3 = st.tabs([
    "📋 Attendance Register",
    "👥 Workforce Directory",
    "💳 Payroll & Payslips",
])

# ================= TAB 1: ATTENDANCE =================
with tab1:
  m1, m2, m3 = st.columns(3)
  with m1:
    st.metric(label="Active Workforce", value=f"{len(staff_df)} Members")
  with m2:
    st.metric(label="Synced Cloud Shifts", value=f"{len(attendance_df)} Shifts")
  with m3:
    today_logged = (
        len(attendance_df[attendance_df["Date"] == str(datetime.date.today())])
        if not attendance_df.empty
        else 0
    )
    st.metric(label="Logged Today", value=f"{today_logged} Records")

  st.markdown("<br>", unsafe_allow_html=True)

  if staff_df.empty:
    st.warning("Please add employees in the Workforce Directory tab first.")
  else:
    with st.form("attendance_form", clear_on_submit=True):
      st.markdown("#### Record Shift Attendance")
      c_date, c_staff = st.columns(2)
      with c_date:
        att_date = st.date_input("Shift Date", datetime.date.today())
      with c_staff:
        selected_staff = st.selectbox(
            "Employee Name", staff_df["Name"].tolist()
        )

      c_stat, c_ot = st.columns(2)
      with c_stat:
        status = st.selectbox(
            "Shift Status",
            ["Present", "Half-Day", "Absent (Unpaid)", "Leave (Paid)"],
        )
      with c_ot:
        ot_hours = st.number_input(
            "Overtime Hours", min_value=0.0, value=0.0, step=0.5
        )

      notes = st.text_input("Operational Notes", "")
      record_submit = st.form_submit_button("Save to Google Sheets")

      if record_submit:
        staff_id = staff_df.loc[
            staff_df["Name"] == selected_staff, "Staff ID"
        ].values[0]
        new_row = pd.DataFrame({
            "Date": [str(att_date)],
            "Staff ID": [staff_id],
            "Name": [selected_staff],
            "Status": [status],
            "Overtime Hours": [ot_hours],
            "Notes": [notes],
        })
        updated_att = pd.concat([attendance_df, new_row], ignore_index=True)
        conn.update(worksheet="Attendance", data=updated_att)
        st.success(
            f"Shift permanently backed up to Google Sheets for {selected_staff}!"
        )
        st.rerun()

  st.markdown("<br>#### Synced Shift History", unsafe_allow_html=True)
  if not attendance_df.empty:
    st.dataframe(
        attendance_df.sort_values(by="Date", ascending=False),
        use_container_width=True,
        hide_index=True,
    )
  else:
    st.info("No shift records found in Google Sheets.")

# ================= TAB 2: STAFF DIRECTORY =================
with tab2:
  st.markdown("#### Active Team Profiles (Google Sheets Synced)")
  st.dataframe(staff_df, use_container_width=True, hide_index=True)

  st.markdown("<br>", unsafe_allow_html=True)
  col_add, col_del = st.columns(2)

  with col_add:
    with st.form("add_staff_form", clear_on_submit=True):
      st.markdown("#### Register New Staff")
      new_name = st.text_input("Full Legal Name")
      new_sal = st.number_input(
          "Monthly Base Salary (MVR)", value=3000.0, step=250.0
      )
      add_action = st.form_submit_button("Save Member to Cloud")

      if add_action and new_name:
        generated_id = f"ZF-{len(staff_df) + 1:03d}"
        new_entry = pd.DataFrame({
            "Staff ID": [generated_id],
            "Name": [new_name.strip()],
            "Base Salary (MVR)": [new_sal],
            "Standard Monthly Days": [26],
        })
        updated_staff = pd.concat([staff_df, new_entry], ignore_index=True)
        conn.update(worksheet="Staff", data=updated_staff)
        st.success(f"Saved {new_name} to Google Drive database.")
        st.rerun()

  with col_del:
    with st.form("del_staff_form"):
      st.markdown("#### Remove Staff Member")
      if not staff_df.empty:
        target_name = st.selectbox(
            "Select Staff to Remove", staff_df["Name"].tolist()
        )
        remove_action = st.form_submit_button("Execute Cloud Removal")
        if remove_action:
          updated_staff = staff_df[
              staff_df["Name"] != target_name
          ].reset_index(drop=True)
          conn.update(worksheet="Staff", data=updated_staff)
          st.success(f"Removed {target_name} from Google Sheet.")
          st.rerun()
      else:
        st.info("Directory is empty.")
        st.form_submit_button("Execute Removal", disabled=True)

# ================= TAB 3: PAYROLL & PAYSLIPS =================
with tab3:
  st.markdown("#### Monthly Disbursement Ledger")

  if attendance_df.empty or staff_df.empty:
    st.info("Log attendance to calculate live payroll.")
  else:
    df_logs = attendance_df.copy()

    def get_unit_day(val):
      if val in ["Present", "Leave (Paid)"]:
        return 1.0
      elif val == "Half-Day":
        return 0.5
      return 0.0

    df_logs["Day_Value"] = df_logs["Status"].apply(get_unit_day)
    payroll_records = []

    for _, emp in staff_df.iterrows():
      emp_id = emp["Staff ID"]
      emp_name = emp["Name"]
      base_salary = float(emp["Base Salary (MVR)"])
      std_days = float(emp["Standard Monthly Days"])

      sub_logs = df_logs[df_logs["Staff ID"] == emp_id]
      worked_days = sub_logs["Day_Value"].sum()
      ot_hours_total = sub_logs["Overtime Hours"].sum()

      hourly = (base_salary / std_days) / 8.0 if std_days > 0 else 0.0
      ot_pay = ot_hours_total * (hourly * 1.25)

      adjusted_base = base_salary
      if worked_days < std_days and std_days > 0:
        adjusted_base = (base_salary / std_days) * worked_days

      net_disbursement = adjusted_base + ot_pay

      payroll_records.append({
          "Staff ID": emp_id,
          "Employee": emp_name,
          "Base (MVR)": base_salary,
          "Adjusted Base (MVR)": adjusted_base,
          "Units Worked": worked_days,
          "OT Hours": ot_hours_total,
          "OT Payout (MVR)": round(ot_pay, 2),
          "Net Payout (MVR)": round(net_disbursement, 2),
      })

    payroll_df = pd.DataFrame(payroll_records)

    total_budget = payroll_df["Net Payout (MVR)"].sum()
    total_ot_paid = payroll_df["OT Payout (MVR)"].sum()

    p1, p2 = st.columns(2)
    with p1:
      st.metric(
          label="Total Monthly Payroll Commitment",
          value=f"{total_budget:,.2f} MVR",
      )
    with p2:
      st.metric(
          label="Total Overtime Allocation", value=f"{total_ot_paid:,.2f} MVR"
      )

    st.markdown("<br>", unsafe_allow_html=True)
    display_df = payroll_df.drop(columns=["Adjusted Base (MVR)"])
    st.dataframe(display_df, use_container_width=True, hide_index=True)


# --- PDF GENERATOR ---
def generate_payslip_pdf(record, period_label):
  pdf = FPDF()
  pdf.add_page()
  pdf.set_auto_page_break(auto=True, margin=15)
  pdf.set_fill_color(15, 23, 42)
  pdf.rect(0, 0, 210, 32, "F")
  pdf.set_text_color(255, 255, 255)
  pdf.set_font("Helvetica", "B", 18)
  pdf.set_xy(10, 8)
  pdf.cell(0, 8, "ZELQON FOODS", 0, 1, "C")
  pdf.set_font("Helvetica", "", 9)
  pdf.cell(
      0, 5, "Fuvahmulah, Maldives | Official Monthly Salary Slip", 0, 1, "C"
  )
  pdf.ln(12)
  pdf.set_text_color(30, 41, 59)
  pdf.set_font("Helvetica", "B", 10)
  pdf.cell(100, 6, f"Pay Period: {period_label}", 0, 0)
  pdf.cell(
      90,
      6,
      f"Date Issued: {datetime.date.today().strftime('%d %B %Y')}",
      0,
      1,
      "R",
  )
  pdf.line(10, pdf.get_y() + 2, 200, pdf.get_y() + 2)
  pdf.ln(6)
  pdf.cell(40, 7, "Employee ID:", 0, 0)
  pdf.set_font("Helvetica", "", 10)
  pdf.cell(60, 7, str(record["Staff ID"]), 0, 0)
  pdf.set_font("Helvetica", "B", 10)
  pdf.cell(40, 7, "Employee Name:", 0, 0)
  pdf.set_font("Helvetica", "", 10)
  pdf.cell(50, 7, str(record["Employee"]), 0, 1)
  pdf.set_font("Helvetica", "B", 10)
  pdf.cell(40, 7, "Standard Days:", 0, 0)
  pdf.set_font("Helvetica", "", 10)
  pdf.cell(60, 7, "26 Days", 0, 0)
  pdf.set_font("Helvetica", "B", 10)
  pdf.cell(40, 7, "Units Worked:", 0, 0)
  pdf.set_font("Helvetica", "", 10)
  pdf.cell(50, 7, f"{record['Units Worked']} Days", 0, 1)
  pdf.ln(6)
  pdf.set_fill_color(241, 245, 249)
  pdf.set_font("Helvetica", "B", 10)
  pdf.cell(120, 8, "Earnings & Allowances", 1, 0, "L", fill=True)
  pdf.cell(70, 8, "Amount (MVR)", 1, 1, "R", fill=True)
  pdf.set_font("Helvetica", "", 10)
  pdf.cell(120, 8, "Base Monthly Salary", 1, 0)
  pdf.cell(70, 8, f"{record['Base (MVR)']:,.2f}", 1, 1, "R")
  base_deduction = record["Base (MVR)"] - record["Adjusted Base (MVR)"]
  if base_deduction > 0:
    pdf.cell(
        120,
        8,
        f"Absence Deduction ({26 - record['Units Worked']} unworked days)",
        1,
        0,
    )
    pdf.cell(70, 8, f"-{base_deduction:,.2f}", 1, 1, "R")
  pdf.cell(120, 8, f"Overtime Pay ({record['OT Hours']} hrs @ 1.25x)", 1, 0)
  pdf.cell(70, 8, f"+{record['OT Payout (MVR)']:,.2f}", 1, 1, "R")
  pdf.set_font("Helvetica", "B", 11)
  pdf.set_fill_color(226, 232, 240)
  pdf.cell(120, 10, "NET SALARY PAYABLE (MVR)", 1, 0, "L", fill=True)
  pdf.cell(
      70, 10, f"{record['Net Payout (MVR)']:,.2f} MVR", 1, 1, "R", fill=True
  )
  pdf.ln(25)
  pdf.set_font("Helvetica", "", 9)
  pdf.line(15, pdf.get_y(), 80, pdf.get_y())
  pdf.line(130, pdf.get_y(), 195, pdf.get_y())
  pdf.cell(90, 5, "Authorized Signature (Zelqon Foods)", 0, 0, "L")
  pdf.cell(100, 5, "Employee Signature / Acknowledgment", 0, 1, "R")
  return bytes(pdf.output())


if not attendance_df.empty and not staff_df.empty:
  st.markdown("---")
  st.markdown("### 📄 Individual Monthly Payslip Generator")
  col_emp, col_btn = st.columns([2, 1])
  with col_emp:
    selected_emp_name = st.selectbox(
        "Select Employee for Payslip", payroll_df["Employee"].tolist()
    )

  target_record = payroll_df[
      payroll_df["Employee"] == selected_emp_name
  ].iloc[0]
  period_str = datetime.date.today().strftime("%B %Y")
  pdf_bytes = generate_payslip_pdf(target_record, period_str)

  with col_btn:
    st.markdown("<br>", unsafe_allow_html=True)
    st.download_button(
        label=f"📥 Download {selected_emp_name}'s Payslip (PDF)",
        data=pdf_bytes,
        file_name=f"Payslip_{selected_emp_name.replace(' ', '_')}_{datetime.date.today().strftime('%b_%Y')}.pdf",
        mime="application/pdf",
    )
