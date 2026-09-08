import datetime
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Zelqon Foods - HR & Payroll",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# --- PROFESSIONAL EXECUTIVE BACKGROUND & UI STYLING ---
st.markdown(
    """
    <style>
    /* App background styling */
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
        color: #1e293b;
    }
    
    /* Transparent header to blend with background */
    [data-testid="stHeader"] {
        background-color: rgba(0,0,0,0);
    }

    /* Modern cards, inputs, and button designs */
    .stButton>button {
        background-color: #0f766e;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 0.5rem 1.2rem;
        font-weight: 600;
        transition: all 0.2s ease-in-out;
    }
    .stButton>button:hover {
        background-color: #115e59;
        color: #f8fafc;
    }

    .stTextInput>div>div>input, 
    .stNumberInput>div>div>input,
    .stSelectbox>div>div {
        border-radius: 8px;
        background-color: #ffffff;
    }

    .stTabs [data-baseweb="tab-list"] {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 6px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    </style>
""",
    unsafe_allow_html=True,
)

# --- PASSWORD AUTHENTICATION ---
def check_password():
  if "password_correct" not in st.session_state:
    st.session_state.password_correct = False

  if st.session_state.password_correct:
    return True

  col1, col2, col3 = st.columns([1, 2, 1])
  with col2:
    st.markdown("### 🔒 Zelqon Foods Portal")
    st.markdown("Please enter your administrative password to proceed.")
    pwd = st.text_input("Password", type="password")
    if st.button("Access Dashboard"):
      if pwd == "zelqon2026":
        st.session_state.password_correct = True
        st.rerun()
      else:
        st.error("Incorrect password. Please try again.")
  return False

if not check_password():
  st.stop()

# --- DASHBOARD HEADER ---
st.markdown("## 🌱 Zelqon Foods")
st.markdown("**Staff Attendance & Monthly Payroll Hub** | *Fuvahmulah*")
st.markdown("---")

# Initialize default team and logs if empty
if "staff" not in st.session_state:
  st.session_state.staff = pd.DataFrame({
      "Staff ID": ["ZF-001", "ZF-002"],
      "Name": ["Staff Member 1", "Staff Member 2"],
      "Base Salary (MVR)": [3000.0, 3000.0],
      "Standard Monthly Days": [26, 26],
  })

if "attendance" not in st.session_state:
  st.session_state.attendance = pd.DataFrame(columns=[
      "Date",
      "Staff ID",
      "Name",
      "Status",
      "Overtime Hours",
      "Notes",
  ])

# --- NAVIGATION TABS ---
tab1, tab2, tab3 = st.tabs(
    ["📅 Attendance Logger", "👥 Staff Directory", "💰 Payroll Summary"]
)

with tab1:
  st.markdown("### Daily Attendance Entry")
  if st.session_state.staff.empty:
    st.warning("No staff found. Please add members in the Staff Directory tab.")
  else:
    with st.form("attendance_form", clear_on_submit=True):
      col_date, col_staff = st.columns(2)
      with col_date:
        att_date = st.date_input("Work Date", datetime.date.today())
      with col_staff:
        selected_staff = st.selectbox(
            "Select Employee", st.session_state.staff["Name"].tolist()
        )

      col_stat, col_ot = st.columns(2)
      with col_stat:
        status = st.selectbox(
            "Attendance Status",
            ["Present", "Half-Day", "Absent (Unpaid)", "Leave (Paid)"],
        )
      with col_ot:
        ot_hours = st.number_input(
            "Overtime Hours (OT)", min_value=0.0, value=0.0, step=0.5
        )

      notes = st.text_input("Operational Notes / Remarks", "")
      submitted = st.form_submit_button("Record Entry")

      if submitted:
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
        st.success(f"Logged record for {selected_staff} on {att_date}.")

  st.markdown("#### Recent Shift Logs")
  if not st.session_state.attendance.empty:
    st.dataframe(
        st.session_state.attendance.sort_values(by="Date", ascending=False),
        use_container_width=True,
    )
    if st.button("Reset Attendance Records"):
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
    st.info("No attendance entries registered yet.")

