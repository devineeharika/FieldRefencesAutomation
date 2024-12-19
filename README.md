## Setup Instructions

### Step 1: Run the SOQL Query in Salesforce Workbench

1. Log in to **Salesforce Workbench**.
2. Navigate to **SOQL Query**.
3. Execute the following query to extract the required fields for the `Contact` object:

   ```sql
   SELECT DurableId, QualifiedApiName
   FROM FieldDefinition 
   WHERE EntityDefinition.QualifiedApiName = 'Contact' AND DurableId LIKE 'Contact.00%'
   ORDER BY Label
   ```
4. Export the query results as a CSV file (e.g., sandbox_390.csv).

### Step 2: Install Required Python Packages

1. Open a terminal in the project directory.

2. Run the command to install the required dependencies:`pip install -r requirements.txt`

### Step 3: Update Configuration in constants.py

1. Open the constants.py file.
2. Locate the num_process variable and set its value based on your system's capabilities. This controls the number of processes that will run in parallel.

### Step 4: Run the Application

1. Start the Streamlit app by running the command:`streamlit run FieldReferences.py`
2. Open the Local URL displayed in the terminal to access the application in your browser.


### Step 5: Use the Application

1. Enter Your Salesforce Credentials:
  - Username
  - Password
  - Security Token
- Upload the Input File: Select the CSV file generated in Step 1 (e.g., sandbox_390.csv).
2. Click the Submit button.
3. The app will process the data and save the results.


