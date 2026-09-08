import datetime
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Zelqon Foods | Operations & Payroll",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# --- ENTERPRISE EXECUTIVE STYLING ---
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Main canvas background */
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
        color: #0f172a;
    }

    [data-testid="stHeader"] {
        background-color: rgba(248, 250, 252, 0.85);
        backdrop-filter: blur(8px);
    }

    /* Top Brand Hero Banner */
    .brand-hero {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        color: #ffffff;
        padding: 24px 28px;
        border-radius: 14px;
        margin-bottom: 24px;
        border: 1px solid #334155;
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.08);
    }
    .brand-hero h1 {
        color: #ffffff !important;
        font-size: 1.65rem;
        font-weight: 700;
        margin: 0;
        letter-spacing: -0.02em;
    }
    .brand-hero p {
        color: #94a3b8 !important;
        font-size: 0.88rem;
        margin: 4px 0 0 0;
    }

    /* Form and Content Cards */
    [data-testid="stForm"] {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 22px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
    }

    /* Input Fields */
    .stTextInput>div>div>input,
    .stNumberInput>div>div>input,
    .stSelectbox>div>div {
        border-radius: 8px !important;
        border: 1px solid #cbd5e1 !important;
        font-size: 0.92rem !important;
    }
    .stTextInput>div>div>input:focus,
    .stNumberInput>div>div>input:focus {
        border-color: #0d9488 !important;
        box-shadow: 0 0 0 1px #0d9488 !important;
    }

    /* Primary Buttons */
    .stButton>button {
        background: linear-gradient(135deg, #0d9488 0%, #0f766e 100%);
        color: #ffffff !important;
        font-weight: 600;
        font-size: 0.9rem;
        border-radius: 8px;
        border: none;
        padding: 0.55rem 1.4rem;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 1px 3px rgba(13, 148, 136, 0.3);
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #0f766e 0%, #115e59 100%);
        box-shadow: 0 4px 8px rgba(13, 148, 136, 0.4);
        transform: translateY(-1px);
    }

    /* Tab Navigation */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #e2e8f0;
        padding: 5px;
        border-radius: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 7px;
        font-weight: 600;
        font-size: 0.88rem;
        color: #475569;
        padding: 8px 18px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #ffffff !important;
        color: #0f172a !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
    }

    /* Metric Cards */
    [data-testid="stMetric"] {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.03);
    }
    [data-testid="stMetricLabel"] {
        color: #64748b !important;
        font-weight: 600;
        font-size: 0.8rem !important;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }
    [data-testid="stMetricValue"] {
        color: #0f172a !important;
        font-weight: 700 !important;
        font-size: 1.45rem !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- SECURE ACCESS GATEWAY ---
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
      st.markdown(
          "<p style='color: #64748b; font-size: 0.9rem;'>Enter your administrative credentials to continue.</p>",
          unsafe_allow_html=True,
      )
      pwd = st.text_input("Access Password", type="password")
      submit = st.form_submit_button("Authenticate")
      if submit:
        if pwd == "zelqon2026":
          st.session_state.password_correct = True
          st.rerun()
        else:
          st.error("Invalid credentials. Please verify your password.")
  return False

if not check_password():
  st.stop()

# --- HEADER SECTION ---
st.markdown(
    """
    <div class="brand-hero">
        <h1>ZELQON FOODS</h1>
        <p>Operations Management & Payroll Terminal • Fuvahmulah Division</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# --- DATA INITIALIZATION ---
if "staff" not in st.session_state:
  st.session_state.staff = pd.DataFrame({
      "Staff ID": ["ZF-001", "ZF-002"],
      "Name": ["Staff Member 1", "Staff Member 2"],
      "Base Salary (MVR)": [3000.0, 3000.0],
      "Standard Monthly Days": [26, 26],
  })

if "attendance" not in st.session_state:
  st.session_state.attendance = pd.DataFrame(
      columns=["Date", "Staff ID", "Name", "Status", "Overtime Hours", "Notes"]
  )

# --- APPLICATION TABS ---
tab1, tab2, tab3 = st.tabs([
    "📋 Attendance Register",
    "👥 Workforce Directory",
    "💳 Payroll Ledger",
])

# ================= TAB 1: ATTENDANCE =================
with tab1:
  m1, m2, m3 = st.columns(3)
  with m1:
    st.metric(
        label="Active Workforce",
        value=f"{len(st.session_state.staff)} Members",
    )
  with m2:
    st.metric(
        label="Logs Logged This Month",
        value=f"{len(st.session_state.attendance)} Shifts",
    )
  with m3:
    today_logged = (
        len(
            st.session_state.attendance[
                st.session_state.attendance["Date"]
                == str(datetime.date.today())
            ]
        )
        if not st.session_state.attendance.empty
        else 0
    )
    st.metric(label="Logged Today", value=f"{today_logged} Records")

  st.markdown("<br>", unsafe_allow_html=True)

  if st.session_state.staff.empty:
    st.warning("Staff directory is empty. Add employees in Tab 2 to proceed.")
  else:
    with st.form("attendance_form", clear_on_submit=True):
      st.markdown("#### Record Shift Attendance")
      c_date, c_staff = st.columns(2)
      with c_date:
        att_date = st.date_input("Shift Date", datetime.date.today())
      with c_staff:
        selected_staff = st.selectbox(
            "Employee Name", st.session_state.staff["Name"].tolist()
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

      notes = st.text_input("Operational Notes / Batch Activity", "")
      record_submit = st.form_submit_button("Log Shift Record")

      if record_submit:
        staff_id = st.session_state.staff.loc[
            st.session_state.staff["Name"] == selected_staff, "Staff ID"
        ].values[0]
        new_row = pd.DataFrame({
            "Date": [str(att_date)],
            "Staff ID": [staff_id],
            "Name": [selected_staff],
            "Status": [status],
            "Overtime Hours": [ot_hours],
            "Notes": [notes],
        })
        st.session_state.attendance = pd.concat(
            [st.session_state.attendance, new_row], ignore_index=True
        )
        st.success(f"Shift recorded for {selected_staff} ({att_date}).")

  st.markdown("<br>#### Shift History Log", unsafe_allow_html=True)
  if not st.session_state.attendance.empty:
    st.dataframe(
        st.session_state.attendance.sort_values(by="Date", ascending=False),
        use_container_width=True,
        hide_index=True,
    )
    if st.button("Reset Shift Records"):
      st.session_state.attendance = pd.DataFrame(
          columns=[
              "Date",
              "Staff ID",
              "Name",
              "Status",
              "Overtime Hours",
              "Notes",
          ]
      )
      st.rerun()
  else:
    st.info("No shift logs entered yet.")

# ================= TAB 2: STAFF DIRECTORY =================
with tab2:
  st.markdown("#### Active Team Profiles")
  st.dataframe(st.session_state.staff, use_container_width=True, hide_index=True)

  st.markdown("<br>", unsafe_allow_html=True)
  col_add, col_del = st.columns(2)

  with col_add:
    with st.form("add_staff_form", clear_on_submit=True):
      st.markdown("#### Register New Staff")
      new_name = st.text_input("Full Legal Name")
      new_sal = st.number_input(
          "Monthly Base Salary (MVR)", value=3000.0, step=250.0
      )
      add_action = st.form_submit_button("Register Team Member")

      if add_action and new_name:
        generated_id = f"ZF-{len(st.session_state.staff) + 1:03d}"
        new_entry = pd.DataFrame({
            "Staff ID": [generated_id],
            "Name": [new_name.strip()],
            "Base Salary (MVR)": [new_sal],
            "Standard Monthly Days": [26],
        })
        st.session_state.staff = pd.concat(
            [st.session_state.staff, new_entry], ignore_index=True
        )
        st.success(f"Staff member {new_name} added as {generated_id}.")
        st.rerun()

  with col_del:
    with st.form("del_staff_form"):
      st.markdown("#### Remove Staff Member")
      if not st.session_state.staff.empty:
        target_name = st.selectbox(
            "Select Staff to Terminate/Remove",
            st.session_state.staff["Name"].tolist(),
        )
        remove_action = st.form_submit_button("Execute Removal")
        if remove_action:
          st.session_state.staff = st.session_state.staff[
              st.session_state.staff["Name"] != target_name
          ].reset_index(drop=True)
          st.success(f"Removed {target_name} from workforce records.")
          st.rerun()
      else:
        st.info("Workforce directory is empty.")
        st.form_submit_button("Execute Removal", disabled=True)

# ================= TAB 3: PAYROLL LEDGER =================
with tab3:
  st.markdown("#### Monthly Disbursement Ledger")

  if st.session_state.attendance.empty:
    st.info(
        "Attendance ledger is currently blank. Log daily shifts to calculate payouts."
    )
  else:
    df_logs = st.session_state.attendance.copy()

    def get_unit_day(val):
      if val in ["Present", "Leave (Paid)"]:
        return 1.0
      elif val == "Half-Day":
        return 0.5
      return 0.0

    df_logs["Day_Value"] = df_logs["Status"].apply(get_unit_day)
    payroll_records = []

    for _, emp in st.session_state.staff.iterrows():
      emp_id = emp["Staff ID"]
      emp_name = emp["Name"]
      base_salary = emp["Base Salary (MVR)"]
      std_days = emp["Standard Monthly Days"]

      sub_logs = df_logs[df_logs["Staff ID"] == emp_id]
      worked_days = sub_logs["Day_Value"].sum()
      ot_hours_total = sub_logs["Overtime Hours"].sum()

      # Hourly rate = (Base Salary / 26 days) / 8 hours
      hourly = (base_salary / std_days) / 8.0 if std_days > 0 else 0.0
      ot_pay = ot_hours_total * (hourly * 1.25)

      # Pro-rated deduction for unattended standard days
      adjusted_base = base_salary
      if worked_days < std_days and std_days > 0:
        adjusted_base = (base_salary / std_days) * worked_days

      net_disbursement = adjusted_base + ot_pay

      payroll_records.append({
          "Staff ID": emp_id,
          "Employee": emp_name,
          "Base (MVR)": base_salary,
          "Units Worked": worked_days,
          "OT Hours": ot_hours_total,
          "OT Payout (MVR)": round(ot_pay, 2),
          "Net Payout (MVR)": round(net_disbursement, 2),
      })

    payroll_df = pd.DataFrame(payroll_records)

    # Executive Summary Metrics
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
    st.dataframe(payroll_df, use_container_width=True, hide_index=True)

    csv_export = payroll_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Export Certified Payroll Sheet (CSV)",
        data=csv_export,
        file_name=f"zelqon_disbursement_{datetime.date.today().strftime('%Y_%m')}.csv",
        mime="text/csv",
    )
