"""No owner marker means seller recovery is structurally forbidden."""
import os
import unittest
from unittest.mock import patch
from scripts.recover_pair020_once import main

class KnownDraftRecoverySafetyTests(unittest.TestCase):
    def test_cannot_run_without_exact_one_time_owner_authorization(self):
        with patch.dict(os.environ, {"KINDGRID_RECOVERY_AUTHORIZED": ""}):
            with self.assertRaisesRegex(ValueError, "No owner-scoped recovery authorization"):
                main()

    def test_cannot_run_for_wrong_owner_authorization(self):
        with patch.dict(os.environ, {"KINDGRID_RECOVERY_AUTHORIZED": "another_marker"}):
            with self.assertRaisesRegex(ValueError, "No owner-scoped recovery authorization"):
                main()

if __name__ == "__main__":
    unittest.main()
