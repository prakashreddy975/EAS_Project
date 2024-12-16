import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import matplotlib.pyplot as plt

# Connect to the updated database
conn = sqlite3.connect('employee_database_new.db')

# Helper function to fetch data from SQL
def fetch_data(query):
    try:
        return pd.read_sql_query(query, conn)
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return pd.DataFrame()

# Load data for analysis
employee_query = """
SELECT e.Employee_ID, e.Name, e.Gender, e.Age, e.Education, e.Join_Date, e.Tenure, 
       l.City, l.Country
FROM Employee e
JOIN Location l ON e.Location_ID = l.Location_ID
"""
employee_data = fetch_data(employee_query)

salary_query = "SELECT * FROM Salary"
salary_data = fetch_data(salary_query)

performance_query = "SELECT * FROM Performance"
performance_data = fetch_data(performance_query)

department_query = "SELECT * FROM Department"
department_data = fetch_data(department_query)

# Employee-Department relationship query
employee_department_query = """
SELECT e.Employee_ID, e.Name, e.Gender, e.Age, e.Education, e.Join_Date, e.Tenure, 
       l.City, l.Country, 
       s.Salary, s.Annual_Bonus, s.Bonus_Percentage,
       p.Performance_Score, p.Working_Hours,
       d.Department_Name
FROM Employee e
JOIN Location l ON e.Location_ID = l.Location_ID
JOIN Salary s ON e.Employee_ID = s.Employee_ID
JOIN Performance p ON e.Employee_ID = p.Employee_ID
JOIN Employee_Department ed ON e.Employee_ID = ed.Employee_ID
JOIN Department d ON ed.Department_ID = d.Department_ID
"""
merged_data = fetch_data(employee_department_query)

# Streamlit Dashboard
st.title("Employee Data Analysis Dashboard")

# Sidebar Filters
st.sidebar.header("Filters")
selected_gender = st.sidebar.multiselect("Select Gender", options=employee_data["Gender"].unique(), default=employee_data["Gender"].unique())
selected_city = st.sidebar.multiselect("Select City", options=employee_data["City"].unique(), default=employee_data["City"].unique())
selected_country = st.sidebar.multiselect("Select Country", options=employee_data["Country"].unique(), default=employee_data["Country"].unique())  # New Country filter
selected_salary_range = st.sidebar.slider(
    "Select Salary Range", 
    min_value=float(salary_data["Salary"].min()), 
    max_value=float(salary_data["Salary"].max()), 
    value=(float(salary_data["Salary"].min()), float(salary_data["Salary"].max()))
)

selected_age_range = st.sidebar.slider("Select Age Range", 
                                       min_value=int(employee_data["Age"].min()), 
                                       max_value=int(employee_data["Age"].max()), 
                                       value=(int(employee_data["Age"].min()), int(employee_data["Age"].max())))
selected_tenure_range = st.sidebar.slider("Select Tenure Range (Years)", 
                                          min_value=int(employee_data["Tenure"].min()), 
                                          max_value=int(employee_data["Tenure"].max()), 
                                          value=(int(employee_data["Tenure"].min()), int(employee_data["Tenure"].max())))

# Apply Filters
filtered_data = merged_data[
    (merged_data["Gender"].isin(selected_gender)) &
    (merged_data["City"].isin(selected_city)) &
    (merged_data["Country"].isin(selected_country)) &  # Ensure this filter is also applied
    (merged_data["Salary"].between(selected_salary_range[0], selected_salary_range[1])) &
    (merged_data["Age"].between(selected_age_range[0], selected_age_range[1])) &
    (merged_data["Tenure"].between(selected_tenure_range[0], selected_tenure_range[1]))  # Apply tenure filter
]

# Dynamic Metrics
st.subheader("Key Metrics")
col1, col2, col3 = st.columns(3)
col1.metric("Total Employees", len(filtered_data))
col2.metric("Average Salary", f"${filtered_data['Salary'].mean():,.2f}")
col3.metric("Average Performance Score", f"{filtered_data['Performance_Score'].mean():.2f}")

