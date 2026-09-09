st.divider()
st.subheader("Manage Logged Shifts")

# Fetch latest attendance records
attendance_df = conn.read(worksheet="Attendance", ttl=0)

if not attendance_df.empty:
  # Clean out completely empty rows if any exist
  valid_attendance = attendance_df.dropna(subset=["Date", "Name"]).copy()

  if not valid_attendance.empty:
    # Build readable labels for the dropdown (e.g., "2026-09-08 | Ahmed Ali (Present) - 2h OT")
    shift_options = {
        f"{row['Date']} | {row['Name']} ({row['Status']}) - {row['Overtime Hours']}h OT": idx
        for idx, row in valid_attendance.iterrows()
    }

    shift_to_delete = st.selectbox(
        "Select shift to remove:",
        options=list(shift_options.keys()),
        key="delete_shift_select",
    )

    if st.button("🗑️ Delete Shift Record", type="secondary"):
      # Drop the selected record
      row_index = shift_options[shift_to_delete]
      updated_attendance = attendance_df.drop(index=row_index).reset_index(
          drop=True
      )

      # Ensure base columns remain even if all records are deleted
      if updated_attendance.empty:
        updated_attendance = pd.DataFrame(
            columns=[
                "Date",
                "Staff ID",
                "Name",
                "Status",
                "Overtime Hours",
                "Notes",
            ]
        )

      # Overwrite the sheet with the cleaned data
      conn.update(worksheet="Attendance", data=updated_attendance)
      st.cache_data.clear()
      st.success("Shift record successfully deleted from Google Sheets!")
      st.rerun()
  else:
    st.info("No recorded shifts found to delete.")
else:
  st.info("No attendance records logged yet.")
