"""Safe send-now only on exact owner marker and genuine Pinterest public links."""
import os
import unittest
from unittest.mock import patch
from scripts.publish_existing_buffer_now_once import main, valid_public_pin

class SendExistingPinNowTests(unittest.TestCase):
    def test_rejects_unapproved_invocation_before_api_use(self):
        with patch.dict(os.environ, {"KINDGRID_PIN_NOW_AUTHORIZATION": ""}):
            with self.assertRaisesRegex(ValueError, "Not owner-authorized"):
                main()

    def test_public_pin_requires_pinterest_https_pin_path(self):
        self.assertTrue(valid_public_pin("https://www.pinterest.com/pin/1114148395353000000"))
        self.assertFalse(valid_public_pin("https://example.com/pin/1"))
        self.assertFalse(valid_public_pin("http://www.pinterest.com/pin/1"))
        self.assertFalse(valid_public_pin("https://www.pinterest.com/user/"))
if __name__ == "__main__":
    unittest.main()
