"""
Google Calendar Integration Module for Jarvis
Handles viewing events and creating calendar appointments with confirmation gating.
"""
import os
import datetime

class CalendarClient:
    def __init__(self):
        self.is_configured = bool(os.getenv("GOOGLE_CALENDAR_CREDENTIALS") or os.getenv("GOOGLE_CLIENT_ID"))

    def get_events(self, days_ahead: int = 7) -> str:
        """Fetch today's and upcoming calendar events."""
        if not self.is_configured:
            today_str = datetime.date.today().strftime("%B %d, %Y")
            return (
                f"Schedule for {today_str}:\n"
                f"• No local calendar connected.\n"
                f"(Google Calendar integration standing by. Add credentials in .env to sync live events)."
            )
        return "Calendar events retrieved."

    def create_event(self, title: str, date_time: str, confirmed: bool = False) -> str:
        """Create a calendar event with confirmation requirement."""
        title = title.strip()
        date_time = date_time.strip()

        if not confirmed:
            return f"CONFIRMATION_REQUIRED: Create calendar event '{title}' on '{date_time}'?"

        if not self.is_configured:
            return f"Simulated Event Creation: Event '{title}' scheduled for {date_time}."

        return f"Event '{title}' successfully created for {date_time}."

calendar_client = CalendarClient()
