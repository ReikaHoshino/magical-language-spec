#!/usr/bin/env python3
"""Keep the security contract in the standard unittest regression path."""
from __future__ import annotations

import unittest

from validate_security_contract import validate_contract


class SecurityContractTests(unittest.TestCase):
    def test_normative_contract_and_examples_are_synchronized(self) -> None:
        validate_contract()


if __name__ == "__main__":
    unittest.main()
