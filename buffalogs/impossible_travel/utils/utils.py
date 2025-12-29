from ua_parser import user_agent_parser


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

    if not agent:
        return UNKNOWN_FINGERPRINT

    try:
        parsed = user_agent_parser.Parse(agent)
    except Exception:
        return UNKNOWN_FINGERPRINT

    os_data = parsed.get("os", {}) or {}
    ua_data = parsed.get("user_agent", {}) or {}
    device_data = parsed.get("device", {}) or {}

    os_family = (os_data.get("family") or UNKNOWN_OS).strip().lower()
    os_major = (os_data.get("major") or UNKNOWN_OS_MAJOR).strip().lower()
    device_family = (device_data.get("family") or UNKNOWN_DEVICE).strip().lower()
    browser_family = (ua_data.get("family") or UNKNOWN_BROWSER).strip().lower()

    agent_lower = agent.lower()

    # Heuristic for device type
    if any(x in agent_lower for x in ["x11", "win64", "wow64", "x86_64", "macintosh"]):
        device_family = "desktop"
    elif "tablet" in agent_lower or "ipad" in agent_lower:
        device_family = "tablet"
    elif "mobile" in agent_lower:
        device_family = "mobile"

    os_part = f"{os_family}-{os_major}".replace(" ", "")
    device_part = device_family.replace(" ", "")
    browser_part = browser_family.replace(" ", "")

    fingerprint = f"{os_part}-{device_part}-{browser_part}"

    # if all values are unkwown, return the fallback string
    if fingerprint == UNKNOWN_FINGERPRINT:
        return UNKNOWN_FINGERPRINT

    return fingerprint
