import logging

from ua_parser import user_agent_parser

logger = logging.getLogger(__name__)


def build_device_fingerprint(agent: str) -> str:
    """
    Builds a normalized device fingerprint string: os-osversionmajor-device-browser.
    Example output: 'windows-10-desktop-chrome'.

    Fallbacks:
    - OS family missing -> 'unknownos'
    - OS major missing -> 'unknownosmajor'
    - Device missing -> 'unknowndevice'
    - Browser missing -> 'unknownbrowser'

    Returns 'unknownos-unknownosmajor-unknowndevice-unknownbrowser' if UA is empty or invalid.
    """

    UNKNOWN_OS = "unknownos"
    UNKNOWN_OS_MAJOR = "unknownosmajor"
    UNKNOWN_DEVICE = "unknowndevice"
    UNKNOWN_BROWSER = "unknownbrowser"

    UNKNOWN_FINGERPRINT = f"{UNKNOWN_OS}-{UNKNOWN_OS_MAJOR}-{UNKNOWN_DEVICE}-{UNKNOWN_BROWSER}"

    # Check if the agent is provided
    if not agent:
        return UNKNOWN_FINGERPRINT

    try:
        parsed = user_agent_parser.Parse(agent)
    except Exception as e:
        logger.error(f"Error parsing user agent '{agent}': {e}")
        return UNKNOWN_FINGERPRINT

    # Get the relevant data, with fallbacks to empty dict if not found
    os_data = parsed.get("os", {}) or {}
    ua_data = parsed.get("user_agent", {}) or {}
    device_data = parsed.get("device", {}) or {}

    # Extract values with fallbacks
    os_family = (os_data.get("family") or UNKNOWN_OS).strip().lower()
    os_major = (os_data.get("major") or UNKNOWN_OS_MAJOR).strip().lower()
    device_family = (device_data.get("family") or UNKNOWN_DEVICE).strip().lower()
    browser_family = (ua_data.get("family") or UNKNOWN_BROWSER).strip().lower()

    # Normalize agent string for device type detection
    agent_lower = agent.lower()

    # Heuristic for detecting the device type
    if "mobile" in agent_lower:
        device_family = "mobile"
    elif "tablet" in agent_lower or "ipad" in agent_lower:
        device_family = "tablet"
    elif any(x in agent_lower for x in ["x11", "win64", "wow64", "x86_64", "macintosh"]):
        device_family = "desktop"

    # build fingerprint
    os_part = f"{os_family}-{os_major}".replace(" ", "")
    device_part = device_family.replace(" ", "")
    browser_part = browser_family.replace(" ", "")
    fingerprint = f"{os_part}-{device_part}-{browser_part}"

    # if all values are unkwown, return the fallback string
    if fingerprint == UNKNOWN_FINGERPRINT:
        return UNKNOWN_FINGERPRINT

    return fingerprint
