import os
import subprocess
from datetime import datetime, timedelta, timezone

from azure.identity import DefaultAzureCredential
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.monitor import MonitorManagementClient


SUBSCRIPTION_ID = os.getenv("AZURE_SUBSCRIPTION_ID")

RESOURCE_GROUP = "rg-selfhealing-network"
VMSS_NAME = "selfhealing-vmss"

CPU_THRESHOLD = 70.0  # Use 5.0 for demo/testing
MAX_INSTANCES = 3
LOOKBACK_MINUTES = 10


def require_environment():
    if not SUBSCRIPTION_ID:
        raise RuntimeError("AZURE_SUBSCRIPTION_ID is not set.")


def get_vmss_resource_id():
    return (
        f"/subscriptions/{SUBSCRIPTION_ID}"
        f"/resourceGroups/{RESOURCE_GROUP}"
        f"/providers/Microsoft.Compute/virtualMachineScaleSets/{VMSS_NAME}"
    )


def get_average_cpu():
    credential = DefaultAzureCredential()
    monitor_client = MonitorManagementClient(credential, SUBSCRIPTION_ID)

    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(minutes=LOOKBACK_MINUTES)

    response = monitor_client.metrics.list(
        get_vmss_resource_id(),
        timespan=f"{start_time.strftime('%Y-%m-%dT%H:%M:%SZ')}/{end_time.strftime('%Y-%m-%dT%H:%M:%SZ')}",
        interval="PT1M",
        metricnames="Percentage CPU",
        aggregation="Average",
    )

    samples = []

    for metric in response.value:
        for timeseries in metric.timeseries:
            for point in timeseries.data:
                if point.average is not None:
                    samples.append(point.average)

    if not samples:
        return 0.0

    return sum(samples) / len(samples)


def get_current_instance_count():
    credential = DefaultAzureCredential()
    compute_client = ComputeManagementClient(credential, SUBSCRIPTION_ID)

    vmss = compute_client.virtual_machine_scale_sets.get(
        RESOURCE_GROUP,
        VMSS_NAME,
    )

    return int(vmss.sku.capacity)


def run_terraform_scale(new_count):
    terraform_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "terraform")
    )

    command = [
        "terraform",
        "apply",
        "-auto-approve",
        f"-var=instance_count={new_count}",
    ]

    subprocess.run(command, cwd=terraform_dir, check=True)


def self_healing_decision(cpu_average, current_instances):
    if cpu_average >= CPU_THRESHOLD and current_instances < MAX_INSTANCES:
        return current_instances + 1

    return current_instances


def main():
    require_environment()

    print("Self-Healing Network Infrastructure Monitor")
    print("--------------------------------------------------")

    cpu_average = get_average_cpu()
    current_instances = get_current_instance_count()
    desired_instances = self_healing_decision(cpu_average, current_instances)

    print(f"Average CPU: {cpu_average:.2f}%")
    print(f"Current instances: {current_instances}")
    print(f"Desired instances: {desired_instances}")

    if desired_instances > current_instances:
        print("Bottleneck detected. Starting automated remediation...")
        run_terraform_scale(desired_instances)
        print("Remediation completed successfully.")
    else:
        print("System is healthy. No remediation required.")


if __name__ == "__main__":
    main()