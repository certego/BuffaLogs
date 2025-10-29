from ua_parser import user_agent_parser


def build_device_fingerprint(agent: str) -> str:
    """
    Builds a normalized device fingerprint string: OS-OSversionmajor-Device-Broser from a user-agent full string
    Example output: 'Windows-10-Desktop-Chrome'

    :param agent: user-agent full string
    :type agent: str

    :return: string with fingerprint or 'UnknownFingerprint'
    :rtype: str
    """
    # generic fallback
    if not agent:
        return "UnknownOS-UnknownOSmajor-UnknownDevice-UnknownBrowser"

    try:
        parsed = user_agent_parser.Parse(agent)
    except Exception:
        return "UnknownOS-UnknownOSmajor-UnknownDevice-UnknownBrowser"

    # Safe extraction
    os_data = parsed.get("os", {}) or {}
    ua_data = parsed.get("user_agent", {}) or {}
    device_data = parsed.get("device", {}) or {}

    os_family = os_data.get("family") or "UnknownOS"
    os_major = os_data.get("major") or ""
    device_family = device_data.get("family") or "UnknownDevice"
    browser_family = ua_data.get("family") or "UnknownBrowser"

    # Build OS part with major version if available
    if os_major:
        os_part = f"{os_family}-{os_major}"
    else:
        os_part = os_family

    # Clean and normalize
    os_part = os_part.strip().replace(" ", "")
    device_part = device_family.strip().replace(" ", "")
    browser_part = browser_family.strip().replace(" ", "")

    fingerprint = f"{os_part}-{device_part}-{browser_part}".lower()

    return fingerprint or "UnknownFingerprint"
