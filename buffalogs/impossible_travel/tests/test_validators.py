from django.core.exceptions import ValidationError
from django.test import TestCase
from impossible_travel.validators import *


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
        with self.assertRaises(ValidationError) as context:
            validate_ips_or_network(["192.0.2.12", 1])

    def test_validate_ips_or_network_invalid_values(self):
        """Testing the function validate_ips_or_network with incorrect values"""
        with self.assertRaises(ValidationError) as context:
            validate_ips_or_network(["12.45.5"])
