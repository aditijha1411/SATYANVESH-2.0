# SATYANVESH
SATYANVESH is an AI-powered digital investigation and decision-support platform that ingests multi-source evidence including CDR, GPS, IPDR, financial and metadata logs, correlates hidden links using knowledge graphs and explainable AI, reconstructs timelines, and generates actionable leads for law enforcement agencies.
# AI-Assisted Case-Centric Digital Investigation Platform
| Version 2.0 | 2025 | Confidential

## Table of Contents
- [Overview](#overview)
- [System Requirements](#system-requirements)
- [Installation & Startup](#installation--startup)
- [Investigation Workflow](#investigation-workflow)
- [Features](#features)
  - [Case Management](#1-case-management)
  - [Evidence Upload & Parsing](#2-evidence-upload--parsing)
  - [Entities & Correlation Engine](#3-entities--correlation-engine)
  - [Relationships Tab](#4-relationships-tab)
  - [AI Leads Generator](#5-ai-leads-generator)
  - [Timeline Analysis](#6-timeline-analysis)
  - [Reports](#7-reports)
  - [Investigation Notebook](#8-investigation-notebook)
- [Supported Evidence Formats](#supported-evidence-formats)
- [API Reference](#api-reference)
- [Troubleshooting](#troubleshooting)


## Overview

SATYANVESH 2.0 is a full-stack AI-assisted digital investigation platform built for law enforcement. It enables investigators to upload, parse, and correlate multi-source digital evidence — CDRs, GPS data, WhatsApp chats, financial records, and more — and automatically surfaces relationships, suspicious patterns, and investigation leads using a built-in AI engine.

**Tech Stack:** Python (FastAPI) · React · PostgreSQL

**Access URLs:**
| URL | Purpose |
|-----|---------|
| `http://localhost:3000` | Main Dashboard (use this for all investigations) |
| `http://127.0.0.1:8000` | Backend API |
| `http://127.0.0.1:8000/docs` | Interactive API Documentation |



## System Requirements

| Component | Requirement |
|-----------|-------------|
| Operating System | Windows 10/11 (64-bit) |
| Python | 3.11.x |
| Node.js | 20+ (LTS) |
| PostgreSQL | 16 |
| RAM | 8 GB minimum |
| Storage | 10 GB free minimum |
| Browser | Google Chrome (recommended) |


## Installation & Startup

### Method 1 — One-Click Script (Recommended)

1. Copy `START_SATYANVESH.ps1` to your Desktop
2. Right-click → **Run with PowerShell**
3. Two terminal windows open automatically (Backend + Frontend)
4. Wait ~15 seconds
5. Open Chrome → `http://localhost:3000`

### Method 2 — Manual Startup

Open **two separate PowerShell windows** and run the following:

**Terminal 1 — Backend:**
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
& c:\Users\aditi\OneDrive\Desktop\SATYANVESH2.0\venv\Scripts\Activate.ps1
cd C:\Users\aditi\OneDrive\Desktop\SATYANVESH2.0\backend
uvicorn main:app --reload
```
Wait for: `Application startup complete.`

**Terminal 2 — Frontend:**
```powershell
$env:PATH += ';C:\Program Files\nodejs'
cd C:\Users\aditi\OneDrive\Desktop\SATYANVESH2.0\frontend
npm start
```
Wait for: `Compiled successfully!`

> ⚠️ **Keep both terminals open** while using SATYANVESH. Closing either will stop the application.

### Access from Phone (Same Wi-Fi)

Run the backend with network binding:
```powershell
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
Find your laptop IP:
```powershell
ipconfig
# Look for IPv4 Address e.g. 192.168.1.5
```
On your phone, open: `http://192.168.1.5:8000`



## Investigation Workflow

```
1. Start both servers  →  2. Create Case  →  3. Upload Evidence
        ↓
4. Parse Evidence  →  5. Load Entities  →  6. Run Correlation
        ↓
7. Review Relationships  →  8. Generate AI Leads  →  9. Analyse Timeline
        ↓
                    10. Export Report / Add Notebook Entries


**Quick Checklist:**
- [ ] Start backend + frontend servers
- [ ] Open `http://localhost:3000`
- [ ] Create a new case (case number, title, description, officer details)
- [ ] Upload all evidence files (CDR, GPS, WhatsApp, Financial, etc.)
- [ ] Parse each evidence file one by one
- [ ] Go to **Entities** tab → Load Entities → verify extraction
- [ ] Click **Run Correlation** → wait for completion
- [ ] Go to **Relationships** tab → review all connections
- [ ] Go to **Leads** tab → Generate AI Leads → review by confidence score
- [ ] Go to **Timeline** tab → Load Timeline → review suspicious patterns
- [ ] Open `http://127.0.0.1:8000/reports/{case_id}/summary` for full report


## Features

### 1. Case Management

Create and manage investigation cases from the Dashboard.

| Field | Description |
|-------|-------------|
| Case Number | Unique identifier e.g. `MURDER-2025-001` |
| Case Title | Short description |
| Description | Detailed case background |
| Officer Name / Badge / Department | Assigned investigator details |

**Case Statuses:**

| Status | Meaning | Badge |
|--------|---------|-------|
| `open` | Active investigation | 🟢 Green |
| `active` | Advanced stage | 🔵 Blue |
| `closed` | Resolved | ⚫ Grey |
| `archived` | Archived for records | 🔘 Dark Grey |



### 2. Evidence Upload & Parsing

All digital evidence is uploaded and parsed before any analysis. SATYANVESH auto-detects evidence type from the filename.

**Steps:**
1. Open a case → click **Evidence** tab
2. Click **Choose File** → select evidence file
3. Click **Upload** (file appears with status `uploaded`)
4. Click **Parse** next to each file → wait for status `parsed` (green)

> **Tip:** Keep filenames descriptive for auto-detection — e.g., `CDR_Suspect_A.xlsx`, `GPS_Device.json`



### 3. Entities & Correlation Engine

Entities (phones, IPs, accounts, locations) are auto-extracted from parsed evidence.

**Entity Types:**

| Type | Source | Example |
|------|--------|---------|
| `phone_number` | CDR, WhatsApp, IPDR | `9441234567` |
| `bank_account` | Financial Records | `ACC001234` |
| `ip_address` | IPDR, Browser History | `192.168.1.101` |
| `url` | Browser History, IPDR | `www.zinkit.in` |
| `email` | Email Records | `suspect@gmail.com` |
| `bluetooth_device` | Bluetooth Logs | `D4:E8:53:AB:12:34` |
| `iot_device` | IoT Logs | `SENSOR-001` |
| `location` | GPS Records | `19.0176,72.8562` |

**Running Correlation:**
1. Go to **Entities** tab → click **Run Correlation** (purple button)
2. The engine analyses all events across evidence sources
3. Results appear in the **Relationships** tab
4. Re-run after uploading new evidence



### 4. Relationships Tab

Displays all connections found by the Correlation Engine.

| Relationship Type | Meaning | Strength |
|-------------------|---------|----------|
| `COMMUNICATED_WITH` | Entities called/messaged each other | Weight = number of communications |
| `CO_LOCATED` | Both entities at same physical location | Weight = number of co-location events |
| `ACTIVE_SAME_TIME` | Both active in the same hour | Weight = number of overlapping hours |
| `SHARED_DEVICE` | Same physical device (IMEI) used | Weight 5+ = very strong (same person?) |


### 5. AI Leads Generator

Automatically generates actionable investigation leads with confidence scores.

**Steps:**
1. Ensure evidence is parsed and correlation has been run
2. Go to **Leads** tab → click **Generate AI Leads** (red button)
3. Leads appear sorted by confidence score (highest first)

**Lead Types:**

| Lead Type | Meaning | Recommended Action |
|-----------|---------|-------------------|
| `HIGH_FREQUENCY_CONTACT` | 5+ communications between entities | Obtain full call records |
| `SHARED_DEVICE` | Two numbers used same phone | Verify dual SIM or accomplice |
| `LOCATION_OVERLAP` | Entities at same physical place | Cross-reference with comms timeline |
| `FINANCIAL_COMMUNICATION_LINK` | Entity appears in both financial and call records | Map transactions vs communications |
| `ACTIVE_ENTITY` | Entity with 3+ recorded events | Build full profile across all evidence |

**Confidence Score:**

| Score | Colour | Reliability |
|-------|--------|-------------|
| 90–100% | 🔴 Red | Very High — strong digital evidence |
| 70–89% | 🟠 Orange | High — multiple sources corroborate |
| 50–69% | 🟡 Yellow | Medium — investigate further |
| Below 50% | ⚫ Grey | Low — background lead |


### 6. Timeline Analysis

Chronological view of all events across all evidence sources with automatic suspicious pattern detection.

**Suspicious Patterns:**

| Pattern | Trigger | Significance |
|---------|---------|-------------|
| `BURST_CALLS` | 5+ calls in same hour | Coordination before/after incident |
| `LATE_NIGHT_ACTIVITY` | 3+ events between 00:00–04:00 | Unusual behaviour |
| `REPEATED_CONTACT` | 10+ contacts between same pair | Planned/strong relationship |
| `CALL_BEFORE_MOVEMENT` | Call + GPS movement in same hour | Possible coordination |
| `ONE_TIME_CONTACT` | Entity appears only once | Possible burner phone |


### 7. Reports

Structured reports accessible via the API while backend is running.

| Report | URL | Contents |
|--------|-----|----------|
| Case Summary | `http://127.0.0.1:8000/reports/{case_id}/summary` | Full overview, statistics, top entities/relationships |
| Entity Report | `http://127.0.0.1:8000/reports/{case_id}/entities` | All entities sorted by activity count |
| Relationships | `http://127.0.0.1:8000/reports/{case_id}/relationships` | All relationships sorted by strength |
| Timeline | `http://127.0.0.1:8000/reports/{case_id}/timeline` | All events in chronological order |

> Open these URLs in your browser and save the JSON response as a report file.


### 8. Investigation Notebook

Record hypotheses, observations, and notes linked to specific evidence and entities.

| Entry Type | Use For |
|------------|---------|
| `HYPOTHESIS` | Investigator theories about the case |
| `OBSERVATION` | Factual notes about evidence or patterns |
| `LEAD` | Investigation directions to follow up |
| `NOTE` | General notes, reminders, meeting minutes |
| `SUSPECT_PROFILE` | Profile notes on identified suspects |

**API:** `POST http://127.0.0.1:8000/notebook/{case_id}/entry`


## Supported Evidence Formats

| Evidence Type | Formats | Auto-Detected By (filename keyword) |
|---------------|---------|--------------------------------------|
| CDR (Call Detail Records) | XLSX, CSV | `cdr`, `call`, `sms`, `msisdn` |
| IPDR (Internet Records) | XLSX, CSV | `ipdr`, `internet`, `data_record` |
| GPS Location Data | CSV, JSON | `gps`, `location`, `track` |
| Browser History | CSV, JSON | `browser`, `history`, `chrome` |
| WhatsApp Chats | CSV, TXT | `whatsapp`, `wa_`, `chat` |
| Financial Records | XLSX, CSV | `bank`, `transaction`, `financial` |
| Bluetooth Logs | CSV | `bluetooth`, `bt_` |
| IoT Device Logs | CSV, XLSX | `iot`, `device`, `sensor` |
| Email Records | CSV, XLSX | `email`, `mail`, `outlook` |
| Images (EXIF) | JPG, PNG, JPEG | File extension `.jpg`, `.png`, `.jpeg` |


## API Reference

Full interactive API documentation is available at `http://127.0.0.1:8000/docs` while the backend is running.


## Troubleshooting

| Problem | Likely Cause | Solution |
|---------|-------------|---------|
| `localhost:3000` not loading | Frontend not running | Open terminal → `cd frontend` → `npm start` |
| Dashboard shows but blank | Backend not running | Open terminal → activate venv → `uvicorn main:app --reload` |
| Cases not loading | Backend crashed | Check backend terminal for errors; restart uvicorn |
| `'npm' not recognized` | Node.js not in PATH | Run: `$env:PATH += ';C:\Program Files\nodejs'` |
| Evidence parse fails | Wrong filename or format | Ensure filename contains the evidence type keyword |
| Database connection error | PostgreSQL not running | Open pgAdmin 4 → start PostgreSQL 16 service |
| Port already in use | Previous session still running | Close all PowerShell windows and restart |
| Import errors on startup | Missing Python package | Run: `pip install -r requirements.txt --break-system-packages` |

<img width="1677" height="691" alt="image" src="https://github.com/user-attachments/assets/8d1f4bb0-0143-4efe-bfdb-419153772928" />


*SATYANVESH 2.0 —  Cyber Crime Division | Confidential | Version 2.0 | 2025*