# Visualization 1: Gender Distribution with City Breakdown
st.subheader("Gender Distribution by City")
gender_city_fig = px.sunburst(
    filtered_data,
    path=["City", "Gender"],
    title="Gender Distribution by City",
    color="Gender",
    color_discrete_sequence=px.colors.qualitative.Pastel
)
st.plotly_chart(gender_city_fig)

# Visualization 2: Salary vs Performance Score with Tenure Comparison
filtered_data.loc[:, 'Salary'] = pd.to_numeric(filtered_data['Salary'], errors='coerce')
filtered_data.loc[:, 'Performance_Score'] = pd.to_numeric(filtered_data['Performance_Score'], errors='coerce')
filtered_data.loc[:, 'Tenure'] = pd.to_numeric(filtered_data['Tenure'], errors='coerce')
filtered_data.loc[:, 'Working_Hours'] = pd.to_numeric(filtered_data['Working_Hours'], errors='coerce')

# Drop rows with any NaN values in the relevant columns
filtered_data = filtered_data.dropna(subset=['Salary', 'Performance_Score', 'Tenure', 'Working_Hours'])

# Now proceed to plot
st.subheader("Performance Score by Salary")
salary_perf_fig = px.scatter(
    filtered_data,
    x="Salary",
    y="Performance_Score",
    color="Tenure",  # Make sure Tenure is numeric or categorical
    size="Working_Hours",  # Ensure Working_Hours is numeric
    hover_data=["Name", "Age", "City", "Gender"],
    title="Salary vs Performance Score (Colored by Tenure)",
    color_continuous_scale="Viridis"
)

st.plotly_chart(salary_perf_fig)

# Visualization 3: Average Salary by Department
st.subheader("Average Salary by Department")
avg_salary_dept = filtered_data.groupby("Department_Name")["Salary"].mean().reset_index()
department_salary_fig = px.bar(
    avg_salary_dept,
    x="Department_Name",
    y="Salary",
    title="Average Salary by Department",
    color="Salary",
    color_continuous_scale="Blues"
)
st.plotly_chart(department_salary_fig)

# Visualization 4: Performance Score Distribution by Department
st.subheader("Performance Score Distribution by Department")
dept_perf_fig = px.box(
    filtered_data,
    x="Department_Name",
    y="Performance_Score",
    color="Department_Name",
    title="Performance Score Distribution by Department",
    boxmode="overlay"
)
st.plotly_chart(dept_perf_fig)

# Visualization 5: Salary Distribution by Department
st.subheader("Salary Distribution by Department")
dept_salary_fig = px.box(
    filtered_data,
    x="Department_Name",
    y="Salary",
    color="Department_Name",
    title="Salary Distribution by Department",
    boxmode="overlay"
)
st.plotly_chart(dept_salary_fig)

# Visualization 6: Correlation Heatmap
st.subheader("Correlation Heatmap")
numeric_data = filtered_data[["Age", "Salary", "Annual_Bonus", "Bonus_Percentage", "Performance_Score", "Working_Hours", "Tenure"]]
correlation = numeric_data.corr()
heatmap_fig = px.imshow(
    correlation,
    labels=dict(x="Metrics", y="Metrics", color="Correlation"),
    title="Correlation Heatmap of Numeric Metrics",
    color_continuous_scale="RdBu",
    text_auto=True
)
st.plotly_chart(heatmap_fig)

# Visualization: Salary Distribution by Gender
st.subheader("Salary Distribution by Gender")
salary_gender_fig = px.box(
    filtered_data,
    x="Gender",
    y="Salary",
    color="Gender",
    title="Salary Distribution by Gender",
    boxmode="overlay"
)
st.plotly_chart(salary_gender_fig)


