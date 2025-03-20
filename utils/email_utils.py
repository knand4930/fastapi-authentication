from pydantic import BaseModel, EmailStr
import aiosmtplib
from email.message import EmailMessage

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = "your-email@gmail.com"
SMTP_PASSWORD = "your-app-password"

class EmailSchema(BaseModel):
    recipient: EmailStr
    subject: str
    body: str

# Function to Send Email
async def send_email(email: EmailSchema):
    msg = EmailMessage()
    msg["From"] = SMTP_USERNAME
    msg["To"] = email.recipient
    msg["Subject"] = email.subject
    msg.set_content(email.body)

    # Sending Email
    await aiosmtplib.send(
        msg,
        hostname=SMTP_SERVER,
        port=SMTP_PORT,
        username=SMTP_USERNAME,
        password=SMTP_PASSWORD,
        start_tls=True,
    )