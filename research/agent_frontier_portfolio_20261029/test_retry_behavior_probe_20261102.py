from retry_behavior_probe_20261102 import bounded_case, regular_case


class Clock:
    def __init__(self):
        self.sleep_calls = []

    def sleep(self, value):
        self.sleep_calls.append(value)


class Api:
    def __init__(self, limits):
        self.trace = []


def test_regular_check_requires_correct_result_and_delay():
    def incomplete(_cases, _api, clock, max_retries):
        return {"probe": {"case_id": "probe", "value": "payload-probe"}}

    assert regular_case(incomplete, Api, Clock, 5)["passed"] is False
    assert regular_case(incomplete, Api, Clock, 0)["passed"] is True


def test_bounded_check_rejects_unexplained_return():
    assert bounded_case(lambda *_args, **_kwargs: {}, Clock, 3)["passed"] is False
