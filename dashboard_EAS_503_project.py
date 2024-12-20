import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px

# Connect to the updated database
conn = sqlite3.connect('database_employee.db')

# Helper function to fetch data from SQL
def fetch_data(query):
    try:
        return pd.read_sql_query(query, conn)
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return pd.DataFrame()

# Load data for analysis
employee_query = """
SELECT e.Employee_ID, e.Name, e.Gender, e.Age, e.Education, e.Join_Date, 
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
SELECT e.Employee_ID, e.Name, e.Gender, e.Age, e.Education, e.Join_Date, 
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

# Country filter (dropdown with multiple selections)
selected_country = st.sidebar.multiselect(
    "Select Country", 
    options=employee_data["Country"].unique(), 
    default=employee_data["Country"].unique()
)

# City filter (dropdown dependent on selected countries, with multiselect)
cities_in_selected_countries = merged_data[merged_data["Country"].isin(selected_country)]["City"].unique()
selected_cities = st.sidebar.multiselect("Select Cities", options=cities_in_selected_countries)

# Gender filter
selected_gender = st.sidebar.multiselect("Select Gender", options=employee_data["Gender"].unique(), default=employee_data["Gender"].unique())

# Salary range filter
selected_salary_range = st.sidebar.slider(
    "Select Salary Range", 
    min_value=float(salary_data["Salary"].min()), 
    max_value=float(salary_data["Salary"].max()), 
    value=(float(salary_data["Salary"].min()), float(salary_data["Salary"].max()))
)

# Age range filter
min_age = int(merged_data["Age"].min())
max_age = int(merged_data["Age"].max())

selected_age_range = st.sidebar.slider(
    "Select Age Range", 
    min_value=min_age, 
    max_value=max_age, 
    value=(min_age, max_age)
)

# Apply Filters
filtered_data = merged_data[
    (merged_data["Gender"].isin(selected_gender)) &
    (merged_data["City"].isin(selected_cities)) &  # Updated to handle multiple cities
    (merged_data["Country"].isin(selected_country)) &  # Updated to handle multiple countries
    (merged_data["Salary"].between(selected_salary_range[0], selected_salary_range[1])) &
    (merged_data["Age"].between(selected_age_range[0], selected_age_range[1]))  # Filtering based on age range
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

# Visualization 2: Salary vs Performance Score Comparison
filtered_data.loc[:, 'Salary'] = pd.to_numeric(filtered_data['Salary'], errors='coerce')
filtered_data.loc[:, 'Performance_Score'] = pd.to_numeric(filtered_data['Performance_Score'], errors='coerce')
filtered_data.loc[:, 'Working_Hours'] = pd.to_numeric(filtered_data['Working_Hours'], errors='coerce')

# Drop rows with any NaN values in the relevant columns
filtered_data = filtered_data.dropna(subset=['Salary', 'Performance_Score', 'Working_Hours'])

# Now proceed to plot
st.subheader("Performance Score by Salary")
salary_perf_fig = px.scatter(
    filtered_data,
    x="Salary",
    y="Performance_Score",
    size="Working_Hours",  # Ensure Working_Hours is numeric
    hover_data=["Name", "Age", "City", "Gender"],
    title="Salary vs Performance Score",
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

# Visualization: Average Salary by Department (Matplotlib Bar Chart)
st.subheader("Average Salary by Department (Matplotlib)")
avg_salary_by_dept = pd.read_sql_query("""
    SELECT Department.Department_Name, AVG(Salary.Salary) AS Avg_Salary
    FROM Employee_Department
    INNER JOIN Department ON Employee_Department.Department_ID = Department.Department_ID
    INNER JOIN Salary ON Employee_Department.Employee_ID = Salary.Employee_ID
    GROUP BY Department.Department_Name;
""", conn)

fig1, ax1 = plt.subplots()
sns.barplot(data=avg_salary_by_dept, x='Department_Name', y='Avg_Salary', ax=ax1)
ax1.set_title('Average Salary by Department')
ax1.set_xlabel('Department')
ax1.set_ylabel('Average Salary')
plt.xticks(rotation=45)
st.pyplot(fig1)  # Display the Matplotlib figure in Streamlit

# Visualization: Salary vs Performance Score (Matplotlib Scatter Plot)
st.subheader("Salary vs Performance Score (Matplotlib)")
salary_df = pd.read_sql_query("""
    SELECT Salary.Employee_ID, Salary.Salary, Performance.Performance_Score 
    FROM Salary 
    INNER JOIN Performance ON Salary.Employee_ID = Performance.Employee_ID;
""", conn)

fig2, ax2 = plt.subplots()
sns.scatterplot(data=salary_df, x='Performance_Score', y='Salary', ax=ax2)
ax2.set_title('Salary vs Performance Score')
ax2.set_xlabel('Performance Score')
ax2.set_ylabel('Salary')
st.pyplot(fig2)  # Display the Matplotlib figure in Streamlit


# Visualization 6: Correlation Heatmap
st.subheader("Correlation Heatmap")
numeric_data = filtered_data[["Age", "Salary", "Annual_Bonus", "Bonus_Percentage", "Performance_Score", "Working_Hours"]]
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

# Employee Distribution by Department (Pie Chart using Plotly)
st.subheader("Employee Distribution by Department (Pie Chart)")
pie_chart = px.pie(
    empl_dept_data, 
    names='Department_Name', 
    values='Employee_Count', 
    title='Employee Distribution by Department',
    color='Department_Name',  # Color each section differently
    color_discrete_sequence=px.colors.qualitative.Set1  # Valid qualitative color palette
)
st.plotly_chart(pie_chart)

# Top 10 Highest Paid Employees
st.subheader("Top 10 Highest Paid Employees")
top_paid = filtered_data.nlargest(10, "Salary")[["Name", "Salary", "City", "Performance_Score", "Department_Name"]]
st.dataframe(top_paid)

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

# Display the variance in Performance Score
performance_variance = filtered_data['Performance_Score'].var()
st.write(f"### Variance in Performance Score: {performance_variance:.2f}")

# Display Filtered Data
st.write("### Filtered Data")
st.dataframe(filtered_data)

# Close the connection
conn.close()
