# Library Management Service

A comprehensive Django REST API service for managing library operations, including book catalog management, user borrowings, and payment processing.

## Features

- **User Management**: Custom user authentication with email-based login
- **Book Catalog**: Complete book inventory management with real-time availability tracking
- **Borrowing System**: Automated borrowing and return processes with date tracking
- **Payment Integration**: Stripe payment processing for rental fees and fines
- **Notification System**: Telegram bot integration for user notifications
- **Background Tasks**: Celery integration for asynchronous task processing
- **API Documentation**: Interactive API docs with Swagger/OpenAPI
- **Caching**: Redis-based caching for improved performance

## Architecture

### Database Models & Relationships

```
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│     User        │         │   Borrowing     │         │      Book       │
├─────────────────┤    1:N  ├─────────────────┤  N:1    ├─────────────────┤
│ id (PK)         │◄────────┤ id (PK)         │────────►│ id (PK)         │
│ email (unique)  │         │ user_id (FK)    │         │ title           │
│ first_name      │         │ book_id (FK)    │         │ author          │
│ last_name       │         │ borrow_date     │         │ cover           │
│ is_staff        │         │ expected_return │         │ inventory       │
│ is_active       │         │ actual_return   │         │ daily_fee       │
│ date_joined     │         │                 │         │                 │
└─────────────────┘         └─────────────────┘         └─────────────────┘
                                      │                            
                                      │ 1:N                       
                                      ▼                            
                            ┌─────────────────┐                   
                            │    Payment      │                   
                            ├─────────────────┤                   
                            │ id (PK)         │                   
                            │ borrowing_id(FK)│                   
                            │ status          │                   
                            │ type            │                   
                            │ session_url     │                   
                            │ session_id      │                   
                            │ money_to_pay    │                   
                            └─────────────────┘                   
```
### Model Details

#### User Model
- **Purpose**: Custom user authentication using email instead of username
- **Key Fields**: email (unique), first_name, last_name
- **Authentication**: JWT-based with SimpleJWT

#### Book Model  
- **Purpose**: Catalog management with inventory tracking
- **Key Fields**: 
  - `title`, `author` - Basic book information
  - `cover` - Choice field (HARD/SOFT)
  - `inventory` - Available copies count
  - `daily_fee` - Rental price per day
- **Business Logic**: Inventory decreases on borrowing, increases on return

#### Borrowing Model
- **Purpose**: Links users to borrowed books with date tracking
- **Key Fields**:
  - `borrow_date` - Auto-set on creation
  - `expected_return_date` - User-defined return deadline  
  - `actual_return_date` - Set when book is returned
- **Business Logic**: Manages book inventory and triggers payment creation

#### Payment Model
- **Purpose**: Handles all financial transactions via Stripe
- **Key Fields**:
  - `status` - PENDING/PAID/CANCELED/EXPIRED
  - `type` - PAYMENT (rental fee) / FINE (late return penalty)
  - `session_url`, `session_id` - Stripe checkout session data
  - `money_to_pay` - Amount in decimal format

## Technology Stack

### Backend Framework
- **Django 5.2.6** - Main web framework
- **Django REST Framework** - API development
- **PostgreSQL** - Primary database
- **Redis** - Caching and message broker

### Authentication & Security
- **JWT Authentication** - Token-based auth with SimpleJWT
- **Custom User Model** - Email-based authentication
- **API Rate Limiting** - 100/day for anonymous, 1000/day for authenticated

### Payment Processing
- **Stripe Integration** - Secure payment processing
- **Fine System** - 2.0x multiplier for overdue returns

### Background Tasks
- **Celery** - Asynchronous task processing
- **Celery Beat** - Scheduled task execution
- **Flower** - Celery monitoring dashboard

### API Documentation
- **drf-spectacular** - OpenAPI/Swagger documentation
- **Custom API Schema** - Detailed endpoint documentation

### Development Tools
- **Docker & Docker Compose** - Containerized development
- **Black** - Code formatting
- **Flake8 & Ruff** - Code linting
- **Coverage** - Test coverage reporting

## Service Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Client    │    │  Mobile App     │    │   Admin Panel   │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────▼──────────────┐
                    │      Django REST API       │
                    │   (library-service)        │
                    └─────────────┬──────────────┘
                                 │
         ┌───────────────────────┼────────────────────────┐
         │                       │                        │
┌────────▼────────┐    ┌────────▼────────┐    ┌──────────▼─────────┐
│   PostgreSQL    │    │     Redis       │    │     Celery         │
│   (Database)    │    │ (Cache/Broker)  │    │ (Background Tasks) │
└─────────────────┘    └─────────────────┘    └────────────────────┘
                                                          │
                    ┌─────────────────────────────────────┼─────────────┐
                    │                                     │             │
           ┌────────▼────────┐    ┌──────────────────────▼──┐  ┌────────▼────────┐
           │     Stripe      │    │    Telegram Bot         │  │     Flower      │
           │   (Payments)    │    │  (Notifications)        │  │  (Monitoring)   │
           └─────────────────┘    └─────────────────────────┘  └─────────────────┘
