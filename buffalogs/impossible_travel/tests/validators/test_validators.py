import datetime

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils.timezone import get_current_timezone, is_naive, make_aware
from impossible_travel.models import get_default_allowed_countries
from impossible_travel.validators import (
    validate_alert_query,
    validate_boolean_str,
    validate_countries_names,
    validate_country_couples_list,
    validate_datetime_str,
    validate_ips_or_network,
    validate_login_query,
    validate_risk_score,
    validate_string_or_regex,
)


class ValidatorsTest(TestCase):
    """Class for testing validators.py methods"""

    def test_validate_string_or_regex_invalid_type(self):
        """Testing the function validate_string_or_regex with not a list value"""
        with self.assertRaises(ValidationError) as context:
            validate_string_or_regex(value="Siddhartha")
        self.assertIn("The value 'Siddhartha' must be a list", str(context.exception))

    def test_validate_string_or_regex_invalid_string(self):
        """Testing the function validate_string_or_regex with no string values"""
        with self.assertRaises(ValidationError) as context:
            validate_string_or_regex(["Hermann Hesse", 123])
        self.assertIn(
            "The single element '123' in the '['Hermann Hesse', 123]' list field must be a string",
            str(context.exception),
        )

    def test_validate_string_or_regex_invalid_regex(self):
        """Testing the function validate_string_or_regex with invalid regex"""
        with self.assertRaises(ValidationError) as context:
            validate_string_or_regex(["Hermann Hesse", "[a-z"])
        self.assertIn(
            "The single element '[a-z' in the '['Hermann Hesse', '[a-z']' list field is not a valid regex pattern",
            str(context.exception),
        )

    def test_validate_string_or_regex_empty_list(self):
        """Testing the function validate_string_or_regex with empty default list"""
        # no exception
        try:
            validate_string_or_regex([])
        except ValidationError:
            self.fail("The test for the validation with an empty list shouldn't fail")

    def test_validate_string_or_regex_valid(self):
        """Testing the function validate_string_or_regex with a list of valid strings and regex"""
        valid_values = ["Pluto", "[a-z]+.*", "Dog"]
        # no exception
        try:
            validate_string_or_regex(valid_values)
        except ValidationError:
            self.fail("The test with correct list values shouldn't fail")

    def test_validate_ips_or_network_valid(self):
        """Testing the function validate_ips_or_network with correct list"""
        valid_values = ["192.0.2.0/24", "198.51.100.255", "203.0.113.0"]
        # no exception
        try:
            validate_ips_or_network(valid_values)
        except ValidationError:
            self.fail("The test with correct IPs list values shouldn't fail")

    def test_validate_ips_or_network_invalid_type(self):
        """Testing the function validate_ips_or_network with an incorrect type"""
        with self.assertRaises(ValidationError):
            validate_ips_or_network(["192.0.2.12", 1])

    def test_validate_ips_or_network_invalid_values(self):
        """Testing the function validate_ips_or_network with incorrect values"""
        with self.assertRaises(ValidationError):
            validate_ips_or_network(["12.45.5"])

    def test_validate_countries_names_valid_names(self):
        """Test valid ISO country names pass validation"""
        valid_countries = ["Italy", "Nepal", "United States"]
        try:
            validate_countries_names(valid_countries)
        except ValidationError:
            self.fail("validate_countries_names raised ValidationError unexpectedly!")

    def test_validate_countries_names_invalid_entries(self):
        """Test invalid country names or codes raise ValidationError"""
        invalid_countries = ["Atlantis", "ZZ", "Narnia"]
        with self.assertRaises(ValidationError) as context:
            validate_countries_names(invalid_countries)
        for invalid in invalid_countries:
            self.assertIn(invalid, str(context.exception))

    def test_validate_countries_names_mixed_valid_and_invalid(self):
        """Test mixed valid and invalid entries raise ValidationError listing invalids"""
        mixed = ["Italy", "XX", "Nepal", "UnknownLand"]
        with self.assertRaises(ValidationError) as context:
            validate_countries_names(mixed)
        self.assertIn("XX", str(context.exception))
        self.assertIn("UnknownLand", str(context.exception))
        # valid names shouldn't appear in error
        self.assertNotIn("Italy", str(context.exception))

    def test_validate_countries_names_invalid_type(self):
        """Test non-list inputs raise ValidationError"""
        with self.assertRaises(ValidationError) as context:
            # string instead of list
            validate_countries_names("Italy")
        self.assertIn("Value must be a list", str(context.exception))

    def test_validate_countries_names_default_value(self):
        """Test that the default allowed countries pass validation"""
        default_countries = get_default_allowed_countries()
        try:
            validate_countries_names(default_countries)
        except ValidationError:
            self.fail("validate_countries_names raised ValidationError unexpectedly for default allowed countries!")

    def test_validate_country_couples_list_single_elem(self):
        """Test that a single string (not a list of lists) raises an exception"""
        with self.assertRaises(ValidationError) as context:
            validate_country_couples_list("Italy")
        self.assertIn("Value must be a list.", str(context.exception))

    def test_validate_country_couples_list_single_list(self):
        """Test that a single list (not a list of lists) raises an exception"""
        with self.assertRaises(ValidationError) as context:
            validate_country_couples_list(["Italy", "Germany"])
        self.assertIn("Each single value must be a list of 2 elements (list of lists).", str(context.exception))

    def test_validate_country_couples_list_too_elements(self):
        """Test that a list of more than 2 elements raises an exception"""
        with self.assertRaises(ValidationError) as context:
            validate_country_couples_list([["Italy", "Germany", "France"]])
        self.assertIn("Each single value must be a list of 2 elements (list of lists).", str(context.exception))

    def test_validate_country_couples_list_wrong_country_name(self):
        """Test that a list containing a wrong country name raises an exception"""
        with self.assertRaises(ValidationError) as context:
            validate_country_couples_list([["Italy", "wrong_name"]])
        self.assertIn("The following country names are invalid", str(context.exception))

    def test_validate_country_couples_list_correct(self):
        """Test that a correct list of lists of countries is validated correctly"""
        # no exception
        valid_values = [["Italy", "France"], ["Italy", "Italy"], ["Germany", "France"]]
        try:
            validate_country_couples_list(valid_values)
        except ValidationError:
            self.fail("The test with correct list values shouldn't fail")

    def test_validate_datetime_str_naive_conversion(self):
        """
        Test that a naive datetime string is correctly parsed and made aware.
        """
        naive_dt_str = "2023-10-26 14:30:00"
        aware_dt = validate_datetime_str(naive_dt_str)

        self.assertIsInstance(aware_dt, datetime.datetime)
        self.assertTrue(not is_naive(aware_dt))
        expected_naive = datetime.datetime(2023, 10, 26, 14, 30, 0)
        expected_aware = make_aware(expected_naive, get_current_timezone())
        self.assertEqual(aware_dt, expected_aware)

    def test_validate_datetime_str_aware_passthrough(self):
        """
        Test that an already aware datetime string is correctly parsed and passed through.
        """
        aware_dt_str = "2023-10-26T14:30:00+00:00"
        aware_dt = validate_datetime_str(aware_dt_str)

        self.assertIsInstance(aware_dt, datetime.datetime)
        self.assertTrue(not is_naive(aware_dt))
        expected_aware = datetime.datetime(2023, 10, 26, 14, 30, 0, tzinfo=datetime.timezone.utc)
        self.assertEqual(aware_dt, expected_aware)

    def test_validate_datetime_str_empty_invalid(self):
        """
        Test that empty returns None and invalid strings raises ValidationError.
        """
        self.assertIsNone(validate_datetime_str(""))
        self.assertIsNone(validate_datetime_str(None))
        with self.assertRaises(ValidationError) as cm:
            validate_datetime_str("not a date")

        err_msg = "not a date is not a valid datetime format. Please use ISO 8601 format (e.g., YYYY-MM-DDTHH:MM:SSZ)."
        self.assertIn(err_msg, str(cm.exception))

    def test_validate_boolean_str(self):
        """
        Test various inputs for the boolean string validator.
        """
        # True cases
        self.assertTrue(validate_boolean_str("true"))
        self.assertTrue(validate_boolean_str("True"))

        # False cases`
        self.assertFalse(validate_boolean_str("false"))
        self.assertFalse(validate_boolean_str("False"))

        with self.assertRaisesRegex(ValidationError, "Notification status must be true or false, got anything"):
            self.assertFalse(validate_boolean_str("anything"))

        # None case
        self.assertIsNone(validate_boolean_str(None))

    def test_validate_risk_score_valid(self):
        """
        Test valid integer and string risk scores.
        """
        # Valid integers (0-7), testing string and int input
        self.assertEqual(validate_risk_score(0), 0)
        self.assertEqual(validate_risk_score(7), 7)
        self.assertEqual(validate_risk_score("3"), 3)
        self.assertIsNone(validate_risk_score(None))

        # Valid strings (case insensitive)
        self.assertEqual(validate_risk_score("low"), "Low")
        self.assertEqual(validate_risk_score("MEDIUM"), "Medium")
        self.assertEqual(validate_risk_score("high"), "High")

        # Test empty string
        with self.assertRaisesRegex(ValidationError, "Risk score must be an integer 0-7 or one of: High, Medium, Low, No Risk"):
            validate_risk_score("")

        # Test empty string
        with self.assertRaisesRegex(ValidationError, "Risk score must be an integer 0-7 or one of: High, Medium, Low, No Risk"):
            validate_risk_score("Invalid Risk Score")

        # Test out of range risk score
        with self.assertRaisesRegex(ValidationError, "risk score value is out of range"):
            validate_risk_score("8")

    def test_validate_alert_query_full_valid(self):
        """
        Test with a full dictionary of valid query parameters.
        """
        query_dict = {
            "limit": "100",
            "offset": "50",
            "start": "2023-01-01T00:00:00+00:00",
            "end": "2023-01-02 00:00:00",
            "notified": "true",
            "min_risk_score": "LOW",
            "max_risk_score": "High",
            "ip": "192.168.1.1",
            "name": "Test Alert",
            "user": "testuser",
            "is_vip": "True",
            "country_code": "US",
            "login_start_date": "2022-12-01",
            "login_end_date": "2022-12-31",
            "user_agent": "Mozilla/5.0",
        }

        validated_query = validate_alert_query(query_dict)

        # Expected datetime conversions
        aware_start = datetime.datetime(2023, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)
        naive_end = datetime.datetime(2023, 1, 2, 0, 0, 0)
        aware_end = make_aware(naive_end, get_current_timezone())

        self.assertEqual(validated_query["limit"], 100)
        self.assertEqual(validated_query["offset"], 50)
        self.assertEqual(validated_query["start_date"], aware_start)
        self.assertEqual(validated_query["end_date"], aware_end)
        self.assertEqual(validated_query["notified"], True)
        self.assertEqual(validated_query["min_risk_score"], "Low")
        self.assertEqual(validated_query["max_risk_score"], "High")
        self.assertEqual(validated_query["ip"], "192.168.1.1")
        self.assertEqual(validated_query["username"], "testuser")
        self.assertEqual(validated_query["is_vip"], True)
        self.assertEqual(validated_query["login_start_time"], "2022-12-01")

    def test_validate_alert_query_missing_optional(self):
        """
        Test with minimal dictionary (relying on default values and None for optional fields).
        """
        query_dict = {}
        validated_query = validate_alert_query(query_dict)

        self.assertEqual(validated_query["limit"], 0)
        self.assertEqual(validated_query["offset"], 0)

        # Defaults for string-validated fields are None
        self.assertIsNone(validated_query["start_date"])
        self.assertIsNone(validated_query["end_date"])
        self.assertIsNone(validated_query["notified"])  # "" converts to False
        self.assertIsNone(validated_query["risk_score"])

        # Defaults for simple string fields are None
        self.assertIsNone(validated_query["ip"])
        self.assertIsNone(validated_query["username"])

    def test_validate_alert_query_invalid_types(self):
        """
        Test handling of invalid inputs for limit, datetime, and risk score.
        """
        query_dict = {
            "limit": "abc",
            "offset": "10",
            "start": "not a date",
            "notified": "no",
            "risk_score": "high",
        }
        with self.assertRaises(ValidationError):
            validate_alert_query(query_dict)

    def test_validate_login_query_full_valid(self):
        """
        Test the login query validator with all valid parameters.
        """
        query_dict = {
            "limit": "20",
            "offset": "0",
            "user": "jane doe",
            "country": "CA",
            "login_start_date": "2023-01-01",
            "login_end_date": "2023-01-31",
            "ip": "10.0.0.5",
            "user_agent": "TestBrowser/1.0",
        }

        validated_query = validate_login_query(query_dict)

        self.assertEqual(validated_query["limit"], 20)
        self.assertEqual(validated_query["offset"], 0)
        self.assertEqual(validated_query["username"], "jane doe")
        self.assertEqual(validated_query["country"], "CA")
        self.assertEqual(validated_query["login_start_time"], "2023-01-01")
        self.assertEqual(validated_query["ip"], "10.0.0.5")

    def test_validate_login_query_missing_optional(self):
        """
        Test the login query validator with only limit/offset provided.
        """
        query_dict = {"limit": "5"}
        validated_query = validate_login_query(query_dict)

        self.assertEqual(validated_query["limit"], 5)
        self.assertEqual(validated_query["offset"], 0)  # Default
        self.assertIsNone(validated_query["username"])
        self.assertIsNone(validated_query["country"])

    def test_validate_login_query_invalid_limit(self):
        """
        Test handling of non-integer limit/offset values.
        """
        query_dict = {"limit": "a lot", "offset": "ten"}
        with self.assertRaises(ValidationError):
            validate_login_query(query_dict)
