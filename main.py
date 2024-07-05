import streamlit as st
import sqlite3
import pandas as pd

st.set_page_config(
    page_title="Synchllabus",
    page_icon="🗓️",
    layout="wide",
    # initial_sidebar_state="collapsed",
)

st.sidebar.page_link(page="pages/add.py", label="Add instructors", icon="➕")
st.sidebar.page_link(page="pages/instructors.py", label="List of Instructors", icon="👨‍🏫")
st.sidebar.page_link(page="pages/subjects.py", label="List of Subjects", icon="📚")

conn = sqlite3.connect("synchllabus_database.db")

def main():
    st.title("Welcome to Synchlabbus!")
    instructor_subject_df = pd.read_sql_query("SELECT Instructor, Subject FROM instructor_subject", conn)

    # Layout for displaying the tables side by side
    col1, col_spacer, col2 = st.columns([1, 0.1, 1])

    with col1:
        st.write("## Instructors and Their Subjects")
        st.dataframe(instructor_subject_df.set_index('Instructor'), # Set 'Instructor' column as index
                    use_container_width=True)  

    with col2:
        st.write("# 2nd Year")
        st.write("## 2nd Semester")
        st.write("### BS Computer Science")

        # Editable input for number of classes with constraints
        num_classes = st.number_input("Number of Sections/Blocks:", min_value=1, max_value=8, step=1)

        st.subheader("Section Names")
        c1, c2 = st.columns(2)
        for i in range(1, num_classes + 1):
            if i < 5:
                c1.write(f"BSCS 2-{i}")
            else:
                c2.write(f"BSCS 2-{i}")

    # Submit button
    if st.button("Start Scheduling Algorithm"):
        # List all the subjects and meeting types into a list
        # This and the professors will be the 'choices' for the backtracking algorithm
        courses = pd.read_sql_query("SELECT Meeting_type, Subject FROM subjects", conn).values.tolist()

        # Sort courses to place F2F courses before Online courses
        # Since our priority would be to exhaust all the F2F subjects first
        courses.sort(key=lambda x: x[0])
        
        # Clear Table: This can be handled by creating a new empty DataFrame
        schedule_df = create_empty_schedule()

        # Algorithm Proper: Place courses using backtracking
        if place_courses_for_sections(schedule_df, courses):
            st.success("Algorithm Finished")
        else:
            st.error("Unable to place all courses in the schedule")
        display_schedule_in_sections(schedule_df, num_classes)

    st.divider()

    # Close the SQLite connection
    conn.close()

# Function to create and display the initial empty schedule
def create_empty_schedule():
    columns = ["9:00 AM - 12:00 PM", "1:00 PM - 4:00 PM", "4:00 PM - 7:00 PM"]
    empty_data = [["" for _ in columns] for _ in range(48)]
    schedule_df = pd.DataFrame(empty_data, columns=columns)
    return schedule_df

def place_courses(schedule, courses, course_index=0, start_row=0):
    if course_index == len(courses):
        return True

    for row in schedule.index[start_row:]:
        for col in schedule.columns:
            if schedule.at[row, col] == "":
                prof = can_place_course(schedule, courses[course_index], row, col)
                if prof == "Skip":
                    continue  # Skip this cell and move to the next
                elif prof:
                    schedule.at[row, col] = f"{courses[course_index][0]} - {courses[course_index][1]} - {prof}"
                    if place_courses(schedule, courses, course_index + 1, start_row):
                        return True
                    schedule.at[row, col] = ""  # Backtrack
    return False

def place_courses_for_sections(schedule, courses):
    section_start_rows = [0, 6, 12, 18, 24, 30, 36, 42]
    for start_row in section_start_rows:
        if not place_courses(schedule, courses, start_row=start_row):
            print(f"Could not place all courses starting from row {start_row}")
            return False
    return True

def can_place_course(schedule, course, row, col):
    mode, subject = course
    # Check if the slot is empty
    if schedule.at[row, col] != "":
        return False

    if mode == "F2F":
        # Check all multiples of -6 in the same column
        prof1_found = prof2_found = False
        for r in range(row, -1, -6):
            if schedule.loc[r, col] != "" and subject in schedule.loc[r, col]:
                if "Prof 1" in schedule.loc[r, col]:
                    prof1_found = True
                elif "Prof 2" in schedule.loc[r, col]:
                    prof2_found = True
                if prof1_found and prof2_found:
                    return "Skip"  # Indicate to skip this cell if both Prof 1 and Prof 2 are found
        return "Prof 2" if prof1_found else "Prof 1"  # Assign Prof 2 if Prof 1 is found, otherwise Prof 1
    else:  # Online course
        # Check if there's an F2F course in the same row (day)
        for c in schedule.columns:
            if "F2F" in schedule.loc[row, c]:
                return False
        # Check all multiples of -6 in the same column
        prof1_found = prof2_found = False
        for r in range(row, -1, -6):
            if schedule.loc[r, col] != "" and subject in schedule.loc[r, col]:
                if "Prof 1" in schedule.loc[r, col]:
                    prof1_found = True
                elif "Prof 2" in schedule.loc[r, col]:
                    prof2_found = True
                if prof1_found and prof2_found:
                    return "Skip"  # Indicate to skip this cell if both Prof 1 and Prof 2 are found
        return "Prof 2" if prof1_found else "Prof 1"  # Assign Prof 2 if Prof 1 is found, otherwise Prof 1

# Display the schedule DataFrame in sections
def display_schedule_in_sections(schedule_df, num_sections):
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    section_ranges = [(i * 6, (i + 1) * 6) for i in range(num_sections)]
    for i, (start, end) in enumerate(section_ranges):
        st.write(f"### BSCS 2-{i + 1}")
        section_df = schedule_df.iloc[start:end].copy()
        section_df.index = days
        st.dataframe(section_df)

if __name__ == '__main__':
    main()