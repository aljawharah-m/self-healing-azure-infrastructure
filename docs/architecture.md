# Architecture Notes

This document describes the architecture of the Self-Healing Azure Infrastructure project.

## Infrastructure Layer

The environment is deployed on Microsoft Azure using Terraform.

Main components:

- Azure Virtual Network (VNet)
- Azure Network Security Group (NSG)
- Azure Load Balancer
- Azure Virtual Machine Scale Set (VMSS)
- Public IP Address

Traffic enters through the Public IP and Azure Load Balancer before being distributed across VM Scale Set instances running inside the Virtual Network.

## Monitoring Layer

A Python monitoring service continuously evaluates:

- Website availability
- Azure Monitor CPU metrics
- VM Scale Set capacity

The monitoring engine collects telemetry from Azure Monitor and analyzes the infrastructure health state.

## Recovery Layer

When an incident is detected, the monitoring engine automatically:

1. Identifies the failure condition.
2. Determines the required remediation action.
3. Attempts VM Scale Set scaling.
4. Verifies recovery status.
5. Sends Telegram notifications.

## Failure Handling

The system includes error-handling logic for Azure platform limitations such as regional quota restrictions.

If automated recovery cannot be completed successfully, the failure is logged and reported while monitoring continues uninterrupted.
