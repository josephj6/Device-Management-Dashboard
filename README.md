# 🖥️ Device Management Dashboard (DMD)

A Python-based app to digitize, secure, and streamline device tracking for frontline retail teams.

## 🔍 Overview

As a Retail Associate at Nike, I noticed a consistent pain point: our device (AD) checkout process was manual (pen and paper 😵‍💫) and error-prone. It resulted in illegible logs, inaccurate timestamps, and costly device misplacement.

To solve this, I designed and built the **Device Management Dashboard (DMD)** using Python and Replit.

The DMD automates the AD tracking system with a role-based interface for both employees and managers. It improves legibility, auditability, and real-time device visibility—all while applying security best practices like **RBAC** and the **Principle of Least Privilege**.

---

## ⚙️ Key Features

### ✅ For Employees
- **Secure Login** using employee ID and password
- **Dropdown Menus** to select specific AD and payment terminals
- **One-click Checkout & Return**
- **Timestamped Logs** for every action
- **No access to logs or audit data (RBAC enforced)**

### 🔐 For Managers
- **Role-Based Access** to employee + device data tables
- **Search Filters** by device, employee, time, or day
- **Manual Overrides** to return/check out devices if needed
- **Real-time Audit View** of all check-in/check-out activity

---

## 🧠 Technical Highlights

- 🔒 **RBAC Implementation**: Employees vs. Managers have distinct access levels
- 🕒 **NTP-Synced Timestamps**: Accurate and auditable logs
- ♻️ **Auto-removal of Active Devices** from dropdowns (to prevent double booking)
- 📊 **Searchable Audit Logs** with advanced filtering
- 🧾 **Digitized Auditing**: Built-in checks reduce paper waste and improve accuracy

---

## 🔧 Built With

- **Language**: Python  
- **Platform**: Replit  
- **Storage**: In-memory tables (future expansion: SQL integration or cloud backend)

---

## 📈 Impact

This project demonstrates my ability to:
- Identify real-world tech inefficiencies
- Design secure, role-based applications from scratch
- Apply cybersecurity concepts (RBAC, POLP, audit logging) in practical environments
- Build solutions that enhance both usability and operational accountability

---

## 📌 Future Improvements

- 🔄 Add persistent backend (SQLite or Firebase)
- 📱 Convert to mobile-friendly UI
- 📥 Exportable audit logs (CSV/JSON)
- 🧪 Add user authentication via secure API

---

## 👩🏽‍💻 Author

**Jelisha Joseph**  
IT Support Specialist | Cybersecurity Analyst in Training  
🔗 [LinkedIn](https://linkedin.com/in/jelisha-joseph) | 🔗 [Portfolio](#) | 🛡️ Security+ Candidate  