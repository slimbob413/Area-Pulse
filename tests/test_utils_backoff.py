from src.utils import retry

def test_retry_success_after_failures():
    calls = []
    @retry(max_attempts=3, initial_delay=0)
    def flaky():
        if len(calls) < 2:
            calls.append('fail')
            raise ValueError('fail')
        return 'ok'
    result = flaky()
    assert result == 'ok'
    assert calls == ['fail', 'fail'] 