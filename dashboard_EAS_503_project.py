import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px


# Connect to the database
conn = sqlite3.connect('employee_database.db')


# Helper function to fetch data from SQL
def fetch_data(query):
    try:
        return pd.read_sql_query(query, conn)
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return pd.DataFrame()


# Load data for analysis
employee_query = "SELECT * FROM Employee"
employee_data = fetch_data(employee_query)

salary_query = "SELECT * FROM Salary"
salary_data = fetch_data(salary_query)

performance_query = "SELECT * FROM Performance"
performance_data = fetch_data(performance_query)

# Merge datasets for easier exploration
merged_data_query = """
SELECT e.Employee_ID, e.Name, e.Gender, e.Age, e.City, e.Country, e.Join_Date, e.Tenure,
       s.Salary, s.Annual_Bonus, s.Bonus_Percentage,
       p.Performance_Score, p.Working_Hours
FROM Employee e
JOIN Salary s ON e.Employee_ID = s.Employee_ID
JOIN Performance p ON e.Employee_ID = p.Employee_ID
"""
merged_data = fetch_data(merged_data_query)

# Streamlit Dashboard
st.title("Employee Data Analysis Dashboard")

# Sidebar Filters
st.sidebar.header("Filters")
selected_gender = st.sidebar.multiselect("Select Gender", options=employee_data["Gender"].unique(), default=employee_data["Gender"].unique())
selected_city = st.sidebar.multiselect("Select City", options=employee_data["City"].unique(), default=employee_data["City"].unique())
selected_salary_range = st.sidebar.slider("Select Salary Range", 
                                           min_value=float(salary_data["Salary"].min()), 
                                           max_value=float(salary_data["Salary"].max()), 
                                           value=(float(salary_data["Salary"].min()), float(salary_data["Salary"].max())))

# Handle NaN values by filtering out rows with NaN in relevant columns (Salary, Performance_Score, etc.)
merged_data = merged_data.dropna(subset=["Salary", "Performance_Score", "Working_Hours"])

# Apply Filters
filtered_data = merged_data[
    (merged_data["Gender"].isin(selected_gender)) &
    (merged_data["City"].isin(selected_city)) &
    (merged_data["Salary"].between(selected_salary_range[0], selected_salary_range[1]))
]

# Dynamic Metrics
st.subheader("Key Metrics")
col1, col2, col3 = st.columns(3)
col1.metric("Total Employees", len(filtered_data))
col2.metric("Average Salary", f"${filtered_data['Salary'].mean():,.2f}")
col3.metric("Average Performance Score", f"{filtered_data['Performance_Score'].mean():.2f}")

# Visualization 1: Gender Distribution
st.subheader("Gender Distribution")
gender_fig = px.pie(filtered_data, names='Gender', title='Gender Distribution', color_discrete_sequence=px.colors.sequential.RdBu)
st.plotly_chart(gender_fig)

# Visualization 2: Salary vs Performance Score
st.subheader("Salary vs Performance Score")
salary_perf_fig = px.scatter(
    filtered_data,
    x="Salary", 
    y="Performance_Score",
    color="Gender",
    size="Working_Hours",
    hover_data=["Name", "Age", "City"],
    title="Salary vs Performance Score"
)
st.plotly_chart(salary_perf_fig)

# Visualization 3: Average Salary by City
st.subheader("Average Salary by City")
avg_salary_city = filtered_data.groupby("City")["Salary"].mean().reset_index()
city_salary_fig = px.bar(avg_salary_city, x="City", y="Salary", title="Average Salary by City", color="Salary")
st.plotly_chart(city_salary_fig)

# Visualization 4: Performance Score Distribution
st.subheader("Performance Score Distribution")
score_fig = px.histogram(filtered_data, x="Performance_Score", nbins=10, color="Gender", title="Performance Score Distribution")
st.plotly_chart(score_fig)

# Display Filtered Data
st.write("### Filtered Data")
st.dataframe(filtered_data)
