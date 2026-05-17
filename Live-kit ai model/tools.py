"""
tools.py — LiveKit Agent Tool Functions for JARVIS
====================================================
Provides callable tools for the LiveKit LLM agent:
  - get_weather       : current weather for a city
  - search_web        : DuckDuckGo web search
  - send_email        : Gmail SMTP
  - open_app_on_phone : launch an Android app on the connected phone via ADB
  - open_app_on_tablet: launch an Android app on the connected tablet via ADB

Android tools use the shared android_launcher module so package resolution
and ADB execution are identical across all JARVIS entry points.
"""
import logging
import os
import sys
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

import requests
from langchain_community.tools import DuckDuckGoSearchRun
from livekit.agents import function_tool, RunContext

logger = logging.getLogger("jarvis.tools")

# Add android_launcher from voice_agent_hub to path
_hub_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "voice_agent_hub"))
if _hub_dir not in sys.path:
    sys.path.insert(0, _hub_dir)

from android_launcher import adb_launch_app, adb_connect  # noqa: E402

# Device IPs from env (same .env used by voice_agent_hub)
_MOBILE_IP  = os.getenv("MOBILE_IP_PORT",  "192.168.1.7:5555")
_TABLET_IP  = os.getenv("TABLET_IP_PORT",  "192.168.1.3:5555")


# ---------------------------------------------------------------------------
@function_tool()
async def get_weather(context: RunContext, city: str) -> str:  # type: ignore
    """Get the current weather for a given city."""
    try:
        response = requests.get(f"https://wttr.in/{city}?format=3", timeout=8)
        if response.status_code == 200:
            logger.info("Weather for %s: %s", city, response.text.strip())
            return response.text.strip()
        return f"Could not retrieve weather for {city}."
    except Exception as exc:
        logger.error("Weather error: %s", exc)
        return f"An error occurred while retrieving weather for {city}."


# ---------------------------------------------------------------------------
@function_tool()
async def search_web(context: RunContext, query: str) -> str:  # type: ignore
    """Search the web using DuckDuckGo and return a summary."""
    try:
        results = DuckDuckGoSearchRun().run(tool_input=query)
        logger.info("Search results for '%s': %s", query, results[:120])
        return results
    except Exception as exc:
        logger.error("Search error: %s", exc)
        return f"An error occurred while searching for '{query}'."


# ---------------------------------------------------------------------------
@function_tool()
async def send_email(  # type: ignore
    context: RunContext,
    to_email: str,
    subject: str,
    message: str,
    cc_email: Optional[str] = None,
) -> str:
    """Send an email through Gmail."""
    try:
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        gmail_user = os.getenv("GMAIL_USER")
        gmail_password = os.getenv("GMAIL_APP_PASSWORD")

        if not gmail_user or not gmail_password:
            return "Email sending failed: Gmail credentials not configured."

        msg = MIMEMultipart()
        msg["From"] = gmail_user
        msg["To"] = to_email
        msg["Subject"] = subject
        recipients = [to_email]
        if cc_email:
            msg["Cc"] = cc_email
            recipients.append(cc_email)
        msg.attach(MIMEText(message, "plain"))

        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(gmail_user, gmail_password)
        server.sendmail(gmail_user, recipients, msg.as_string())
        server.quit()

        logger.info("Email sent to %s", to_email)
        return f"Email sent successfully to {to_email}."
    except smtplib.SMTPAuthenticationError:
        return "Email failed: authentication error. Check Gmail credentials."
    except Exception as exc:
        logger.error("Email error: %s", exc)
        return f"An error occurred while sending email: {exc}"


# ---------------------------------------------------------------------------
@function_tool()
async def open_app_on_phone(context: RunContext, app_name: str) -> str:  # type: ignore
    """
    Open an app on the connected Android phone.
    Examples: 'whatsapp', 'youtube', 'instagram', 'settings', 'chrome'.
    """
    logger.info("[Tool] open_app_on_phone('%s') -> %s", app_name, _MOBILE_IP)
    adb_connect(_MOBILE_IP)
    success, message = adb_launch_app(_MOBILE_IP, app_name)
    return message


# ---------------------------------------------------------------------------
@function_tool()
async def open_app_on_tablet(context: RunContext, app_name: str) -> str:  # type: ignore
    """
    Open an app on the connected Android tablet.
    Examples: 'whatsapp', 'youtube', 'netflix', 'settings'.
    """
    logger.info("[Tool] open_app_on_tablet('%s') -> %s", app_name, _TABLET_IP)
    adb_connect(_TABLET_IP)
    success, message = adb_launch_app(_TABLET_IP, app_name)
    return message