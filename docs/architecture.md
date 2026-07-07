# Architecture Notes

This document describes the high-level architecture of the self-healing Azure infrastructure.

Traffic flows from the public IP to the Azure Load Balancer, then to the VM Scale Set instances inside the Virtual Network. A Python monitoring script checks infrastructure metrics and triggers Terraform remediation when scaling is required.