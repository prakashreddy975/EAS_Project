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

# Removed department query since it's not used in the analysis
# department_query = "SELECT * FROM Department"
# department_data = fetch_data(department_query)

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
filtered_data['Salary'] = pd.to_numeric(filtered_data['Salary'], errors='coerce')
filtered_data['Performance_Score'] = pd.to_numeric(filtered_data['Performance_Score'], errors='coerce')
filtered_data['Tenure'] = pd.to_numeric(filtered_data['Tenure'], errors='coerce')
filtered_data['Working_Hours'] = pd.to_numeric(filtered_data['Working_Hours'], errors='coerce')

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

# Visualization 3: Average Salary by Country
st.subheader("Average Salary by Country")
avg_salary_country = filtered_data.groupby("Country")["Salary"].mean().reset_index()
country_salary_fig = px.bar(
    avg_salary_country,
    x="Country",
    y="Salary",
    title="Average Salary by Country",
    color="Salary",
    color_continuous_scale="Blues"
)
st.plotly_chart(country_salary_fig)

# Visualization 4: Performance Score Distribution by Gender
st.subheader("Performance Score Distribution by Gender")
score_fig = px.box(
    filtered_data,
    x="Gender",
    y="Performance_Score",
    color="Gender",
    title="Performance Score Distribution by Gender",
    boxmode="overlay"
)
st.plotly_chart(score_fig)

# Visualization 5: Tenure Distribution by Gender
st.subheader("Tenure Distribution by Gender")
tenure_fig = px.histogram(
    filtered_data,
    x="Tenure",
    color="Gender",
    title="Tenure Distribution by Gender",
    nbins=20,
    barmode="overlay",
    opacity=0.7
)
st.plotly_chart(tenure_fig)

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

# Top 10 Highest Paid Employees
st.subheader("Top 10 Highest Paid Employees")
top_paid = filtered_data.nlargest(10, "Salary")[["Name", "Salary", "City", "Performance_Score"]]
st.dataframe(top_paid)

# Visualization: Tenure vs Salary
st.subheader("Tenure vs Salary")
tenure_salary_fig = px.scatter(
    filtered_data,
    x="Tenure",
    y="Salary",
    color="Gender",
    hover_data=["Name", "City"],
    title="Tenure vs Salary"
)
st.plotly_chart(tenure_salary_fig)

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
