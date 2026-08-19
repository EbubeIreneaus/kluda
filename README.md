<p align="center">
  <img src="web/public/favicon.svg" alt="Kluda Logo" width="80" />
</p>

<h1 align="center">Kluda</h1>

<p align="center">
  <strong>Sell Faster, Track Everything — Modern, offline-first Retail & Point of Sale Platform.</strong>
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#tech-stack">Tech Stack</a> •
  <a href="#project-structure">Project Structure</a> •
  <a href="#getting-started">Getting Started</a> •
  <a href="#environment-variables">Environment Variables</a> •
  <a href="#api-reference">API Reference</a> •
  <a href="#deployment">Deployment</a> •
  <a href="#license">License</a>
</p>

---

## Overview

Kluda is a complete, turnkey Point of Sale and retail operations platform designed for retail stores — supermarkets, boutiques, pharmacies, and multi-branch businesses. It pairs a **FastAPI** backend with **Nuxt** frontend applications that work as installable **Progressive Web Apps (PWA)**, allowing cashiers to continue recording sales even when the network goes down.

Sales recorded offline are persisted in the browser via **IndexedDB** (powered by Dexie.js) and automatically synced to the server when connectivity is restored. Multiple staff terminals stay in real-time sync through **WebSocket** broadcasts — when one cashier adds a product or records a sale, every other open terminal updates instantly.

---

## Features

### 🛒 POS Terminal
- Full-screen checkout interface optimised for speed
- **Barcode scanner** support via device camera (ZXing library)
- Quick product search with fuzzy matching
- Cart management with quantity editing, discount application, and customer linking
- Multiple payment methods: **Cash**, **POS**, **Transfer**, **Online**, **Debt (Credit)**
- On-screen receipt preview after checkout
- Haptic feedback (device vibration) on barcode scan

### 📦 Product (Inventory) Management
- Add, edit, soft-delete products with rich metadata (SKU, barcode, unit type, description)
- Support for 9 unit types: piece, kg, g, litre, ml, pack, carton, dozen, bag
- Configurable max discount per product
- Full-text search powered by PostgreSQL `tsvector` / `tsquery` ranking
- Automatic slug generation with collision handling

### 📊 Sales & Analytics
- Paginated sales history filtered by date
- Batch sale creation with **idempotency keys** — safe to retry without duplicates
- Automatic inventory deduction on completed sales
- Analytics dashboard with configurable time periods (today, week, month, 3/6/12 months, custom range)
- KPI cards: total revenue, total transactions, payment method breakdown
- Charts: revenue trend, top-selling products, payment method distribution, daily transaction series

### 👥 Customer & Debt Management
- Customer registry with full-text search (name, email, phone, address)
- Debt (credit) tracking — automatically created when payment method is "debt"
- Debt records include itemised purchase notes
- Mark debts as paid; deactivate customers

### 👮 Staff & Access Control
- Role-based access: **SuperAdmin**, **Admin**, **Manager**, **Staff**
- Granular permission system with 7 permission scopes:

  | Permission | Description |
  |---|---|
  | `manage:all` | Full access (SuperAdmin) |
  | `manage:staff` | Create, edit, suspend, terminate staff |
  | `manage:product` | Create, edit, delete products |
  | `view:product` | View-only product access |
  | `manage:user` | Manage customers and debts |
  | `record:sales` | Access POS terminal and record sales |
  | `view:analytics` | View analytics dashboard |

- Auto-generated unique staff IDs (`STF1000` – `STF9999`)
- SuperAdmin account bootstrapped from environment variables on first run
- Client-side route guarding based on permissions

### 🔐 Authentication & Security
- **Argon2id** password hashing via `pwdlib`
- **JWT** access tokens (1-hour expiry) + **refresh token rotation** (30-day sliding window)
- Refresh tokens stored as SHA-256 hashes in the database — raw tokens never persisted server-side
- **HttpOnly, Secure, SameSite** cookies with environment-aware configuration
- Multi-device session management — each login creates an independent session
- Session revocation: changing password invalidates all sessions across all devices
- OTP-based password reset flow (email → verify token → submit new password)
- Automatic token refresh on 401 with request queuing (prevents thundering herd)

