"""Offline checks; behavioral prompt changes belong in the live evals."""

import unittest

from agent import Booking, api_error
from evals import check_turn


class BookingTests(unittest.TestCase):
    def test_valid_move_and_normalized_input(self):
        booking = Booking()
        self.assertIn("16A", booking.move(" abc123 ", "16a"))
        self.assertEqual(booking.seat, "16A")

    def test_wrong_booking_preserves_seat(self):
        booking = Booking()
        with self.assertRaisesRegex(ValueError, "Booking not found"):
            booking.move("WRONG1", "16A")
        self.assertEqual(booking.seat, "14C")

    def test_invalid_seats_preserve_booking(self):
        for seat in ("0A", "31A", "12G", "01A", "window", "", "12A\nother"):
            with self.subTest(seat=seat):
                booking = Booking()
                with self.assertRaisesRegex(ValueError, "Invalid seat"):
                    booking.move("ABC123", seat)
                self.assertEqual(booking.seat, "14C")

    def test_valid_boundary_seats(self):
        for seat in ("1A", "30F"):
            with self.subTest(seat=seat):
                booking = Booking()
                booking.move("ABC123", seat)
                self.assertEqual(booking.seat, seat)

    def test_chats_do_not_share_booking_state(self):
        first, second = Booking(), Booking()
        first.move("ABC123", "16A")
        self.assertEqual(second.seat, "14C")


class EvalTests(unittest.TestCase):
    def test_detects_unrequested_action_even_if_final_seat_unchanged(self):
        problems = check_turn("14C", "", Booking(), [{"name": "change_seat"}])
        self.assertTrue(problems)

    def test_detects_missing_tool_even_if_state_looks_correct(self):
        self.assertTrue(check_turn("14C", "lookup_policy", Booking(), []))

    def test_policy_lookup_is_allowed_while_clarifying(self):
        self.assertEqual(check_turn("14C", "", Booking(), [{"name": "lookup_policy"}]), [])

    def test_detects_wrong_seat(self):
        self.assertTrue(check_turn("16A", "", Booking(), []))

    def test_expected_tool_and_state_pass(self):
        self.assertEqual(check_turn("14C", "lookup_policy", Booking(), [{"name": "lookup_policy"}]), [])

    def test_api_errors_do_not_echo_response_or_credentials(self):
        error = RuntimeError("sensitive response body")
        self.assertEqual(api_error(error), "ERROR: RuntimeError")


if __name__ == "__main__":
    unittest.main()
