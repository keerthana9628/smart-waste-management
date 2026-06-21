# 🌿 Smart Waste Management System

A full-stack, AI-enhanced web application for monitoring and managing
waste bins. Built with **Flask + MySQL** on the backend and
**Bootstrap 5 + Chart.js** on the frontend, with **machine learning**
features for fill-level prediction and AI-optimized collection scheduling.

---

## 1. Features

- **Authentication & Roles** — Admin / Collector login with Flask-Login,
  role-based access control.
- **Dashboard** — total/active/full bins, pending collections, recent
  activity feed, Chart.js graphs (bar, doughnut, line).
- **Dustbin Management** — add/edit/delete bins, track location,
  capacity, fill level (%), and status (Empty / Half Full / Full).
- **Alert System** — automatic alerts when fill level ≥ 80%, with a
  notification panel and resolved-alert history.
- **Collection Management** — create schedules, assign collectors,
  update status (pending → in progress → completed/missed), history log.
- **Reports & Analytics** — daily/weekly/monthly stats, bin utilization,
  downloadable PDF reports (ReportLab).
- **Modern UI** — green eco-themed, responsive Bootstrap 5 layout,
  sidebar navigation, dark mode toggle, search & filter.
- **AI / ML Features**
  - **Fill-level prediction** (linear regression on historical sensor
    readings) — estimates when each bin will hit 80% / 100%.
  - **AI-optimized collection scheduling** — ranks bins by urgency and
    load-balances tasks across collectors.
  - **Predictive dashboard widgets** — "AI Predictive Insights" panel
    and AI fill-rate table in Reports.

---

## 2. Project Structure

```
smart_waste_management/
├── app/
│   ├── __init__.py            # App factory
│   ├── models.py               # SQLAlchemy models
│   ├── routes/                 # Blueprints (auth, dashboard, bins, ...)
│   ├── ml/                      # predictor.py, scheduler_ai.py
│   ├── utils/                   # decorators.py, pdf_generator.py
│   ├── templates/               # Jinja2 templates
│   └── static/                  # css/, js/
├── database/
│   ├── schema.sql               # MySQL schema + ER relationships
│   └── seed_data.sql            # Reference sample SQL data
├── config.py
├── run.py
├── seed_db.py                   # Recommended way to seed sample data
├── requirements.txt
├── .env.example
└── README.md
```

---

## 3. Database Design (ER Diagram)

```
 users (1) ───< (M) collections (M) >─── (1) bins
   │                                          │
   │                                          ├──< bin_fill_history  (ML training data)
   └──< activity_logs                        └──< alerts
```

| Table              | Key columns                                                                 |
|--------------------|------------------------------------------------------------------------------|
| `users`            | id, username, password_hash, full_name, role (admin/collector), email, phone |
| `bins`             | id, bin_code, location, lat/lng, capacity_l, fill_level, status, waste_type   |
| `bin_fill_history` | id, bin_id (FK), fill_level, recorded_at                                      |
| `alerts`           | id, bin_id (FK), alert_type, message, is_resolved, created_at, resolved_at    |
| `collections`      | id, bin_id (FK), collector_id (FK→users), scheduled_date, status, waste_kg    |
| `activity_logs`    | id, user_id (FK), action, details, created_at                                 |

See `database/schema.sql` for the full DDL with constraints and indexes.

---

## 4. Setup Instructions (Windows + VS Code)

### Step 1 — Install prerequisites
- Python 3.10+ → https://www.python.org/downloads/
- MySQL Server (e.g. MySQL Community Server / XAMPP) → https://dev.mysql.com/downloads/
- VS Code with the Python extension

### Step 2 — Get the project & create a virtual environment
```bash
cd smart_waste_management
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux
```

### Step 3 — Install dependencies
```bash
pip install -r requirements.txt
```

### Step 4 — Configure the database
1. Start MySQL and create the database (the seed script can also do
   this automatically via SQLAlchemy, but creating it manually first
   is recommended):
   ```sql
   CREATE DATABASE smart_waste_db CHARACTER SET utf8mb4;
   ```
2. Copy `.env.example` to `.env` and fill in your MySQL credentials:
   ```bash
   copy .env.example .env        # Windows
   # cp .env.example .env         # macOS/Linux
   ```
   Edit `.env`:
   ```
   SECRET_KEY=any-random-string
   DB_USER=root
   DB_PASSWORD=your_mysql_password
   DB_HOST=localhost
   DB_NAME=smart_waste_db
   ```

### Step 5 — Create tables and load sample data
```bash
python seed_db.py
```
This creates all tables (via SQLAlchemy) and inserts:
- 1 admin + 3 collector accounts
- 12 sample bins with ~5 days of fill-level history (for ML)
- Alerts, collection schedules/history, and activity logs

