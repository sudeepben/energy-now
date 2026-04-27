from pathlib import Path
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

GPU_FILE = DATA_DIR / "gpu_timeseries.csv"
CLUSTER_FILE = DATA_DIR / "cluster_timeseries.csv"
OUTPUT_FILE = DATA_DIR / "compute_latest.csv"


def load_data():
    gpu_df = pd.read_csv(GPU_FILE)
    cluster_df = pd.read_csv(CLUSTER_FILE)
    return gpu_df, cluster_df


def clean_gpu_data(gpu_df: pd.DataFrame) -> pd.DataFrame:
    gpu_df = gpu_df.copy()
    gpu_df["timestamp"] = pd.to_datetime(gpu_df["timestamp"])
    gpu_df["board_power_kw"] = gpu_df["board_power_w"] / 1000.0
    return gpu_df


def clean_cluster_data(cluster_df: pd.DataFrame) -> pd.DataFrame:
    cluster_df = cluster_df.copy()
    cluster_df["timestamp"] = pd.to_datetime(cluster_df["timestamp"])

    # Helper time columns
    cluster_df["hour"] = cluster_df["timestamp"].dt.floor("h")
    cluster_df["date"] = cluster_df["timestamp"].dt.date

    # Helper feature columns
    cluster_df["cooling_to_it_ratio"] = (
        cluster_df["power_kw_cooling"] / cluster_df["power_kw_it"]
    )

    cluster_df["power_per_token"] = (
        cluster_df["power_kw_total"] / cluster_df["tokens_per_sec"]
    )

    # Battery state bands
    cluster_df["battery_state"] = pd.cut(
        cluster_df["battery_soc_pct"],
        bins=[0, 20, 80, 100],
        labels=["low", "medium", "high"],
        include_lowest=True
    )

    # Thermal risk bands
    cluster_df["thermal_state"] = pd.cut(
        cluster_df["gpu_temp_max_c"],
        bins=[0, 80, 84, 200],
        labels=["normal", "warm", "hot"],
        include_lowest=True
    )

    # Workload bands
    cluster_df["workload_state"] = pd.cut(
        cluster_df["gpu_utilization_pct"],
        bins=[0, 40, 75, 100],
        labels=["low", "medium", "high"],
        include_lowest=True
    )

    return cluster_df


def main():
    print("Loading compute telemetry files...")
    gpu_df, cluster_df = load_data()

    print("Cleaning GPU data...")
    gpu_df = clean_gpu_data(gpu_df)

    print("Cleaning cluster data...")
    cluster_df = clean_cluster_data(cluster_df)

    print(f"Saving cleaned compute data to: {OUTPUT_FILE}")
    cluster_df.to_csv(OUTPUT_FILE, index=False)

    print("\nDone.")
    print("GPU shape:", gpu_df.shape)
    print("Cluster shape:", cluster_df.shape)
    print("Output shape:", cluster_df.shape)
    print("\nOutput columns:")
    print(cluster_df.columns.tolist())

    print("\nFirst 5 rows of cleaned compute data:")
    print(cluster_df.head())


if __name__ == "__main__":
    main()