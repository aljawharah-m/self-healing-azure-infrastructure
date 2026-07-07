# Intelligent Self-Healing Cloud Infrastructure using Azure, Terraform and Python

## Overview

This project focuses on building a self-healing cloud infrastructure on Microsoft Azure using Terraform and Python.

The infrastructure monitors resource performance and automatically performs remediation actions when predefined thresholds are exceeded. The goal is to improve availability and reduce manual intervention through automation.

## Technologies

- Microsoft Azure
- Terraform
- Python
- Azure VM Scale Sets
- Azure Load Balancer
- Azure Virtual Network (VNet)
- Network Security Groups (NSG)
- Ubuntu Linux

## Architecture

User
→ Public IP
→ Azure Load Balancer
→ VM Scale Set
→ Virtual Network
→ Network Security Group

Monitoring Engine (Python)
→ Terraform Remediation
→ Infrastructure Scaling

## Infrastructure Components

### VM Scale Set

Used to provide scalable compute resources and support automatic scaling during remediation.

### Load Balancer

Distributes incoming traffic across available virtual machine instances.

### Virtual Network

Provides connectivity between Azure resources.

### Network Security Group

Controls network access using security rules.

### Python Monitoring Script

Monitors infrastructure metrics and determines when remediation actions are required.

### Terraform

Deploys and manages Azure infrastructure using Infrastructure as Code principles.

## Workflow

1. Monitor infrastructure metrics.
2. Detect performance bottlenecks.
3. Trigger remediation automatically.
4. Update infrastructure using Terraform.
5. Scale VM instances when needed.
6. Maintain service availability.

## Results

### Initial State

- VMSS instances: 1

### Event Detected

- Bottleneck detected
- Remediation triggered

### Final State

- VMSS instances: 2
- Load Balancer backend updated
- Service remained available

## Screenshots

- Resource Group Overview
- Virtual Network Overview
- Load Balancer Overview
- VM Scale Set Overview
- VM Scale Set Instances
- Bottleneck Detection
- Terraform Scaling Plan
- Remediation Success
- Website Health Verification

## Author

Al-Jawhara Mohammed Alsumayri

Computer Engineering & Networks  
Umm Al-Qura University

Email: jojo.alsumayri@gmail.com

GitHub: https://github.com/aljohara-m

LinkedIn: https://www.linkedin.com/in/aljawharah-alsumayri-219265375/