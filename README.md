# frappe-moodle-app

A Frappe **v16.x** app that integrates with **Moodle (v5.1)** using the Moodle Web Services REST API.
It allows Frappe users to link or create Moodle accounts and access Moodle directly from a Frappe website or workspace.

Frappe App Name: **moodle**

---

## Features

- Link Frappe users to Moodle accounts using email matching
- Create Moodle user accounts from Frappe (via Moodle REST API)
- Secure storage of Moodle service token using Frappe Password fields
- Website dashboard & workspace UI for Moodle integration
- Password-safe UX (no password disclosure, autocomplete disabled)

---

## Requirements

- **Frappe Framework: 16.x**
- **Moodle: 5.1**
- Moodle Web Services enabled (REST)
- A dedicated Moodle service user (e.g. `ws_frappe`)

---

## Moodle Setup (Web Services)

### 1) Enable Web Services
Moodle Admin:
- *Site administration* → *Advanced features* → **Enable web services**
- *Site administration* → *Server* → *Web services* → **Manage protocols**
  - Enable **REST**

### 2) Create a service user
Create a Moodle user (example):
- Username: `ws_frappe`
- Role: minimal permissions only

### 3) Create External Service & Token
- *Site administration* → *Server* → *Web services* → **External services**
  - Create a service (e.g. `Frappe Integration`)
- Add required functions (see below)
- *Manage tokens*
  - Create a token for user `ws_frappe` and the service

### 4) Required External Functions (minimum)
Depending on features used:
- `core_user_get_users_by_field`
- `core_user_create_users`

> Add additional functions only if your dashboard logic requires them.

---

## Installation (Frappe Bench)

### 1) Clone the app
```bash
cd /path/to/frappe-bench/apps
git clone https://github.com/jdpark7/frappe-moodle-app.git moodle
