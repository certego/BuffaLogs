from django.core.exceptions import ValidationError
from django.test import TestCase
from impossible_travel.validators import StringOrRegexValidator


class StringOrRegexValidatorTest(TestCase):
    def setUp(self):
        self.validator = StringOrRegexValidator()

    def test_invalid_type_exception(self):
        """Test with not a list value"""
        with self.assertRaises(ValidationError) as context:
            self.validator("Siddhartha")
        self.assertIn("The value 'Siddhartha' must be a list", str(context.exception))

    def test_invalid_strings_exception(self):
        """Test with no string values"""
        with self.assertRaises(ValidationError) as context:
            self.validator(["Hermann Hesse", 123])
        self.assertIn("The single element '123' in the '['Hermann Hesse', 123]' list field is not a valid string", str(context.exception))

    def test_invalid_regex_exception(self):
        """Test with invalid regex"""
        with self.assertRaises(ValidationError) as context:
            self.validator(["Hermann Hesse", "[a-z"])
        self.assertIn("The single element '[a-z' in the '['Hermann Hesse', '[a-z']' list field is not a valid regex pattern", str(context.exception))

    def test_empty_list_valid(self):
        """Test with empty default list"""
        # no exception
        try:
            self.validator([])
        except ValidationError:
            self.fail("The test for the validation with an empty list shouldn't fail")

    def test_strings_and_regex_valid(self):
        """Test with a list of valid strings and regex"""
        # no exception
        try:
            self.validator(["user1", "[a-z]+.*", "user1@gmail.com"])
        except ValidationError:
            self.fail("The test with correct list values shouldn't fail")