> 🔐 **Default login credentials** (all passwords = `password123`):
> | Role      | Username     |
> |-----------|--------------|
> | Admin     | `admin`      |
> | Collector | `collector1` / `collector2` / `collector3` |

### Step 6 — Run the application
```bash
python run.py
```
Open your browser at **http://127.0.0.1:5000**

---

## 5. Quick Start Without MySQL (SQLite, for testing)

If you just want to try the project without installing MySQL, set:
```
DATABASE_URL=sqlite:///dev.db
```
in your `.env` (or as an environment variable) before running
`seed_db.py` and `run.py`. SQLAlchemy will create a local `dev.db`
file automatically.

---

## 6. API Endpoints (JSON, used by charts/AI widgets)

| Endpoint                         | Description                                |
|-----------------------------------|---------------------------------------------|
| `GET /api/bins`                   | All bins as JSON                            |
| `GET /api/bins/<id>/history`      | Fill-level history for one bin              |
| `GET /api/predictions`            | ML fill-rate predictions for all bins       |
| `GET /api/ai-schedule`            | AI-optimized collection schedule preview    |
| `GET /api/waste-trend`            | 30-day waste collection totals              |
| `GET /api/bin-status-summary`     | Bin counts by status (for pie chart)        |

---

## 7. Testing Scenarios

1. **Authentication**
   - Log in as `admin` / `password123` → should reach the Dashboard.
   - Log in as `collector1` / `password123` → sidebar should hide
     "Add Bin", "AI Scheduler" admin-only links.
   - Try accessing `/bins/add` as a collector → should return 403.
   - Log out and try accessing `/` → should redirect to `/login`.

2. **Dustbin Management**
   - Add a new bin (e.g. `BIN-013`, location "Gym", capacity 100).
   - Edit a bin's fill level to 85% → status should change to "Full"
     and a new alert should appear under **Alerts**.
   - Search for "Hostel" in the bins page → only matching bins shown.
   - Filter by status = "Full" → only full bins shown.
   - Delete a bin (admin only) → confirm it disappears from the list.

3. **Alert System**
   - Push any bin's fill level ≥ 80% → check the Alerts badge in the
     sidebar increments.
   - Resolve an alert → it moves to "Alert History".
   - Use "Resolve All" → all active alerts cleared.

4. **Collection Management**
   - As admin, create a new collection schedule for a bin, assign a
     collector, pick today's date.
   - Log in as that collector → see the task under "Collections".
   - Mark it "In Progress", then "Completed" with a waste weight
     (e.g. 12.5 kg) → bin's fill level resets to 0% and any open alert
     for that bin is auto-resolved.

5. **AI Features**
   - Go to **AI Scheduler** (admin) → verify bins with fill level ≥ 80%
     (or predicted to reach it soon) appear, sorted by urgency, with
     collectors assigned across the next 3 days.
   - Click "Apply Suggestions" → new pending collection tasks appear in
     **Collections**.
   - On the **Dashboard**, check the "AI Predictive Insights" panel —
     bins are ranked by predicted time-to-80%.
   - On **Reports**, check the "AI Fill-Rate Predictions" table.

6. **Reports & Analytics**
   - Switch between Daily / Weekly / Monthly tabs → stats update.
   - Click "Download PDF Report" → a PDF opens/downloads with summary,
     bin utilization, and collection history tables.

7. **UI / UX**
   - Toggle dark mode (moon/sun icon) → theme persists after refresh.
   - Resize the browser to mobile width → sidebar collapses behind a
     hamburger menu.

---

## 8. Notes on the ML Components

- `app/ml/predictor.py` fits a simple **linear regression** (per bin)
  on `bin_fill_history` readings recorded since the bin's last
  collection, to estimate the fill rate (%/hour) and predict when the
  bin will cross 80% / 100%. Falls back to a default rate if there's
  insufficient history.
- `app/ml/scheduler_ai.py` ranks bins by an **urgency score** (derived
  from current fill level + predicted time-to-threshold) and
  distributes the most urgent bins across available collectors using a
  simple load-balancing algorithm over a configurable planning window
  (default 3 days).
- These are intentionally lightweight, explainable models suitable for
  a college project — they can be swapped for more advanced models
  (e.g. Prophet, ARIMA, or a trained regression on real IoT sensor
  data) without changing the rest of the application, since both
  modules only return plain dictionaries consumed by the routes/templates.

---

## 9. Production Notes

- Set `FLASK_ENV=production` and a strong, random `SECRET_KEY`.
- Run behind a production WSGI server (e.g. `gunicorn` or `waitress`),
  not the built-in Flask dev server.
- Use a real IoT integration (e.g. ultrasonic sensors + ESP32/Raspberry
  Pi posting to `/bins/<id>/update-level`) to replace manual fill-level
  updates.