```

## Getting Started

### Prerequisites

- Docker & Docker Compose
- Python 3.11+ (for local development)
- PostgreSQL (if running locally)
- Redis (if running locally)

### Environment Variables
Copy `.env.sample` to `.env` and configure:

```bash
# Database
DATABASE_NAME=library_db
DATABASE_USER=library_user
DATABASE_PASS=your_password
DATABASE_HOST=postgres
DATABASE_PORT=5432

# Django
DJANGO_SECRET_KEY=your-secret-key
DEBUG=False
SITE_URL=http://127.0.0.1:8000

# Redis
 REDIS_HOST=redis
 REDIS_PORT=6379

# Stripe
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...

# Telegram
TG_API_TOKEN=your-bot-token
CHAT_ID=your-chat-id

# Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
```

### Running with Docker

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Service URLs
- **API Server**: http://localhost:8000
- **Admin Panel**: http://localhost:8000/admin/
- **API Documentation**: http://localhost:8000/api/doc/swagger/
- **Flower (Celery Monitor)**: http://localhost:5555
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

## API Endpoints

### Authentication
```
POST /api/users/                        # User registration
POST /api/users/token/                  # User login (get JWT tokens)
POST /api/users/token/refresh/          # Refresh JWT token
GET  /api/users/me/                     # Get user profile
PUT  /api/users/me/change-password      # Update user profile
```

### Books
```
GET    /api/library/books/           # List all books
POST   /api/library/books/           # Create book (admin only)
GET    /api/library/books/{id}/      # Get book details
PUT    /api/library/books/{id}/      # Update book (admin only)
DELETE /api/library/books/{id}/      # Delete book (admin only)
```

### Borrowings
```
GET    /api/library/borrowings/                  # List user's borrowings
POST   /api/library/borrowings/                  # Create new borrowing
GET    /api/library/borrowings/{id}/             # Get borrowing details
POST   /api/library/borrowings/{id}/return-book/ # Return borrowed book
```

### Payments
```
GET    /api/library/payments/               # List user's payments
GET    /api/library/payments/{id}/          # Get payment details
POST   /api/library/payments/{id}/success/  # Handle payment success
POST   /api/library/payments/{id}/cancel/   # Handle payment cancellation
```

## Business Logic

### Borrowing Process
1. **Book Selection**: User selects available book from catalog
2. **Inventory Check**: System verifies book availability (inventory > 0)
3. **Payment Creation**: Stripe checkout session created for rental fee
4. **Inventory Update**: Book inventory decreased by 1
5. **Notification**: User receives confirmation via Telegram

### Return Process
1. **Return Request**: User initiates return through API
2. **Date Recording**: System records actual return date
3. **Inventory Update**: Book inventory increased by 1
4. **Fine Calculation**: If overdue, fine payment created (daily_fee × days_overdue × 2.0)
5. **Notification**: Return confirmation sent to user

### Payment System
- **Rental Fees**: Calculated as `daily_fee × rental_days`
- **Late Fines**: Calculated as `daily_fee × overdue_days × FINE_MULTIPLIER(2.0)`
- **Stripe Integration**: Secure payment processing with session URLs
- **Payment Status**: Tracked through webhook notifications

### Notifications
- **Telegram Integration**: Automated notifications for:
  - Successful borrowings
  - Return confirmations  
  - Payment reminders
  - Overdue book alerts

## Monitoring & Maintenance

### Celery Tasks
- **Periodic Tasks**: Scheduled via Celery Beat
- **Background Processing**: Payment webhook handling
- **Monitoring**: Flower dashboard for task monitoring

### Database Maintenance
- **Migrations**: Django migrations for schema changes
- **Indexing**: Optimized queries with proper indexing
- **Backup**: Regular PostgreSQL backups recommended

### Caching Strategy
- **Redis Cache**: API response caching
- **Query Optimization**: Reduced database load
- **Session Storage**: User session management

## Testing

```bash
# Run all tests
python manage.py test

# Run with coverage
coverage run --source='.' manage.py test
coverage report
coverage html
```

## Performance Considerations

### Database Optimization
- Indexed foreign key relationships
- Efficient queries with select_related/prefetch_related
- Connection pooling for high load
### Caching Strategy
- Redis caching for frequently accessed data
- API response caching
- Database query result caching

### Background Tasks
- Celery for heavy processing
- Email/notification sending
- Payment processing workflows

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

### Code Standards
- Follow PEP 8 style guide
- Use Black for code formatting
- Write comprehensive tests
- Update documentation

## Support

For support and questions:
- Open an issue in the GitHub repository
- Check the API documentation at `/api/doc/swagger/`
- Review the admin panel for data management

---
