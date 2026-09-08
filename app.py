import datetime
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Zelqon Foods - Attendance & Payroll",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# --- PROFESSIONAL UI STYLING ---
st.markdown(
    """
    <style>
    .main { background-color: #f4f6f9; }
    .stButton>button { border-radius: 6px; font-weight: 600; }
    .stTextInput, .stSelectbox, .stNumberInput { border-radius: 6px; }
    h1, h2, h3 { color: #1e293b; }
    </style>
""",
    unsafe_allow_html=True,
)

# --- PASSWORD PROTECTION ---
def check_password():
  if "password_correct" not in st.session_state:
    st.session_state.password_correct = False

  if st.session_state.password_correct:
    return True

  st.markdown("### 🔒 Zelqon Foods - Secure Access")
  pwd = st.text_input("Enter App Password", type="password")
  if st.button("Login"):
    if pwd == "zelqon2026":
      st.session_state.password_correct = True
      st.rerun()
    else:
      st.error("Incorrect password. Please try again.")
  return False

if not check_password():
  st.stop()

# --- MAIN APP HEADER ---
st.markdown("## 🌱 Zelqon Foods")
st.markdown("*Staff Attendance & Payroll System — Fuvahmulah*")
st.markdown("---")

# Initialize session state for staff and attendance records
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

# --- TABS ---
tab1, tab2, tab3 = st.tabs(
    ["📅 Daily Attendance", "👥 Staff Management", "💰 Payroll Summary"]
)

with tab1:
  st.markdown("### Log Daily Attendance")

  if st.session_state.staff.empty:
    st.warning(
        "Please add staff members in the 'Staff Management' tab first."
    )
  else:
    with st.form("attendance_form", clear_on_submit=True):
      col1, col2 = st.columns(2)
      with col1:
        att_date = st.date_input("Date", datetime.date.today())
      with col2:
        selected_staff = st.selectbox(
            "Select Staff", st.session_state.staff["Name"].tolist()
        )

      col3, col4 = st.columns(2)
      with col3:
        status = st.selectbox(
            "Status", ["Present", "Half-Day", "Absent (Unpaid)", "Leave (Paid)"]
        )
      with col4:
        ot_hours = st.number_input(
            "Overtime Hours", min_value=0.0, value=0.0, step=0.5
        )

      notes = st.text_input("Remarks / Notes", "")
      submitted = st.form_submit_button("Save Record")

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
        st.success(f"Attendance recorded for {selected_staff}!")

  st.markdown("#### Recent Attendance History")
  if not st.session_state.attendance.empty:
    st.dataframe(
        st.session_state.attendance.sort_values(by="Date", ascending=False),
        use_container_width=True,
    )
    if st.button("Clear Attendance History"):
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
    st.info("No attendance logs recorded yet.")

with tab2:
  st.markdown("### Current Team Members")
  st.dataframe(st.session_state.staff, use_container_width=True)

  col_add, col_rem = st.columns(2)

  with col_add:
    with st.form("add_staff"):
      st.markdown("#### Add New Staff")
      new_name = st.text_input("Staff Name")
      new_salary = st.number_input("Monthly Salary (MVR)", value=3000.0)
      add_btn = st.form_submit_button("Add Member")
      if add_btn and new_name:
        new_id = f"ZF-00{len(st.session_state.staff) + 1}"
        temp_df = pd.DataFrame({
            "Staff ID": [new_id],
            "Name": [new_name],
            "Base Salary (MVR)": [new_salary],
            "Standard Monthly Days": [26],
        })
        st.session_state.staff = pd.concat(
            [st.session_state.staff, temp_df], ignore_index=True
        )
        st.success(f"Added {new_name} successfully!")
        st.rerun()

  with col_rem:
    with st.form("remove_staff"):
      st.markdown("#### Remove Staff Member")
      if not st.session_state.staff.empty:
        staff_to_remove = st.selectbox(
            "Select Staff to Remove", st.session_state.staff["Name"].tolist()
        )
        remove_btn = st.form_submit_button("Remove Member")
        if remove_btn:
          st.session_state.staff = st.session_state.staff[
              st.session_state.staff["Name"] != staff_to_remove
          ].reset_index(drop=True)
          st.success(f"Removed {staff_to_remove}!")
          st.rerun()
      else:
        st.info("No staff to remove.")
        st.form_submit_button("Remove Member", disabled=True)

with tab3:
  st.markdown("### Monthly Payroll & Settlement Summary")

  if st.session_state.attendance.empty:
    st.warning("Log attendance records in Tab 1 to generate payroll totals.")
  else:
    df_att = st.session_state.attendance.copy()

    def get_day_value(status):
      if status == "Present" or status == "Leave (Paid)":
        return 1.0
      elif status == "Half-Day":
        return 0.5
      return 0.0

    df_att["Day_Value"] = df_att["Status"].apply(get_day_value)

    summary_list = []
    for index, row in st.session_state.staff.iterrows():
      s_id = row["Staff ID"]
      s_name = row["Name"]
      base_sal = row["Base Salary (MVR)"]
      std_days = row["Standard Monthly Days"]

      staff_logs = df_att[df_att["Staff ID"] == s_id]
      days_worked = staff_logs["Day_Value"].sum()
      total_ot = staff_logs["Overtime Hours"].sum()

      hourly_rate = (base_sal / std_days) / 8
      ot_pay = total_ot * hourly_rate * 1.25

      effective_base = base_sal
      if days_worked < std_days and std_days > 0:
        effective_base = (base_sal / std_days) * days_worked

      net_pay = effective_base + ot_pay

      summary_list.append({
          "Staff ID": s_id,
          "Name": s_name,
          "Base Salary (MVR)": base_sal,
          "Days Logged": days_worked,
          "Total OT Hours": total_ot,
          "OT Pay (MVR)": round(ot_pay, 2),
          "Calculated Net Pay (MVR)": round(net_pay, 2),
      })

    summary_df = pd.DataFrame(summary_list)
    st.dataframe(summary_df, use_container_width=True)

    csv = summary_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Download Monthly Payroll Report (CSV)",
        data=csv,
        file_name=f"zelqon_payroll_{datetime.date.today().strftime('%Y-%m')}.csv",
        mime="text/csv",
    )
