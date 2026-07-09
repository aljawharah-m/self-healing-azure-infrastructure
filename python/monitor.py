import os
import urllib.request
import requests
from datetime import datetime, timedelta, timezone

from azure.core.exceptions import HttpResponseError
from azure.identity import DefaultAzureCredential
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.monitor import MonitorManagementClient


SUBSCRIPTION_ID = os.getenv("AZURE_SUBSCRIPTION_ID")

RESOURCE_GROUP = "rg-selfhealing-network"
VMSS_NAME = "selfhealing-vmss"

HEALTH_CHECK_URL = os.getenv("HEALTH_CHECK_URL")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

CPU_THRESHOLD = 70.0
MAX_INSTANCES = 3
LOOKBACK_MINUTES = 10
HEALTH_TIMEOUT_SECONDS = 5


def require_environment():
    if not SUBSCRIPTION_ID:
        raise RuntimeError("AZURE_SUBSCRIPTION_ID is not set.")

    if not HEALTH_CHECK_URL:
        raise RuntimeError("HEALTH_CHECK_URL is not set.")


def send_telegram_message(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    try:
        requests.post(
            url,
            json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": message,
            },
            timeout=10,
        )
    except Exception as error:
        print(f"Telegram alert failed: {error}")


def get_vmss_resource_id():
    return (
        f"/subscriptions/{SUBSCRIPTION_ID}"
        f"/resourceGroups/{RESOURCE_GROUP}"
        f"/providers/Microsoft.Compute/virtualMachineScaleSets/{VMSS_NAME}"
    )


def check_website_health():
    try:
        with urllib.request.urlopen(
            HEALTH_CHECK_URL,
            timeout=HEALTH_TIMEOUT_SECONDS,
        ) as response:
            return 200 <= response.status < 400
    except Exception:
        return False


def get_average_cpu():
    credential = DefaultAzureCredential()
    monitor_client = MonitorManagementClient(credential, SUBSCRIPTION_ID)

    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(minutes=LOOKBACK_MINUTES)

    response = monitor_client.metrics.list(
        get_vmss_resource_id(),
        timespan=(
            f"{start_time.strftime('%Y-%m-%dT%H:%M:%SZ')}/"
            f"{end_time.strftime('%Y-%m-%dT%H:%M:%SZ')}"
        ),
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


def scale_vmss_directly(new_count):
    credential = DefaultAzureCredential()
    compute_client = ComputeManagementClient(credential, SUBSCRIPTION_ID)

    vmss = compute_client.virtual_machine_scale_sets.get(
        RESOURCE_GROUP,
        VMSS_NAME,
    )

    current_capacity = int(vmss.sku.capacity)

    if current_capacity >= new_count:
        return {
            "success": True,
            "message": "Already at requested capacity",
        }

    vmss.sku.capacity = new_count

    try:
        poller = compute_client.virtual_machine_scale_sets.begin_create_or_update(
            RESOURCE_GROUP,
            VMSS_NAME,
            vmss,
        )

        poller.result()

        return {
            "success": True,
            "message": f"Scaled successfully to {new_count} instances",
        }

    except HttpResponseError as error:
        error_text = str(error)

        if (
            "Total Regional Cores quota" in error_text
            or "OperationNotAllowed" in error_text
            or "quota" in error_text.lower()
        ):
            return {
                "success": False,
                "message": "Azure quota limit reached",
            }

        return {
            "success": False,
            "message": error_text,
        }

    except Exception as error:
        return {
            "success": False,
            "message": str(error),
        }

# Scale out when the website is unavailable or CPU stays high.

def self_healing_decision(cpu_average, website_healthy, current_instances):
    if not website_healthy and current_instances < MAX_INSTANCES:
        return current_instances + 1, "Website health check failed"

    if cpu_average >= CPU_THRESHOLD and current_instances < MAX_INSTANCES:
        return current_instances + 1, "High CPU bottleneck detected"

    if not website_healthy and current_instances >= MAX_INSTANCES:
        return current_instances, "Website unhealthy, but maximum capacity reached"

    if cpu_average >= CPU_THRESHOLD and current_instances >= MAX_INSTANCES:
        return current_instances, "High CPU detected, but maximum capacity reached"

    return current_instances, "System healthy"


def main():
    require_environment()

    print("Self-Healing Cloud Infrastructure Monitor")
    print("--------------------------------------------------")

    website_healthy = check_website_health()
    cpu_average = get_average_cpu()
    current_instances = get_current_instance_count()

    desired_instances, reason = self_healing_decision(
        cpu_average,
        website_healthy,
        current_instances,
    )

    print(f"Website healthy: {website_healthy}")
    print(f"Average CPU: {cpu_average:.2f}%")
    print(f"Current instances: {current_instances}")
    print(f"Desired instances: {desired_instances}")
    print(f"Decision reason: {reason}")

    if desired_instances > current_instances:
        print("Incident detected. Starting automated recovery...")

        send_telegram_message(
            f"🚨 Incident Detected\n"
            f"Reason: {reason}\n"
            f"CPU: {cpu_average:.2f}%\n"
            f"Current instances: {current_instances}\n"
            f"Target instances: {desired_instances}"
        )

        result = scale_vmss_directly(desired_instances)

        if not result["success"]:
            print(f"Recovery failed: {result['message']}")

            send_telegram_message(
                f"⚠️ Recovery Failed\n"
                f"Reason: {reason}\n"
                f"Error: {result['message']}\n"
                f"Current instances: {current_instances}\n"
                f"Target instances: {desired_instances}"
            )

            return

        print(result["message"])
        print("Verifying recovery...")

        recovered = check_website_health()

        if recovered:
            print("Recovery completed successfully. Website is healthy.")

            send_telegram_message(
                f"✅ Recovery Successful\n"
                f"Website is healthy again.\n"
                f"Instances: {desired_instances}"
            )
        else:
            print("Recovery action completed, but website is still unhealthy.")

            send_telegram_message(
                f"⚠️ Recovery Completed But Website Still Unhealthy\n"
                f"Reason: {reason}\n"
                f"Instances: {desired_instances}"
            )

    elif "maximum capacity reached" in reason:
        print("Incident detected, but maximum capacity has already been reached.")

        send_telegram_message(
            f"⚠️ Incident Detected But Max Capacity Reached\n"
            f"Reason: {reason}\n"
            f"CPU: {cpu_average:.2f}%\n"
            f"Current instances: {current_instances}"
        )

    else:
        print("System is healthy. No recovery required.")


if __name__ == "__main__":
    main()