### 🌐 Real-Time Sync (WebSocket)
- Per-staff WebSocket connections with automatic reconnection and exponential backoff
- Broadcasts on every mutation: product CRUD, customer CRUD, debt CRUD, sale creation
- Excludes the originating staff from receiving their own broadcast — no duplicate UI updates
- Dead connection pruning on failed sends

### 📱 Offline-First PWA
- Installable on any device (desktop, tablet, phone) as a standalone app
- **Service Worker** with Workbox: CacheFirst for static assets, NetworkFirst for pages
- **IndexedDB** (Dexie.js) stores:
  - `pendingSales` — offline sale queue with idempotency keys
  - `products` — local product cache for instant POS lookup
  - `customers` — local customer cache
  - `salesCache` — today's sales for offline viewing
  - `debtors` — local debt cache
- Automatic sync-on-reconnect: watches `navigator.onLine` and flushes the pending queue
- Network status bar in the UI
- PWA update prompt with in-app banner

---

## Tech Stack

### Backend (`/api`)

| Technology | Purpose |
|---|---|
| [FastAPI](https://fastapi.tiangolo.com/) | Async Python web framework |
| [SQLAlchemy 2.0](https://www.sqlalchemy.org/) | Async ORM with mapped columns |
| [PostgreSQL](https://www.postgresql.org/) + [asyncpg](https://github.com/MagicStack/asyncpg) | Database + async driver |
| [Alembic](https://alembic.sqlalchemy.org/) | Database migrations |
| [Pydantic v2](https://docs.pydantic.dev/) + [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) | Validation, serialization, config |
| [PyJWT](https://pyjwt.readthedocs.io/) | JWT token encoding/decoding |
| [pwdlib](https://github.com/frankie567/pwdlib) (Argon2) | Password hashing |
| [fastapi-pagination](https://github.com/uriyyo/fastapi-pagination) | Cursor/offset pagination |
| [SlowAPI](https://github.com/laurentS/slowapi) | Rate limiting |
| [Uvicorn](https://www.uvicorn.org/) | ASGI server |

### Frontend (`/dashboard`)

| Technology | Purpose |
|---|---|
| [Nuxt 4](https://nuxt.com/) | Vue 3 meta-framework (SPA mode) |
| [Nuxt UI v4](https://ui.nuxt.com/) | Component library + Tailwind CSS |
| [Pinia](https://pinia.vuejs.org/) | State management |
| [Dexie.js](https://dexie.org/) | IndexedDB wrapper for offline storage |
| [Chart.js](https://www.chartjs.org/) + [vue-chartjs](https://vue-chartjs.org/) | Analytics charts |
| [ZXing](https://github.com/nickhudkins/zxing-js) | Barcode scanning via camera |
| [VueUse](https://vueuse.org/) | Composition API utilities |
| [@vite-pwa/nuxt](https://vite-pwa-org.netlify.app/frameworks/nuxt) | PWA / Service Worker |

---

## Project Structure

```
retail-pos/
├── api/                          # FastAPI backend
│   ├── main.py                   # App entry point, lifespan, CORS, router mounting
│   ├── setting.py                # Pydantic settings (env vars)
│   ├── alembic.ini               # Alembic config
│   ├── vercel.json               # Vercel deployment config
│   │
│   ├── models/                   # SQLAlchemy ORM models
│   │   ├── config.py             # Engine, session factory, Base
│   │   ├── user.py               # Staff, StaffSession, Customer, Debtor
│   │   └── stock.py              # Stock, SaleItem, Sale, Images, Barcode
│   │
│   ├── schemas/                  # Pydantic request/response schemas
│   │   ├── user.py               # Auth, Staff, Customer, Debtor schemas
│   │   └── stock.py              # Product, Sale, SaleItem, Barcode schemas
│   │
│   ├── routers/                  # API route handlers
│   │   ├── auth.py               # Login, logout, refresh, password reset
│   │   ├── staff.py              # Staff CRUD + access revocation
│   │   └── stock/
│   │       ├── product.py        # Product CRUD + full-text search
│   │       ├── customer.py       # Customer CRUD + Debtor CRUD
│   │       └── sales.py          # Sale creation, analytics, history
│   │
│   ├── libs/                     # Shared utilities
│   │   ├── security.py           # Hashing, JWT, cookies, IP extraction
│   │   ├── deps.py               # Auth dependencies, permission guards
│   │   ├── init_db.py            # SuperAdmin bootstrap on startup
│   │   └── ws_manager.py         # WebSocket connection manager
│   │
│   └── migrations/               # Alembic migration versions
│
└── dashboard/                    # Nuxt 4 frontend (SPA / PWA)
    ├── nuxt.config.ts            # Nuxt config: PWA, runtime config, route rules
    ├── package.json
    │
    └── app/
        ├── app.vue               # Root app component
        ├── middleware/
        │   └── auth.global.ts    # Route guard (auth + permission checks)
        │
        ├── layouts/
        │   └── dashboard.vue     # Sidebar nav, header, mobile slideover
        │
        ├── pages/
        │   ├── login.vue         # Login page
        │   └── dashboard/
        │       ├── index.vue     # Dashboard home (KPIs, charts)
        │       ├── pos.vue       # POS terminal (barcode scan, cart, checkout)
        │       ├── products.vue  # Product management
        │       ├── sales.vue     # Sales history
        │       ├── customers.vue # Customer & debt management
        │       ├── analytics.vue # Analytics with charts
        │       ├── staff.vue     # Staff management
        │       └── settings.vue  # User settings
        │
        ├── stores/               # Pinia state management
        │   ├── auth.ts           # Auth state, login/logout, permissions
        │   ├── cart.ts           # POS cart state
        │   ├── sales.ts          # Sales + offline sync + IndexedDB
        │   ├── product.ts        # Product state + IndexedDB cache
        │   ├── customer.ts       # Customer & debtor state
        │   └── analytics.ts      # Analytics data fetching
        │
        ├── composables/          # Reusable logic
        │   ├── useApi.ts         # HTTP client with auto token refresh
        │   ├── useWebSocket.ts   # Real-time sync (WS connect/reconnect)
        │   ├── useFormatCurrency.ts  # Kobo → Naira formatting
        │   └── useForm.ts        # Form state helper
        │
        ├── components/
        │   ├── NetworkStatusBar.vue
        │   ├── PwaInstallModal.vue
        │   ├── PwaUpdateBanner.vue
        │   └── dashboard/        # Dashboard-specific widgets
        │       ├── KpiCard.vue
        │       ├── LowStockAlert.vue
        │       ├── RevenueChart.vue
        │       ├── TopProductsChart.vue
        │       ├── PaymentMethodChart.vue
        │       └── RecentSalesTable.vue
        │
        └── utils/
            └── db.ts             # Dexie IndexedDB schema & singleton
```

---

## Getting Started

### Prerequisites

| Tool | Version |
|---|---|
| **Python** | 3.14+ |
| **Node.js** | 20+ |
| **pnpm** | 11+ |
| **PostgreSQL** | 14+ |
| **uv** | Latest (recommended) or pip |

### 1. Clone the Repository

```bash
git clone https://github.com/EbubeIreneaus/retail-pos-prototype.git
cd retail-pos-prototype
```

### 2. Set Up the Backend

```bash
cd api

# Create a virtual environment and install dependencies
uv venv
uv pip install -r requirements.txt

# Copy and configure environment variables
cp .env.example .env
# Edit .env with your database credentials (see section below)

# Run database migrations
uv run alembic upgrade head

# Start the development server
uv run python main.py
```

The API will be available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

### 3. Set Up the Dashboard

```bash
cd dashboard

# Install dependencies
pnpm install

# Configure the API URL
cp .env.example .env
# Set NUXT_PUBLIC_API_URL=http://localhost:8000

# Start the development server
pnpm dev
```

The dashboard will be available at `http://localhost:3000` and will redirect to `/dashboard`.

---

## Environment Variables

### Backend (`api/.env`)

```env
# Database
DB_URL=postgresql+asyncpg://user:password@localhost:5432/retailpos

# JWT
JWT_SECRET=your-strong-secret-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_HOURS=13

# SuperAdmin (created on first startup)
SUPER_STAFF_NAME=Admin
SUPER_STAFF_EMAIL=admin@example.com
SUPER_STAFF_PASSWORD=your-secure-password

# Environment
APP_ENV=development
DOMAIN_NAME=localhost
```

### Frontend (`dashboard/.env`)

```env
NUXT_PUBLIC_API_URL=http://localhost:8000
```

---

## API Reference

The API is fully documented via FastAPI's auto-generated **Swagger UI** and **ReDoc**:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Endpoint Summary

| Group | Endpoint | Methods | Description |
|---|---|---|---|
| **Auth** | `/auth/login` | POST | Staff login (returns JWT + sets cookies) |
| | `/auth/logout` | POST | Logout and revoke session |
| | `/auth/refresh-token` | POST | Rotate access + refresh tokens |
| | `/auth/me` | GET | Get current staff profile |
| | `/auth/change-password` | POST | Change password (invalidates all sessions) |
| | `/auth/send-reset-email` | POST | Initiate password reset |
| | `/auth/verify-reset-token` | POST | Verify OTP reset token |
| | `/auth/reset-password` | POST | Submit new password with OTP |
| **Staff** | `/staff/` | GET, POST | List / create staff members |
| | `/staff/{staff_id}` | GET, PUT, PATCH, DELETE | Get / update / terminate staff |
| | `/staff/revoke-access` | POST | Revoke a staff member's access token |
| **Products** | `/product/` | GET, POST | List / create products |
| | `/product/{slug}` | GET, PUT, DELETE | Get / update / soft-delete product |
| **Sales** | `/sales/` | GET, POST | List today's sales / batch create sales |
| | `/sales/{sale_id}` | GET, PUT, DELETE | Get / update / cancel a sale |
| | `/sales/analytics` | GET | Aggregated analytics for a time period |
| | `/sales/ping` | GET | Database health check |
| **Customers** | `/customer/` | GET, POST | List / create customers |
| | `/customer/{customer_id}` | GET, PUT, DELETE | Get / update / deactivate customer |
| **Debts** | `/debtor/` | GET, POST | List / create debt records |
| | `/debtor/{debtor_id}` | GET, PUT, DELETE | Get / update / mark debt as paid |
| **WebSocket** | `/ws/{staff_id}` | WS | Real-time event stream |

---

## Database Schema

```mermaid
erDiagram
    staffs ||--o{ staff_sessions : has
    staffs {
        int id PK
        string staff_id UK
        string first_name
        string last_name
        string role
        string email
        json permission
        enum status
    }
    staff_sessions {
        int id PK
        string staff_id FK
        string refresh_token_hash
        datetime expired_at
    }
    customers ||--o{ debtors : owes
    customers {
        int id PK
        uuid customer_id UK
        string fullname
        string email UK
        enum status
    }
    debtors {
        int id PK
        uuid debtor_id
        uuid customer_id FK
        int amount
        string status
    }
    stocks ||--o{ product_images : has
    stocks ||--o{ sale_items : sold_as
    stocks {
        int id PK
        string name
        string slug UK
        string barcode_id UK
        int unit_price
        numeric quantities
        string unit_in
        boolean deleted
    }
    sales ||--o{ sale_items : contains
    sales }o--o| customers : linked_to
    sales {
        int id PK
        uuid sale_id UK
        int discount
        string payment_method
        int amount_recived
        uuid idempotency_key UK
        string status
    }
    sale_items {
        int id PK
        string stock_slug FK
        uuid sale_id FK
        int amount
        numeric quantities
    }
    product_images {
        int id PK
        string stock_slug FK
        string src
    }
    store_barcodes {
        int id PK
        string barcode_id UK
        string title
        string image
    }
```

---

## Deployment

### Backend (Vercel)

The API includes a `vercel.json` configured for serverless deployment:

```bash
cd api
vercel --prod
```

The build command automatically runs `uv run alembic upgrade head` to apply migrations.

### Frontend (Static / Vercel / Netlify)

The dashboard is configured for static generation (`nuxt generate`):

```bash
cd dashboard
pnpm build
```

The output in `.output/public/` can be deployed to any static hosting provider (Vercel, Netlify, Cloudflare Pages, etc).

### Alternative: VPS / Single Server

For a turnkey deployment on a single VPS:

1. Install PostgreSQL and create a database
2. Clone the repo and configure `.env` files
3. Run `alembic upgrade head` to initialise the schema
4. Run the API with `uvicorn main:app --host 0.0.0.0 --port 8000` (or behind a reverse proxy like Nginx/Caddy)
5. Build and serve the dashboard static files from the same server

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -m 'feat: add your feature'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Open a Pull Request

---

## License

This project is licensed under the [MIT License](dashboard/LICENSE).

---

<p align="center">
  Built with ❤️ for retail businesses
</p>
