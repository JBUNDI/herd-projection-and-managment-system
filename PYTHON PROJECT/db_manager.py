import sqlite3
import pandas as pd
from datetime import datetime
import numpy as np 
import io # NEW IMPORT to handle in-memory file data

# --- IMPORTANT CONSTANTS ---
DB_NAME = 'cattle_db.sqlite'

def get_db_connection():
    """Returns a connection object to the SQLite database."""
    return sqlite3.connect(DB_NAME)

def initialize_db():
    """Creates the necessary tables if they don't exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # --- Cow Table ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cows (
            cow_id TEXT PRIMARY KEY,
            sex TEXT NOT NULL,
            birth_date TEXT NOT NULL,
            status TEXT NOT NULL,  -- e.g., Active, Sold, Dead
            mother_id TEXT,
            breed TEXT
        )
    """)
    
    # --- Events Table ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS events (
            event_id INTEGER PRIMARY KEY AUTOINCREMENT,
            cow_id TEXT NOT NULL,
            event_type TEXT NOT NULL, -- e.g., Birth, Death, Sale, Vet
            event_date TEXT NOT NULL,
            details TEXT,
            FOREIGN KEY(cow_id) REFERENCES cows(cow_id)
        )
    """)
    
    # --- Projections Table ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS projections (
            proj_id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_date TEXT NOT NULL,
            B0_start INTEGER,
            Y0_start INTEGER,
            C_param REAL,
            m_param REAL,
            projection_data_json TEXT -- Store the DataFrame as JSON
        )
    """)
    
    conn.commit()
    conn.close()

# --- CRUD Functions (CRUD functions remain unchanged) ---

def add_new_cow(cow_id: str, sex: str, birth_date: str, mother_id: str = None, breed: str = 'N/A') -> bool:
    """Adds a new cow record to the 'cows' table."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO cows (cow_id, sex, birth_date, status, mother_id, breed) VALUES (?, ?, ?, ?, ?, ?)",
            (cow_id, sex, birth_date, 'Active', mother_id, breed)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False 
    finally:
        conn.close()

def log_event(cow_id: str, event_type: str, details: str = ""):
    """Logs an event and updates the cow's status if needed."""
    conn = get_db_connection()
    cursor = conn.cursor()
    event_date = datetime.now().strftime("%Y-%m-%d")
    
    try:
        cursor.execute("INSERT INTO events (cow_id, event_type, event_date, details) VALUES (?, ?, ?, ?)",
                       (cow_id, event_type, event_date, details))

        if event_type in ('Death', 'Sale'):
            cursor.execute("UPDATE cows SET status = ? WHERE cow_id = ?", (event_type, cow_id))
            
        conn.commit()
    except Exception as e:
        print(f"Error logging event: {e}") 
    finally:
        conn.close()

def save_projection(B0, Y0, C, m, proj_df: pd.DataFrame):
    """Saves a completed projection run to the 'projections' table."""
    conn = get_db_connection()
    run_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    proj_json = proj_df.to_json(orient='split') 
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO projections (run_date, B0_start, Y0_start, C_param, m_param, projection_data_json)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (run_date, B0, Y0, C, m, proj_json))
        conn.commit()
    except Exception as e:
        print(f"Error saving projection: {e}")
    finally:
        conn.close()

def get_all_projections() -> pd.DataFrame:
    """Retrieves metadata of all saved projections."""
    conn = get_db_connection()
    try:
        df = pd.read_sql_query("SELECT proj_id, run_date, B0_start, Y0_start, C_param, m_param FROM projections ORDER BY run_date DESC", conn)
    except Exception as e:
        print(f"Error fetching projections: {e}")
        df = pd.DataFrame(columns=['proj_id', 'run_date', 'B0_start', 'Y0_start', 'C_param', 'm_param'])
    finally:
        conn.close()
    return df

def get_projection_data(proj_id: int) -> pd.DataFrame:
    """Retrieves a specific projection's full DataFrame."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT projection_data_json FROM projections WHERE proj_id = ?", (proj_id,))
        result = cursor.fetchone()
    finally:
        conn.close()
    
    if result and result[0]:
        return pd.read_json(result[0], orient='split')
    return pd.DataFrame()

def get_all_cows() -> pd.DataFrame:
    """Fetches all cow records for display."""
    conn = get_db_connection()
    try:
        df = pd.read_sql_query("SELECT cow_id, sex, birth_date, status, mother_id, breed FROM cows ORDER BY birth_date DESC", conn)
    except Exception as e:
        print(f"Error fetching cows: {e}")
        df = pd.DataFrame(columns=['cow_id', 'sex', 'birth_date', 'status', 'mother_id', 'breed'])
    finally:
        conn.close()
    return df

# --- CRITICAL FUNCTION: Updated to accept uploaded CSV data ---
def get_actual_herd_counts(years_horizon: int, csv_data: bytes) -> pd.DataFrame:
    """
    Reads actual historical data from a bytes object (from st.file_uploader in app.py). 
    It aligns the data to the projection horizon, using np.nan for future/missing years.
    """
    
    # Check if data was provided by the uploader in app.py
    if csv_data is None:
        # Return a safe, empty DataFrame covering the full horizon
        return pd.DataFrame({'Year': range(years_horizon + 1), 'Actual_Total': [np.nan] * (years_horizon + 1)})

    try:
        # Decode the bytes object into a string buffer for pandas to read
        data_string_io = io.StringIO(csv_data.decode('utf-8'))
        actual_data_df = pd.read_csv(data_string_io)
        
        # Ensure 'Year' and 'Actual_Total' columns exist
        if 'Year' not in actual_data_df.columns or 'Actual_Total' not in actual_data_df.columns:
             print("ERROR: CSV file missing 'Year' or 'Actual_Total' columns. Check the file format.")
             return pd.DataFrame({'Year': range(years_horizon + 1), 'Actual_Total': [np.nan] * (years_horizon + 1)})

        # Prepare for merging/reindexing
        actual_data_df = actual_data_df.set_index('Year')
        
        # 3. Create a complete index for the full projection time span
        full_index = pd.Index(range(years_horizon + 1), name='Year')
        
        # 4. Reindex to align data. Future years get 'NaN'.
        final_df = actual_data_df.reindex(full_index)
        final_df = final_df.reset_index()

        return final_df[['Year', 'Actual_Total']]

    except Exception as e:
        print(f"Error loading and processing uploaded CSV data: {e}")
        # Return safe empty data if there is a file format error
        return pd.DataFrame({'Year': range(years_horizon + 1), 'Actual_Total': [np.nan] * (years_horizon + 1)})

# --- Initialize Database on Start-up ---
initialize_db()
