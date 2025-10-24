import numpy as np
import pandas as pd

def project_herd_yearly(B0: int, Y0: int, C: float, m: float, years: int) -> pd.DataFrame:
    """
    Implements the modified two-cohort (Breeders B, Juveniles Y) model.
    This function projects the female herd count over a period of 'years'.
    
    B0: Initial Breeders (Adult Females)
    Y0: Initial Juveniles (Young Females)
    C: Female Calves born per Breeder per year (e.g., 0.5 for a 50% female ratio)
    m: Annual Mortality Rate (e.g., 0.05 for 5%)
    years: Projection horizon
    """
    
    # Initialize lists with starting values for Year 0
    B = [B0]
    Y = [Y0]
    
    for n in range(1, years + 1):
        # 1. Calculate new female calves born this year (based on last year's breeders)
        birth_n = C * B[-1]
        
        # 2. Breeders (B) and Juveniles (Y) survive based on mortality rate (1 - m)
        # Next year's Breeders are surviving Breeders plus surviving Juveniles who are now adults
        next_B_raw = (B[-1] * (1 - m)) + (Y[-1] * (1 - m))
        
        # The next year's Juveniles are the survivors of the new calves born this year.
        next_Y_raw = birth_n * (1 - m)
        
        # Round to the nearest integer for cattle counts
        next_B = int(np.round(next_B_raw))
        next_Y = int(np.round(next_Y_raw))
        
        B.append(next_B)
        Y.append(next_Y)

    # Compile results into a DataFrame
    df = pd.DataFrame({
        'Year': range(years + 1),
        'Breeders (Projected)': B,
        'Juveniles (Projected)': Y,
        'Total Females (Projected)': np.array(B) + np.array(Y)
    })
    
    return df

def calculate_error(projected_counts: list, actual_counts: list) -> tuple[float, float]:
    """
    Calculates Mean Absolute Error (MAE) and Mean Absolute Percentage Error (MAPE).
    """
        
    projected = np.array(projected_counts)
    actual = np.array(actual_counts)

    # 1. Mean Absolute Error (MAE)
    mae = np.mean(np.abs(projected - actual))
    
    # 2. Mean Absolute Percentage Error (MAPE) - Handle division by zero
    valid_mask = actual != 0
    
    if not np.any(valid_mask):
        return mae, 0.0 
        
    percentage_errors = np.abs(projected[valid_mask] - actual[valid_mask]) / actual[valid_mask]
    mape = np.mean(percentage_errors) * 100
    
    return mae, mape
