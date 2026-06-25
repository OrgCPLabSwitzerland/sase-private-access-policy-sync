# SASE Private Access Policy Sync

## Overview

SASE Private Access Policy Sync is a SmartConsole extension backend that automates synchronization of Check Point Access Policies to Check Point SASE.

### Key Features

* Fetch rulebases from a centralized Check Point Management Server
* Map Check Point rules to Check Point SASE format
* Validate policies before deployment
* Push policies to selected SASE networks

---

# Architecture

* **SmartConsole** → Loads extension UI and triggers actions
* **Backend Service** → Processes rulebase and communicates with APIs
* **Check Point Management Server** → Source of rulebase data
* **Check Point SASE** → Target system for policy deployment

---

# Requirements

## System Requirements

* Linux server (Ubuntu recommended)
* Python 3.10+
* Access to Check Point Management API
* Check Point SASE API credentials

## Connectivity Requirements

The backend must be reachable from:

* SmartConsole client
* Check Point Management Server

Required endpoint:

```text id="xq9m0v"
https://<SERVER>:5000
```

Used for:

* Loading SmartConsole extension (`extension.json`)
* Backend API communication (validate/install)
* UI interaction from SmartConsole

---

# SmartConsole Prerequisites

Before using the extension, create the following in SmartConsole:

## Policy Package

```text id="p1a9kd"
SASE-Private-Access
```

## Inline Layer

```text id="l9c2qp"
SASE-Private-Access-Layer
```

> ⚠️ The layer name must match exactly or rulebase extraction will fail.

---

# Installation

## 1. Clone Repository

```bash id="c8q2lm"
git clone <repository-url>
cd sase-unified-pa-policy
```

## 2. Run Setup (Recommended)

The setup script prepares everything automatically:

```bash id="s3n9aa"
chmod +x setup.sh
./setup.sh
```

What it does:

* Creates Python virtual environment
* Installs dependencies
* Generates `config/config.json` from template (if missing)
* Generates `frontend/extension.json` from template (if missing)

---

## 3. Start Backend

```bash id="z2m8kd"
chmod +x start.sh
./start.sh
```

---

# Post-Setup Configuration

## Config File

After first run (if not already present), update:

```text id="c9x2aa"
config/config.json
```

Add:

* Check Point Management API credentials
* SASE API credentials
* Backend configuration values

---

## Extension Configuration

Ensure this file contains correct backend URL:

```text id="e8k3lp"
frontend/extension.json
```

Replace:

```text
https://<YOUR-SERVER>:5000
```

with your actual server hostname or IP.

---

# SmartConsole Extension Setup

## Register Extension

1. Open SmartConsole
2. Navigate to:

   ```
   Manage & Settings → Extensions
   ```
3. Click:

   ```
   Add → From URL
   ```
4. Enter:

   ```
   https://<SERVER>:5000/extension.json
   ```
5. Click **Add**

---

## Result

A new tab will appear:

**Install SASE Policy**

Located in the Access Policy section.

---

# Troubleshooting

## Extension Not Loading

Check:

```text id="t4q1zz"
https://<SERVER>:5000/extension.json
```

## Backend Issues

* Check backend logs
* Ensure port `5000` is open
* Ensure server is reachable from SmartConsole

## Certificate Issues

If using self-signed certificates:

* SmartConsole must trust the certificate
* HTTPS must be correctly configured

---

# Quick Start

```bash id="q1w8zx"
git clone <repository-url>
cd sase-unified-pa-policy

chmod +x setup.sh start.sh

./setup.sh
./start.sh
```

---

# Notes

* The backend does **not** run on the Management Server
* SmartConsole communicates directly with backend via HTTPS
* `setup.sh` handles environment initialization automatically
