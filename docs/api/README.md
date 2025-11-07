# API Reference

Complete API documentation for the Event Management System.

## Base URL

- **Development**: `http://localhost:8000/api/`
- **Production**: `https://api.yourdomain.com/api/`

## Authentication

All authenticated endpoints require a JWT token in the Authorization header:

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Obtaining Tokens

**Endpoint**: `POST /api/users/login/`

**Request**:
```json
{
  "email": "user@example.com",
  "password": "your_password"
}
```

**Response**:
```json
{
  "tokens": {
    "access": "eyJ...",
    "refresh": "eyJ..."
  },
  "user": {
    "id": 1,
    "email": "user@example.com",
    "username": "john_doe",
    "role": "attendee"
  }
}
```

### Refreshing Tokens

**Endpoint**: `POST /api/users/token/refresh/`

**Request**:
```json
{
  "refresh": "eyJ..."
}
```

**Response**:
```json
{
  "access": "eyJ...",
  "refresh": "eyJ..."
}
```

## Response Format

### Success Response

```json
{
  "id": 1,
  "title": "Event Title",
  "field": "value"
}
```

### List Response (Paginated)

```json
{
  "count": 150,
  "next": "http://api.example.com/events/?page=2",
  "previous": null,
  "results": [
    { "id": 1, "title": "Event 1" },
    { "id": 2, "title": "Event 2" }
  ]
}
```

### Error Response

```json
{
  "detail": "Error message",
  "code": "error_code"
}
```

### Validation Error

```json
{
  "field_name": [
    "This field is required.",
    "This field must be unique."
  ]
}
```

## Endpoints

### Authentication

#### Register User
```http
POST /api/users/register/
```

**Request**:
```json
{
  "email": "user@example.com",
  "username": "john_doe",
  "password": "SecurePass123!",
  "first_name": "John",
  "last_name": "Doe",
  "role": "attendee"
}
```

**Response** (201):
```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "john_doe",
  "first_name": "John",
  "last_name": "Doe",
  "role": "attendee",
  "is_email_verified": false
}
```

#### Login
```http
POST /api/users/login/
```