# Fetch employee department data
empl_dept_query = """
SELECT d.Department_Name, COUNT(ed.Employee_ID) AS Employee_Count
FROM Department d
JOIN Employee_Department ed ON d.Department_ID = ed.Department_ID
GROUP BY d.Department_Name
ORDER BY Employee_Count DESC;
"""
empl_dept_data = fetch_data(empl_dept_query)

# Employee Distribution by Department (Pie Chart)
st.subheader("Employee Distribution by Department (Pie Chart)")
fig, ax = plt.subplots(figsize=(8, 8))
ax.pie(empl_dept_data['Employee_Count'], labels=empl_dept_data['Department_Name'], autopct='%1.1f%%', colors=sns.color_palette('viridis', len(empl_dept_data)))
ax.set_title('Employee Distribution by Department')
ax.axis('equal')  # Equal aspect ratio ensures the pie chart is circular.
st.pyplot(fig)


# Top 10 Highest Paid Employees
st.subheader("Top 10 Highest Paid Employees")
top_paid = filtered_data.nlargest(10, "Salary")[["Name", "Salary", "City", "Performance_Score", "Department_Name"]]
st.dataframe(top_paid)

# Visualization: Tenure vs Salary by Department
# Visualization: Average Salary by Department and Tenure (Bar Chart)
st.subheader("Average Salary by Department and Tenure")
avg_salary_dept_tenure = filtered_data.groupby(["Department_Name", "Tenure"])["Salary"].mean().reset_index()
bar_fig = px.bar(
    avg_salary_dept_tenure,
    x="Department_Name",
    y="Salary",
    color="Tenure",
    title="Average Salary by Department and Tenure",
    barmode="group"
)
st.plotly_chart(bar_fig)



# Create Age Groups
filtered_data["Age_Group"] = pd.cut(filtered_data["Age"], bins=[20, 30, 40, 50, 60, 70], labels=["20-30", "30-40", "40-50", "50-60", "60-70"])

# Grouping and calculating the average performance score by Age Group
st.subheader("Average Performance Score by Age Group")
avg_perf_age_group = filtered_data.groupby("Age_Group", observed=False)["Performance_Score"].mean().reset_index()

# Create a bar chart
age_perf_fig = px.bar(
    avg_perf_age_group,
    x="Age_Group",
    y="Performance_Score",
    title="Average Performance Score by Age Group",
    color="Performance_Score",
    color_continuous_scale="Viridis"
)
st.plotly_chart(age_perf_fig)

# Visualization: Join Date Distribution
st.subheader("Join Date Distribution")
join_date_fig = px.histogram(
    filtered_data,
    x="Join_Date",
    title="Join Date Distribution",
    nbins=30,
    color="Gender"
)
st.plotly_chart(join_date_fig)

# Visualization: Performance Score vs Working Hours
st.subheader("Performance Score vs Working Hours")
working_hours_perf_fig = px.scatter(
    filtered_data,
    x="Working_Hours",
    y="Performance_Score",
    color="Gender",
    hover_data=["Name", "City"],
    title="Performance Score vs Working Hours"
)
st.plotly_chart(working_hours_perf_fig)

# Correlation between Salary and Performance Score
st.subheader("Correlation Analysis")
numeric_data = filtered_data.select_dtypes(include=['number'])
correlation = numeric_data.corr()
st.write("### Correlation between Salary and Performance Score")
st.write(correlation.loc['Salary', 'Performance_Score'])

# Check if 'Performance_Score' exists and is numeric
if 'Performance_Score' in filtered_data.columns:
    # Convert to numeric if necessary (handling any potential non-numeric values)
    filtered_data['Performance_Score'] = pd.to_numeric(filtered_data['Performance_Score'], errors='coerce')
    
    # Calculate the variance, excluding NaN values
    performance_variance = filtered_data['Performance_Score'].var()
    
    # Display the result
    st.write(f"### Variance of Performance Score: {performance_variance:.2f}")
else:
    st.write("### Performance_Score column is missing.")

# Display Filtered Data
st.write("### Filtered Data")
st.dataframe(filtered_data)

# Close the connection
conn.close()
