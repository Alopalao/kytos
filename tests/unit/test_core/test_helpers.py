"""Test kytos.core.helpers module."""
from unittest import TestCase
from unittest.mock import MagicMock, patch

from kytos.core.helpers import (alisten_to, executors,
                                get_thread_pool_max_workers, get_time,
                                listen_to, run_on_thread)


async def test_alisten_to():
    """Test alisten_to decorator."""

    class SomeClass:
        """SomeClass."""

        @alisten_to("some_event")
        async def on_some_event(self, event):
            """On some event handler."""
            _ = event
            return "some_response"

    assert SomeClass.on_some_event.__name__ == "inner"
    result = await SomeClass().on_some_event(MagicMock())
    assert result == "some_response"


class TestHelpers(TestCase):
    """Test the helpers methods."""

    @staticmethod
    @patch('kytos.core.helpers.Thread')
    def test_run_on_thread(mock_thread):
        """Test run_on_thread decorator."""

        @run_on_thread
        def test():
            pass

        test()

        mock_thread.return_value.start.assert_called()

    @staticmethod
    def test_default_executors():
        """Test default expected executors."""
        pools = ["app", "db", "sb"]
        assert sorted(pools) == sorted(executors.keys())

    @staticmethod
    def test_listen_to_run_on_threadpool_by_default():
        """Test listen_to runs on ThreadPoolExecutor by default."""

        assert get_thread_pool_max_workers()
        assert "app" in executors
        executors["app"] = MagicMock()
        mock_executor = executors["app"]

        @listen_to("some_event")
        def test(event):
            _ = event

        assert test({}) is None
        mock_executor.submit.assert_called()

    def test_get_time__str(self):
        """Test get_time method passing a string as parameter."""
        date = get_time("2000-01-01T00:30:00")

        self.assertEqual(date.year, 2000)
        self.assertEqual(date.month, 1)
        self.assertEqual(date.day, 1)
        self.assertEqual(date.hour, 0)
        self.assertEqual(date.minute, 30)
        self.assertEqual(date.second, 0)

    def test_get_time__dict(self):
        """Test get_time method passing a dict as parameter."""
        date = get_time({"year": 2000,
                         "month": 1,
                         "day": 1,
                         "hour": 00,
                         "minute": 30,
                         "second": 00})

        self.assertEqual(date.year, 2000)
        self.assertEqual(date.month, 1)
        self.assertEqual(date.day, 1)
        self.assertEqual(date.hour, 0)
        self.assertEqual(date.minute, 30)
        self.assertEqual(date.second, 0)

    def test_get_time__none(self):
        """Test get_time method by not passing a parameter."""
        date = get_time()

        self.assertIsNone(date)
