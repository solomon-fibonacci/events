import qrcode
from io import BytesIO
from django.core.files import File
from PIL import Image


class QRCodeService:
    """Service for generating QR codes"""

    @staticmethod
    def generate_qr_code(data, fill_color="black", back_color="white"):
        """
        Generate a QR code image

        Args:
            data: Data to encode in the QR code
            fill_color: Foreground color
            back_color: Background color

        Returns:
            BytesIO object containing the QR code image
        """
        try:
            # Create QR code instance
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )

            # Add data
            qr.add_data(data)
            qr.make(fit=True)

            # Create image
            img = qr.make_image(fill_color=fill_color, back_color=back_color)

            # Save to BytesIO
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)

            return buffer
        except Exception as e:
            raise Exception(f"QR code generation error: {str(e)}")

    @staticmethod
    def generate_ticket_qr_code(ticket):
        """
        Generate a QR code for a ticket

        Args:
            ticket: Registration/Ticket object

        Returns:
            File object
        """
        try:
            # Create QR code data (can be the ticket number or a verification URL)
            qr_data = f"{ticket.ticket_number}"

            # Generate QR code
            qr_buffer = QRCodeService.generate_qr_code(qr_data)

            # Create a Django File object
            filename = f"ticket_{ticket.ticket_number}.png"
            qr_file = File(qr_buffer, name=filename)

            return qr_file
        except Exception as e:
            raise Exception(f"Ticket QR code generation error: {str(e)}")

    @staticmethod
    def generate_event_share_qr_code(event):
        """
        Generate a QR code for sharing an event

        Args:
            event: Event object

        Returns:
            BytesIO object containing the QR code image
        """
        try:
            from django.conf import settings
            # Create event URL
            event_url = f"{settings.FRONTEND_URL}/events/{event.slug}"

            # Generate QR code
            qr_buffer = QRCodeService.generate_qr_code(event_url)

            return qr_buffer
        except Exception as e:
            raise Exception(f"Event QR code generation error: {str(e)}")
