import unittest

from impossible_travel.utils.utils import build_device_fingerprint


class TestBuildDeviceFingerprint(unittest.TestCase):
    def test_empty_agent(self):
        """Should return fallback when agent is empty."""
        result = build_device_fingerprint("")
        self.assertEqual(
            result, "unknownos-unknownosmajor-unknowndevice-unknownbrowser"
        )

    def test_invalid_agent_string(self):
        """Should return fallback for invalid or unparseable user agent."""
        result = build_device_fingerprint("!!!not a valid user agent!!!")
        # Should still produce a fingerprint with unknown parts, not crash
        self.assertIn("unknown", result.lower())

    def test_linux_desktop_agent(self):
        """Should detect desktop from X11/Linux UA."""
        ua = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Ubuntu Chromium/78.0.3904.108 "
            "Chrome/78.0.3904.108 Safari/537.36"
        )
        result = build_device_fingerprint(ua)
        self.assertIn("ubuntu", result)
        self.assertIn("unknownosmajor", result)
        self.assertIn("desktop", result)
        self.assertIn("chromium", result)
        self.assertEqual("ubuntu-unknownosmajor-desktop-chromium", result)

    def test_windows_desktop_agent(self):
        """Should detect desktop from Windows UA."""
        ua = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36"
        )
        result = build_device_fingerprint(ua)
        self.assertIn("windows", result)
        self.assertIn("10", result)
        self.assertIn("desktop", result)
        self.assertIn("chrome", result)
        self.assertEqual("windows-10-desktop-chrome", result)

    def test_android_mobile_agent(self):
        """Should detect mobile device from Android UA."""
        ua = (
            "Mozilla/5.0 (Linux; Android 13; Pixel 8) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/118.0 Mobile Safari/537.36"
        )
        result = build_device_fingerprint(ua)
        self.assertIn("android", result)
        self.assertIn("13", result)
        self.assertIn("mobile", result)
        self.assertIn("chrome", result)
        self.assertEqual("android-13-mobile-chrome", result)

    def test_ipad_tablet_agent(self):
        """Should detect tablet from iPad UA."""
        ua = (
            "Mozilla/5.0 (iPad; CPU OS 17_1 like Mac OS X) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/604.1"
        )
        result = build_device_fingerprint(ua)
        self.assertIn("ios", result)
        self.assertIn("17", result)
        self.assertIn("tablet", result)
        self.assertIn("mobilesafariui/wkwebview", result)
        self.assertEqual("ios-17-tablet-mobilesafariui/wkwebview", result)

    def test_iphone_mobile_agent(self):
        """Should detect mobile from iPhone UA."""
        ua = (
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
        )
        result = build_device_fingerprint(ua)
        self.assertIn("ios", result)
        self.assertIn("17", result)
        self.assertIn("mobile", result)
        self.assertIn("safari", result)
        self.assertEqual("ios-17-mobile-mobilesafari", result)

    def test_generic_unknown_agent(self):
        """Should handle unknown/rare UA"""
        ua = "SomeRandomStringWithoutKnownPatterns"
        result = build_device_fingerprint(ua)
        # The parser should still return something, but likely unknown
        self.assertTrue(len(result) > 0)
        self.assertIn("unknown", result)
