# Stationery Shop SaaS

স্টেশনারি শপ ম্যানেজমেন্ট সিস্টেম - A complete multi-tenant SaaS application for stationery shop management.

## Features

- 🏪 **Multi-tenant Architecture** - Multiple shops in one system
- 📦 **Inventory Management** - Stock tracking & low stock alerts
- 💰 **POS System** - Point of sale with receipt printing
- 🛒 **Sales Management** - Customer, invoices, payments
- 📥 **Purchase Management** - Suppliers, purchase orders
- 📊 **Accounting** - Transactions, expenses, profit/loss reports
- 👥 **Role-Based Access Control** - Admin, Manager, Accountant, Staff

## Tech Stack

- **Backend**: Django 5.0+
- **Database**: PostgreSQL 15
- **Server**: Gunicorn + Nginx
- **Container**: Docker & Docker Compose
- **CI/CD**: GitHub Actions

---

## Quick Start (Development)

### Option 1: Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/shoeb-devops/stationery-shop-saas.git
cd stationery-shop-saas

# Start with Docker Compose
docker-compose up --build

# Access at http://localhost:8000
```

### Option 2: Local Development

```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run server
python manage.py runserver
```

---

## Production Deployment

### 1. Setup Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your production values
nano .env
```

### 2. Deploy with Docker Compose

```bash
# Build and start production containers
docker-compose -f docker-compose.prod.yml up -d --build

# Check logs
docker-compose -f docker-compose.prod.yml logs -f

# Run migrations (first time only)
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate
```

### 3. Create Admin User

```bash
docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

---

## Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `DEBUG` | Debug mode | `False` |
| `SECRET_KEY` | Django secret key | `your-secret-key` |
| `DATABASE_URL` | PostgreSQL URL | `postgres://user:pass@db:5432/dbname` |
| `ALLOWED_HOSTS` | Allowed domains | `your-domain.com` |
| `CSRF_TRUSTED_ORIGINS` | CSRF origins | `https://your-domain.com` |

---

## Project Structure

```
stationery-shop-saas/
├── accounts/          # User authentication & management
├── products/          # Product & category management
├── inventory/         # Stock & inventory tracking
├── sales/             # POS, sales, customers
├── purchases/         # Suppliers & purchases
├── accounting/        # Financial transactions
├── tenants/           # Multi-tenancy & subscriptions
├── templates/         # HTML templates
├── static/            # CSS, JS, images
├── nginx/             # Nginx configuration
├── .github/workflows/ # CI/CD pipelines
├── docker-compose.yml # Development Docker config
└── docker-compose.prod.yml # Production Docker config
```

---

## License

MIT License - Free to use for personal and commercial projects.
