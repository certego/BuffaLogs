from django.core.exceptions import ValidationError
from django.test import TestCase
from impossible_travel.validators import validate_string_or_regex


class ValidatorsTest(TestCase):
    """Class for testing validators.py methods"""

    def test_validate_string_or_regex_invalid_type(self):
        """Test with not a list value"""
        with self.assertRaises(ValidationError) as context:
            validate_string_or_regex(value="Siddhartha")
        self.assertIn("The value 'Siddhartha' must be a list", str(context.exception))

    def test_validate_string_or_regex_invalid_string(self):
        """Test with no string values"""
        with self.assertRaises(ValidationError) as context:
            validate_string_or_regex(["Hermann Hesse", 123])
        self.assertIn("The single element '123' in the '['Hermann Hesse', 123]' list field is not a valid string", str(context.exception))

    def test_validate_string_or_regex_invalid_regex(self):
        """Test with invalid regex"""
        with self.assertRaises(ValidationError) as context:
            validate_string_or_regex(["Hermann Hesse", "[a-z"])
        self.assertIn("The single element '[a-z' in the '['Hermann Hesse', '[a-z']' list field is not a valid regex pattern", str(context.exception))

    def test_validate_string_or_regex_empty_list(self):
        """Test with empty default list"""
        # no exception
        try:
            validate_string_or_regex([])
        except ValidationError:
            self.fail("The test for the validation with an empty list shouldn't fail")

    def test_validate_string_or_regex_valid(self):
        """Test with a list of valid strings and regex"""
        valid_values = ["Pluto", "[a-z]+.*", "Dog"]
        # no exception
        try:
            validate_string_or_regex(valid_values)
        except ValidationError:
            self.fail("The test with correct list values shouldn't fail")
