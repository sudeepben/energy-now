from pathlib import Path
import pandas as pd

# Project paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

gpu_file = DATA_DIR / "gpu_timeseries.csv"
cluster_file = DATA_DIR / "cluster_timeseries.csv"

print("GPU file path:", gpu_file)
print("Cluster file path:", cluster_file)

print("\nChecking if files exist...")
print("gpu_timeseries.csv exists:", gpu_file.exists())
print("cluster_timeseries.csv exists:", cluster_file.exists())

if not gpu_file.exists() or not cluster_file.exists():
    raise FileNotFoundError(
        "Make sure gpu_timeseries.csv and cluster_timeseries.csv are placed inside the data folder."
    )

# Load files
gpu_df = pd.read_csv(gpu_file)
cluster_df = pd.read_csv(cluster_file)

# Print summary
print("\n" + "=" * 60)
print("GPU DATA")
print("=" * 60)
print("Shape:", gpu_df.shape)
print("\nColumns:")
print(gpu_df.columns.tolist())
print("\nFirst 5 rows:")
print(gpu_df.head())
print("\nData types:")
print(gpu_df.dtypes)
print("\nMissing values:")
print(gpu_df.isnull().sum())

print("\n" + "=" * 60)
print("CLUSTER DATA")
print("=" * 60)
print("Shape:", cluster_df.shape)
print("\nColumns:")
print(cluster_df.columns.tolist())
print("\nFirst 5 rows:")
print(cluster_df.head())
print("\nData types:")
print(cluster_df.dtypes)
print("\nMissing values:")
print(cluster_df.isnull().sum())