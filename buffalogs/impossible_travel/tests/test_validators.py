from django.core.exceptions import ValidationError
from django.test import TestCase
from impossible_travel.validators import validate_countries_names, validate_ips_or_network, validate_string_or_regex
from impossible_travel.models import get_default_allowed_countries


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
        self.assertIn("The single element '123' in the '['Hermann Hesse', 123]' list field must be a string", str(context.exception))

    def test_validate_string_or_regex_invalid_regex(self):
        """Testing the function validate_string_or_regex with invalid regex"""
        with self.assertRaises(ValidationError) as context:
            validate_string_or_regex(["Hermann Hesse", "[a-z"])
        self.assertIn("The single element '[a-z' in the '['Hermann Hesse', '[a-z']' list field is not a valid regex pattern", str(context.exception))

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

    def test_validate_countries_names_valid_codes(self):
        """Test valid ISO Alpha-2 country codes pass validation"""
        valid_codes = ["IT", "NP", "US"]
        try:
            validate_countries_names(valid_codes)
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
        self.assertIn("allowed_countries must be a list", str(context.exception))

    def test_validate_countries_names_default_value(self):
        """Test that the default allowed countries pass validation"""
        default_countries = get_default_allowed_countries()
        try:
            validate_countries_names(default_countries)
        except ValidationError:
            self.fail("validate_countries_names raised ValidationError unexpectedly for default allowed countries!")
