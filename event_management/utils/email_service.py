import resend
from django.conf import settings
from django.utils import timezone

# Initialize Resend
resend.api_key = settings.RESEND_API_KEY


class EmailService:
    """Service for sending emails via Resend"""

    @staticmethod
    def send_email(to_email, subject, html_content, from_email=None):
        """
        Send an email using Resend

        Args:
            to_email: Recipient email address (string or list)
            subject: Email subject
            html_content: HTML content of the email
            from_email: Sender email (optional, uses DEFAULT_FROM_EMAIL if not provided)

        Returns:
            Email send response
        """
        try:
            if not from_email:
                from_email = settings.DEFAULT_FROM_EMAIL

            # Ensure to_email is a list
            if isinstance(to_email, str):
                to_email = [to_email]

            params = {
                "from": from_email,
                "to": to_email,
                "subject": subject,
                "html": html_content,
            }

            response = resend.Emails.send(params)
            return response
        except Exception as e:
            raise Exception(f"Email sending error: {str(e)}")

    @staticmethod
    def send_verification_email(user, verification_url):
        """Send email verification email"""
        subject = "Verify Your Email Address"
        html_content = f"""
        <html>
            <body>
                <h2>Welcome to Event Management System!</h2>
                <p>Hi {user.first_name or user.username},</p>
                <p>Thank you for registering. Please verify your email address by clicking the link below:</p>
                <p><a href="{verification_url}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Verify Email</a></p>
                <p>Or copy and paste this URL into your browser:</p>
                <p>{verification_url}</p>
                <p>If you didn't create an account, please ignore this email.</p>
                <br>
                <p>Best regards,<br>Event Management Team</p>
            </body>
        </html>
        """
        return EmailService.send_email(user.email, subject, html_content)

    @staticmethod
    def send_password_reset_email(user, reset_url):
        """Send password reset email"""
        subject = "Reset Your Password"
        html_content = f"""
        <html>
            <body>
                <h2>Password Reset Request</h2>
                <p>Hi {user.first_name or user.username},</p>
                <p>We received a request to reset your password. Click the link below to reset it:</p>
                <p><a href="{reset_url}" style="background-color: #2196F3; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Reset Password</a></p>
                <p>Or copy and paste this URL into your browser:</p>
                <p>{reset_url}</p>
                <p>If you didn't request a password reset, please ignore this email.</p>
                <br>
                <p>Best regards,<br>Event Management Team</p>
            </body>
        </html>
        """
        return EmailService.send_email(user.email, subject, html_content)

    @staticmethod
    def send_registration_confirmation(user, event, ticket):
        """Send event registration confirmation email"""
        subject = f"Registration Confirmed: {event.title}"
        html_content = f"""
        <html>
            <body>
                <h2>Registration Confirmed!</h2>
                <p>Hi {user.first_name or user.username},</p>
                <p>Your registration for <strong>{event.title}</strong> has been confirmed!</p>
                <h3>Event Details:</h3>
                <ul>
                    <li><strong>Event:</strong> {event.title}</li>
                    <li><strong>Date:</strong> {event.start_date.strftime('%B %d, %Y at %I:%M %p')}</li>
                    <li><strong>Venue:</strong> {event.venue_name}</li>
                    <li><strong>Address:</strong> {event.venue_address}</li>
                    <li><strong>Ticket Number:</strong> {ticket.ticket_number}</li>
                </ul>
                <p>Your ticket with QR code will be available in your account.</p>
                <p><a href="{settings.FRONTEND_URL}/my-tickets/{ticket.ticket_number}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">View Ticket</a></p>
                <p>We look forward to seeing you at the event!</p>
                <br>
                <p>Best regards,<br>Event Management Team</p>
            </body>
        </html>
        """
        return EmailService.send_email(user.email, subject, html_content)

    @staticmethod
    def send_event_reminder(user, event):
        """Send event reminder email"""
        subject = f"Reminder: {event.title} is Coming Up!"
        html_content = f"""
        <html>
            <body>
                <h2>Event Reminder</h2>
                <p>Hi {user.first_name or user.username},</p>
                <p>This is a reminder that <strong>{event.title}</strong> is coming up soon!</p>
                <h3>Event Details:</h3>
                <ul>
                    <li><strong>Date:</strong> {event.start_date.strftime('%B %d, %Y at %I:%M %p')}</li>
                    <li><strong>Venue:</strong> {event.venue_name}</li>
                    <li><strong>Address:</strong> {event.venue_address}</li>
                </ul>
                <p>Don't forget to bring your ticket!</p>
                <p><a href="{settings.FRONTEND_URL}/events/{event.slug}" style="background-color: #2196F3; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">View Event</a></p>
                <br>
                <p>Best regards,<br>Event Management Team</p>
            </body>
        </html>
        """
        return EmailService.send_email(user.email, subject, html_content)

    @staticmethod
    def send_food_order_confirmation(user, food_order):
        """Send food order confirmation email"""
        subject = f"Food Order Confirmed: Order #{food_order.order_number}"
        items_html = "".join([
            f"<li>{item.quantity}x {item.menu_item.name} - ${item.total_price}</li>"
            for item in food_order.items.all()
        ])
        html_content = f"""
        <html>
            <body>
                <h2>Food Order Confirmed!</h2>
                <p>Hi {user.first_name or user.username},</p>
                <p>Your food order has been confirmed!</p>
                <h3>Order Details:</h3>
                <ul>
                    <li><strong>Order Number:</strong> {food_order.order_number}</li>
                    <li><strong>Event:</strong> {food_order.event.title}</li>
                    <li><strong>Total:</strong> ${food_order.total}</li>
                    <li><strong>Table Number:</strong> {food_order.table_number or 'N/A'}</li>
                </ul>
                <h3>Items:</h3>
                <ul>
                    {items_html}
                </ul>
                <p>Your order is being prepared and will be ready soon!</p>
                <br>
                <p>Best regards,<br>Event Management Team</p>
            </body>
        </html>
        """
        return EmailService.send_email(user.email, subject, html_content)
