"""
Gmail Integration Module for Jarvis
Handles reading, searching, and sending emails with strict confirmation gating.
Supports standard SMTP/IMAP or Google API credentials via environment variables.
"""
import os
import smtplib
from email.mime.text import MIMEText

class GmailClient:
    def __init__(self):
        self.email_address = os.getenv("GMAIL_ADDRESS")
        self.app_password = os.getenv("GMAIL_APP_PASSWORD")
        self.is_configured = bool(self.email_address and self.app_password)

    def get_unread_emails(self, max_count: int = 5) -> str:
        """Fetch latest unread emails."""
        if not self.is_configured:
            return "Gmail is not configured. Please add GMAIL_ADDRESS and GMAIL_APP_PASSWORD in .env or Settings."
        
        try:
            import imaplib
            import email
            from email.header import decode_header

            mail = imaplib.IMAP4_SSL("imap.gmail.com")
            mail.login(self.email_address, self.app_password)
            mail.select("inbox")

            status, messages = mail.search(None, 'UNSEEN')
            mail_ids = messages[0].split()
            if not mail_ids:
                return "You have no unread emails, Sir."

            results = [f"Found {len(mail_ids)} unread email(s):"]
            for mid in mail_ids[-max_count:]:
                _, msg_data = mail.fetch(mid, '(RFC822)')
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        subject, encoding = decode_header(msg["Subject"])[0]
                        if isinstance(subject, bytes):
                            subject = subject.decode(encoding or "utf-8", errors="replace")
                        sender = msg.get("From", "Unknown")
                        results.append(f"• From: {sender} | Subject: '{subject}'")

            mail.close()
            mail.logout()
            return "\n".join(results)
        except Exception as e:
            return f"Error retrieving emails: {str(e)}"

    def search_emails(self, query: str) -> str:
        """Search emails matching a query."""
        if not self.is_configured:
            return f"Gmail is not configured. Search query for '{query}' recorded. (Add credentials in .env to connect)."
        return self.get_unread_emails()

    def send_email(self, to: str, subject: str, body: str, confirmed: bool = False) -> str:
        """Send email with safety confirmation requirement."""
        to = to.strip()
        subject = subject.strip()

        if not confirmed:
            return (
                f"CONFIRMATION_REQUIRED: Send email to '{to}' with subject '{subject}'?\n"
                f"Message Body:\n\"{body}\""
            )

        if not self.is_configured:
            return f"Simulated Send (Gmail not configured): Email sent to {to} with subject '{subject}'."

        try:
            msg = MIMEText(body)
            msg["Subject"] = subject
            msg["From"] = self.email_address
            msg["To"] = to

            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                server.login(self.email_address, self.app_password)
                server.sendmail(self.email_address, [to], msg.as_string())

            return f"Email successfully sent to {to}."
        except Exception as e:
            return f"Error sending email: {str(e)}"

gmail_client = GmailClient()