with tab2:
  st.markdown("### Manage Team & Salaries")
  st.dataframe(st.session_state.staff, use_container_width=True)

  col_add, col_del = st.columns(2)

  with col_add:
    with st.form("add_member_form", clear_on_submit=True):
      st.markdown("#### Add New Team Member")
      name_to_add = st.text_input("Full Name")
      salary_to_add = st.number_input("Monthly Salary (MVR)", value=3000.0)
      add_btn = st.form_submit_button("Register Staff")
      if add_btn and name_to_add:
        generated_id = f"ZF-00{len(st.session_state.staff) + 1}"
        new_member = pd.DataFrame({
            "Staff ID": [generated_id],
            "Name": [name_to_add],
            "Base Salary (MVR)": [salary_to_add],
            "Standard Monthly Days": [26],
        })
        st.session_state.staff = pd.concat(
            [st.session_state.staff, new_member], ignore_index=True
        )
        st.success(f"Registered {name_to_add} under {generated_id}.")
        st.rerun()

  with col_del:
    with st.form("remove_member_form"):
      st.markdown("#### Remove Staff Member")
      if not st.session_state.staff.empty:
        to_delete = st.selectbox(
            "Select Staff to Delete", st.session_state.staff["Name"].tolist()
        )
        delete_btn = st.form_submit_button("Delete Member")
        if delete_btn:
          st.session_state.staff = st.session_state.staff[
              st.session_state.staff["Name"] != to_delete
          ].reset_index(drop=True)
          st.success(f"Removed {to_delete} from active staff.")
          st.rerun()
      else:
        st.info("No active staff to remove.")
        st.form_submit_button("Delete Member", disabled=True)

with tab3:
  st.markdown("### Monthly Payroll Calculation")

  if st.session_state.attendance.empty:
    st.warning("Log daily attendance in Tab 1 to compute monthly payroll.")
  else:
    df_att = st.session_state.attendance.copy()

    def get_day_val(status_val):
      if status_val in ["Present", "Leave (Paid)"]:
        return 1.0
      elif status_val == "Half-Day":
        return 0.5
      return 0.0

    df_att["Day_Value"] = df_att["Status"].apply(get_day_val)
    payroll_summary = []

    for _, row in st.session_state.staff.iterrows():
      s_id = row["Staff ID"]
      s_name = row["Name"]
      base_sal = row["Base Salary (MVR)"]
      std_days = row["Standard Monthly Days"]

      staff_records = df_att[df_att["Staff ID"] == s_id]
      days_worked = staff_records["Day_Value"].sum()
      total_ot = staff_records["Overtime Hours"].sum()

      # Overtime formula: (Base / Std Days / 8 hrs) * 1.25 multiplier
      hourly_rate = (base_sal / std_days) / 8
      ot_amount = total_ot * hourly_rate * 1.25

      # Pro-rated base calculation for unexcused absence
      effective_base = base_sal
      if days_worked < std_days and std_days > 0:
        effective_base = (base_sal / std_days) * days_worked

      total_net = effective_base + ot_amount

      payroll_summary.append({
          "Staff ID": s_id,
          "Name": s_name,
          "Base Salary (MVR)": base_sal,
          "Days Worked": days_worked,
          "Total OT Hours": total_ot,
          "OT Pay (MVR)": round(ot_amount, 2),
          "Net Payout (MVR)": round(total_net, 2),
      })

    summary_df = pd.DataFrame(payroll_summary)
    st.dataframe(summary_df, use_container_width=True)

    csv_data = summary_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Export Monthly Payroll (CSV)",
        data=csv_data,
        file_name=f"zelqon_payroll_{datetime.date.today().strftime('%Y_%m')}.csv",
        mime="text/csv",
    )