See [Obtaining Tokens](#obtaining-tokens) above.

#### Verify Email
```http
POST /api/users/verify-email/
```

**Request**:
```json
{
  "token": "verification_token_from_email"
}
```

**Response** (200):
```json
{
  "detail": "Email verified successfully"
}
```

#### Get Profile
```http
GET /api/users/profile/
Authorization: Bearer {token}
```

**Response** (200):
```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "john_doe",
  "first_name": "John",
  "last_name": "Doe",
  "role": "attendee",
  "bio": "Event enthusiast",
  "profile_picture": "http://example.com/media/profiles/pic.jpg",
  "is_email_verified": true
}
```

#### Update Profile
```http
PUT /api/users/profile/
Authorization: Bearer {token}
```

**Request**:
```json
{
  "first_name": "John",
  "last_name": "Smith",
  "bio": "Updated bio"
}
```

#### Change Password
```http
POST /api/users/change-password/
Authorization: Bearer {token}
```

**Request**:
```json
{
  "old_password": "OldPass123!",
  "new_password": "NewPass123!"
}
```

### Events

#### List Events
```http
GET /api/events/
```

**Query Parameters**:
- `city` - Filter by city
- `country` - Filter by country
- `category` - Filter by category ID
- `status` - Filter by status (published, draft, cancelled)
- `search` - Search in title and description
- `start_date__gte` - Events starting after date
- `start_date__lte` - Events starting before date

**Example**:
```http
GET /api/events/?city=San Francisco&category=2&status=published
```

**Response** (200):
```json
{
  "count": 50,
  "next": "http://api.example.com/events/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "title": "Tech Conference 2024",
      "slug": "tech-conference-2024",
      "description": "Annual tech conference",
      "organizer": {
        "id": 5,
        "username": "organizer1",
        "email": "organizer@example.com"
      },
      "category": {
        "id": 2,
        "name": "Technology",
        "slug": "technology"
      },
      "location_city": "San Francisco",
      "location_country": "USA",
      "start_datetime": "2024-06-15T10:00:00Z",
      "end_datetime": "2024-06-15T18:00:00Z",
      "capacity": 500,
      "status": "published",
      "privacy": "public",
      "view_count": 1250,
      "banner_image": "http://example.com/media/events/banner.jpg",
      "created_at": "2024-05-01T12:00:00Z"
    }
  ]
}
```

#### Get Event Detail
```http
GET /api/events/{slug}/
```

**Response** (200):
```json
{
  "id": 1,
  "title": "Tech Conference 2024",
  "slug": "tech-conference-2024",
  "description": "Detailed event description...",
  "organizer": {
    "id": 5,
    "username": "organizer1",
    "email": "organizer@example.com",
    "profile_picture": "http://example.com/media/profiles/org.jpg"
  },
  "category": {
    "id": 2,
    "name": "Technology",
    "slug": "technology"
  },
  "location_city": "San Francisco",
  "location_country": "USA",
  "location_address": "123 Main St",
  "location_latitude": 37.7749,
  "location_longitude": -122.4194,
  "start_datetime": "2024-06-15T10:00:00Z",
  "end_datetime": "2024-06-15T18:00:00Z",
  "capacity": 500,
  "status": "published",
  "privacy": "public",
  "view_count": 1250,
  "banner_image": "http://example.com/media/events/banner.jpg",
  "thumbnail_image": "http://example.com/media/events/thumb.jpg",
  "created_at": "2024-05-01T12:00:00Z",
  "updated_at": "2024-05-10T14:30:00Z"
}
```

#### Create Event
```http
POST /api/events/
Authorization: Bearer {token}
Role: organizer
```

**Request**:
```json
{
  "title": "New Event",
  "description": "Event description",
  "category_id": 2,
  "location_city": "San Francisco",
  "location_country": "USA",
  "location_address": "123 Main St",
  "start_datetime": "2024-06-15T10:00:00Z",
  "end_datetime": "2024-06-15T18:00:00Z",
  "capacity": 500,
  "status": "published",
  "privacy": "public"
}
```

**Response** (201):
```json
{
  "id": 42,
  "title": "New Event",
  "slug": "new-event",
  ...
}
```

#### Update Event
```http
PUT /api/events/{slug}/
Authorization: Bearer {token}
Role: organizer (owner only)
```

#### Delete Event
```http
DELETE /api/events/{slug}/
Authorization: Bearer {token}
Role: organizer (owner only)
```

**Response** (204): No content

#### Favorite Event
```http
POST /api/events/{slug}/favorite/
Authorization: Bearer {token}
```

**Response** (200):
```json
{
  "detail": "Event added to favorites"
}
```

**Unfavorite**: POST again to toggle

#### Get Event Ticket Types
```http
GET /api/events/{slug}/ticket_types/
```

**Response** (200):
```json
[
  {
    "id": 1,
    "name": "General Admission",
    "description": "Standard ticket",
    "price": "50.00",
    "quantity_available": 450,
    "quantity_sold": 50,
    "sale_start_date": "2024-05-01T00:00:00Z",
    "sale_end_date": "2024-06-14T23:59:59Z",
    "is_active": true
  },
  {
    "id": 2,
    "name": "VIP",
    "description": "VIP access",
    "price": "150.00",
    "quantity_available": 45,
    "quantity_sold": 5,
    "is_active": true
  }
]
```

### Categories

#### List Categories
```http
GET /api/categories/
```

**Response** (200):
```json
[
  {
    "id": 1,
    "name": "Technology",
    "slug": "technology",
    "description": "Tech events"
  },
  {
    "id": 2,
    "name": "Music",
    "slug": "music",
    "description": "Music events"
  }
]
```

### Comments

#### List Comments
```http
GET /api/comments/?event={event_id}
```

#### Create Comment
```http
POST /api/comments/
Authorization: Bearer {token}
```

**Request**:
```json
{
  "event_id": 1,
  "content": "Great event!",
  "parent_id": null  // Optional, for replies
}
```

**Response** (201):
```json
{
  "id": 15,
  "event": 1,
  "user": {
    "id": 3,
    "username": "john_doe"
  },
  "content": "Great event!",
  "parent": null,
  "created_at": "2024-05-15T10:30:00Z"
}
```

### Tickets

#### Create Order
```http
POST /api/tickets/order/
Authorization: Bearer {token}
```

**Request**:
```json
{
  "event_id": 1,
  "tickets": [
    {
      "ticket_type_id": 1,
      "quantity": 2
    },
    {
      "ticket_type_id": 2,
      "quantity": 1
    }
  ]
}
```

**Response** (201):
```json
{
  "order_id": 42,
  "event": {
    "id": 1,
    "title": "Tech Conference 2024"
  },
  "total_amount": "250.00",
  "payment_intent": {
    "id": "pi_1234567890",
    "client_secret": "pi_1234567890_secret_abcdef",
    "amount": 25000,
    "currency": "usd"
  },
  "tickets": [
    {
      "ticket_type": "General Admission",
      "quantity": 2,
      "price": "50.00",
      "subtotal": "100.00"
    },
    {
      "ticket_type": "VIP",
      "quantity": 1,
      "price": "150.00",
      "subtotal": "150.00"
    }
  ],
  "status": "pending"
}
```

**Next Steps**:
1. Use `client_secret` with Stripe.js to complete payment
2. On success, tickets will be generated and emailed

#### Get My Tickets
```http
GET /api/tickets/my-tickets/
Authorization: Bearer {token}
```

**Response** (200):
```json
[
  {
    "id": 101,
    "event": {
      "id": 1,
      "title": "Tech Conference 2024",
      "start_datetime": "2024-06-15T10:00:00Z"
    },
    "ticket_type": "General Admission",
    "ticket_number": "TICK-2024-001-101",
    "qr_code": "http://example.com/media/qr_codes/101.png",
    "checked_in": false,
    "check_in_time": null,
    "order_date": "2024-05-15T14:30:00Z"
  }
]
```

#### Check-In Ticket
```http
POST /api/tickets/check-in/
Authorization: Bearer {token}
Role: organizer or admin
```

**Request**:
```json
{
  "ticket_number": "TICK-2024-001-101"
}
```

**Response** (200):
```json
{
  "detail": "Check-in successful",
  "ticket": {
    "id": 101,
    "ticket_number": "TICK-2024-001-101",
    "attendee": "John Doe",
    "ticket_type": "General Admission",
    "checked_in": true,
    "check_in_time": "2024-06-15T09:45:00Z"
  }
}
```

### Menus

#### List Menus
```http
GET /api/menus/?event={event_id}
```

**Response** (200):
```json
[
  {
    "id": 1,
    "event": 1,
    "vendor": {
      "id": 7,
      "username": "food_vendor",
      "email": "vendor@example.com"
    },
    "name": "Main Event Menu",
    "description": "Food and beverages",
    "is_active": true,
    "items": [
      {
        "id": 1,
        "name": "Burger",
        "description": "Beef burger with fries",
        "price": "12.00",
        "category": "Entrees",
        "dietary_info": ["gluten-free-option"],
        "is_available": true,
        "quantity_available": 50
      }
    ]
  }
]
```

#### Create Menu
```http
POST /api/menus/
Authorization: Bearer {token}
Role: vendor or organizer
```

**Request**:
```json
{
  "event_id": 1,
  "name": "VIP Lounge Menu",
  "description": "Exclusive menu for VIP guests",
  "items": [
    {
      "name": "Gourmet Burger",
      "description": "Premium burger",
      "price": "18.00",
      "category_id": 2,
      "dietary_info": ["gluten-free"],
      "quantity_available": 30
    }
  ]
}
```

### Food Orders

#### Create Food Order
```http
POST /api/food/order/
Authorization: Bearer {token}
```

**Request**:
```json
{
  "event_id": 1,
  "items": [
    {
      "item_id": 1,
      "quantity": 2,
      "special_instructions": "No onions"
    },
    {
      "item_id": 5,
      "quantity": 1
    }
  ],
  "table_number": "A12"
}
```

**Response** (201):
```json
{
  "order_id": 42,
  "event": 1,
  "items": [
    {
      "item": "Burger",
      "quantity": 2,
      "price": "12.00",
      "subtotal": "24.00",
      "special_instructions": "No onions"
    },
    {
      "item": "Soda",
      "quantity": 1,
      "price": "3.00",
      "subtotal": "3.00"
    }
  ],
  "total_amount": "27.00",
  "payment_intent": {
    "id": "pi_food_123",
    "client_secret": "pi_food_123_secret",
    "amount": 2700,
    "currency": "usd"
  },
  "table_number": "A12",
  "status": "pending"
}
```

### Reviews

#### List Reviews
```http
GET /api/reviews/?event={event_id}
```

**Response** (200):
```json
[
  {
    "id": 1,
    "event": 1,
    "user": {
      "id": 3,
      "username": "john_doe"
    },
    "rating": 5,
    "comment": "Amazing event!",
    "created_at": "2024-06-16T10:00:00Z"
  }
]
```

#### Create Review
```http
POST /api/reviews/
Authorization: Bearer {token}
```

**Request**:
```json
{
  "event_id": 1,
  "rating": 5,
  "comment": "Great organization and venue!"
}
```

**Response** (201):
```json
{
  "id": 15,
  "event": 1,
  "user": {
    "id": 3,
    "username": "john_doe"
  },
  "rating": 5,
  "comment": "Great organization and venue!",
  "created_at": "2024-06-16T10:30:00Z"
}
```

### Analytics

#### Get Event Analytics
```http
GET /api/analytics/event/{event_id}/
Authorization: Bearer {token}
Role: organizer (owner only) or admin
```

**Response** (200):
```json
{
  "event_id": 1,
  "event_title": "Tech Conference 2024",
  "views": 1250,
  "total_registrations": 387,
  "checked_in": 342,
  "attendance_rate": "88.37%",
  "revenue": {
    "tickets": "18550.00",
    "food": "4320.00",
    "total": "22870.00"
  },
  "ticket_sales": [
    {
      "ticket_type": "General Admission",
      "sold": 320,
      "revenue": "16000.00"
    },
    {
      "ticket_type": "VIP",
      "sold": 67,
      "revenue": "10050.00"
    }
  ],
  "average_rating": 4.7,
  "total_reviews": 89
}
```

### Follow System

#### Follow User
```http
POST /api/users/follow/{user_id}/
Authorization: Bearer {token}
```

**Response** (200):
```json
{
  "detail": "Successfully followed user"
}
```

#### Unfollow User
```http
DELETE /api/users/follow/{user_id}/
Authorization: Bearer {token}
```

#### Get Followers
```http
GET /api/users/followers/
Authorization: Bearer {token}
```

#### Get Following
```http
GET /api/users/following/
Authorization: Bearer {token}
```

## Rate Limiting

Currently no rate limiting is implemented. Will be added in future versions.

## Webhook Endpoints

### Stripe Webhook
```http
POST /api/webhooks/stripe/
Stripe-Signature: {signature}
```

Handles Stripe events:
- `payment_intent.succeeded`
- `payment_intent.payment_failed`
- `charge.refunded`

## Interactive Documentation

For interactive API testing:
- **Swagger UI**: http://localhost:8000/api/docs/
- **ReDoc**: http://localhost:8000/api/redoc/

## Error Codes

| Status Code | Description |
|-------------|-------------|
| 200 | Success |
| 201 | Created |
| 204 | No Content |
| 400 | Bad Request / Validation Error |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 500 | Internal Server Error |

## Common Headers

**Request Headers**:
```
Authorization: Bearer {access_token}
Content-Type: application/json
```

**Response Headers**:
```
Content-Type: application/json
```

## SDK Examples (Coming Soon)

- Python SDK
- JavaScript/TypeScript SDK
- React Hooks
- Vue Composables
