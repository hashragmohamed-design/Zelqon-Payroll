import datetime
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Zelqon Foods - Attendance & Payroll", layout="wide"
)

st.title("🌱 Zelqon Foods: Staff Attendance & Payroll Tracker")
st.markdown("### Initial Startup Team Management (Fuvahmulah)")

# Initialize session state for staff and attendance records if they don't exist
if "staff" not in st.session_state:
  st.session_state.staff = pd.DataFrame({
      "Staff ID": ["ZF-001", "ZF-002"],
      "Name": ["Staff Member 1", "Staff Member 2"],
      "Base Salary (MVR)": [3000.0, 3000.0],
      "Standard Monthly Days": [26, 26],  # e.g., 6 days a week schedule
  })

if "attendance" not in st.session_state:
  # Mock initial attendance log for the current month
  st.session_state.attendance = pd.DataFrame(columns=[
      "Date",
      "Staff ID",
      "Name",
      "Status",
      "Overtime Hours",
      "Notes",
  ])

# --- TAB SETUP ---
tab1, tab2, tab3 = st.tabs(
    ["📅 Log Attendance", "👥 Staff Management", "💰 Payroll Summary"]
)

with tab1:
  st.subheader("Daily Attendance Entry")

  with st.form("attendance_form"):
    col1, col2, col3 = st.columns(3)
    with col1:
      att_date = st.date_input("Date", datetime.date.today())
    with col2:
      selected_staff = st.selectbox(
          "Select Staff", st.session_state.staff["Name"].tolist()
      )
    with col3:
      status = st.selectbox(
          "Status", ["Present", "Half-Day", "Absent (Unpaid)", "Leave (Paid)"]
      )

    col4, col5 = st.columns(2)
    with col4:
      ot_hours = st.number_input(
          "Overtime Hours (if any)", min_value=0.0, value=0.0, step=0.5
      )
    with col5:
      notes = st.text_input("Notes / Remarks", "")

    submitted = st.form_submit_button("Save Attendance Record")

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
      st.success(f"Attendance recorded for {selected_staff} on {att_date}!")

  st.markdown("### Recent Attendance Log")
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
    st.info("No attendance records logged yet for this period.")

with tab2:
  st.subheader("Manage Staff Profiles")
  st.dataframe(st.session_state.staff, use_container_width=True)

  with st.form("add_staff"):
    st.markdown("#### Update Base Info")
    new_name = st.text_input("New Staff Name")
    new_salary = st.number_input("Monthly Salary (MVR)", value=3000.0)
    add_btn = st.form_submit_button("Add Team Member")
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
      st.success(f"Added {new_name} to Zelqon Foods team!")
      st.rerun()

with tab3:
  st.subheader("Monthly Payroll & Settlement Calculator")

  if st.session_state.attendance.empty:
    st.warning(
        "Log some attendance data in the first tab to view payroll calculations."
    )
  else:
    # Calculate payroll metrics based on logs
    df_att = st.session_state.attendance.copy()

    # Map status to multipliers/deductions if needed
    # Present = 1, Half-Day = 0.5, Absent = 0
    def get_day_value(status):
      if status == "Present" or status == "Leave (Paid)":
        return 1.0
      elif status == "Half-Day":
        Spacer = 0.5
        return 0.5
      return 0.0

    df_att["Day_Value"] = df_att["Status"].apply(get_day_value)

    # Aggregate by staff
    summary_list = []
    for index, row in st.session_state.staff.iterrows():
      s_id = row["Staff ID"]
      s_name = row["Name"]
      base_sal = row["Base Salary (MVR)"]
      std_days = row["Standard Monthly Days"]

      staff_logs = df_att[df_att["Staff ID"] == s_id]
      days_worked = staff_logs["Day_Value"].sum()
      total_ot = staff_logs["Overtime Hours"].sum()

      # Simple prorated calculation or standard base deduction
      # Assuming 1 overtime hour = (Base Salary / Standard Days / 8 hours) * 1.25 multiplier
      hourly_rate = (base_sal / std_days) / 8
      ot_pay = total_ot * hourly_rate * 1.25

      # Pro-rate base salary if they missed days below standard (optional logic, or flat rate)
      # Let's use a proportional approach if days logged are fewer than standard
      effective_base = base_sal
      if days_worked < std_days and std_days > 0:
        # Optional: Pro-rate base salary based on attendance adherence
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

    # Export option
    csv = summary_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Download Monthly Payroll Report (CSV)",
        data=csv,
        file_name=f"zelqon_payroll_{datetime.date.today().strftime('%Y-%m')}.csv",
        mime="text/csv",
    )
