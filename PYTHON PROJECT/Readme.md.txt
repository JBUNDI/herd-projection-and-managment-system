🐂 Fibonacci-based Cattle Herd Projection System

Project Overview

This is a professional, three-part Python application built using Streamlit for the frontend, a modified Fibonacci sequence model for forecasting, and SQLite for data persistence. The system allows farm managers to forecast their female herd growth, log individual animal events, and validate model performance against historical data.

The application adheres to high standards of UI/UX, featuring a clean, horizontal navigation bar, formal icons, and a card-based layout for intuitive use.

🚀 Getting Started

Prerequisites

You need Python 3.8+ installed on your system. This project relies on the following libraries:

streamlit

pandas

numpy

sqlite3 (built-in to Python)

Installation

Clone or Download: Get the project files (app.py, db_manager.py, projection_model.py) into a single directory.

Install Dependencies: Open your terminal or command prompt, navigate to the project directory, and run:

pip install streamlit pandas numpy


Running the Application

From your project directory, execute the Streamlit application:

python -m streamlit run app.py


The application will automatically open in your web browser (usually at http://localhost:8501).

🗃️ File Structure

The system is organized into three Python files:

File Name

Role

Description

app.py

Frontend & Integrator

The main application file. It contains the Streamlit UI, horizontal navigation, and the logic to call functions from the other two modules.

db_manager.py

Data Manager

Handles the creation and management of the SQLite database (cattle_db.sqlite). It manages saving projections and logging individual animal records.

projection_model.py

Core Model

Contains the mathematical functions, including the two-cohort Fibonacci projection algorithm and accuracy calculation (MAE and MAPE).

cattle_db.sqlite

Database File

(Created Automatically) This file is generated the first time the app runs and stores all persistent data.

🛠️ Key Features and Usage

📈 Herd Projection

Input Parameters: Enter your starting herd size (B0, Y0), biological parameters (C, m), and the projection horizon.

Results: Displays results in a Chart (default, graph-first) and a detailed Data Table for analysis.

Data Persistence: Every run is saved to the database for later validation.

📝 Event Logging

Forms: Use simple forms to log new Births (adding a new cow record) or Exits (Death or Sale).

Herd View: Displays the current list of Active cows, including calculated age, for quick management overview.

📊 Comparison Report

Model Validation: Select any saved projection run from the dropdown.

Data Alignment (Bug Fix): Safely compares the saved Projected figures with a sample of Actual herd data (currently mocked) by automatically aligning the dataframes and handling years with no actual data (np.nan).

Accuracy Metrics: Calculates Mean Absolute Error (MAE) and Mean Absolute Percentage Error (MAPE) to quantify model performance.