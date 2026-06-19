import unittest


class FakeSession:
    def __init__(self) -> None:
        self.committed = False
        self.rolled_back = False
        self.closed = False

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        self.rolled_back = True

    def close(self) -> None:
        self.closed = True


class DbSessionDependencyTest(unittest.TestCase):
    def test_get_db_commits_after_successful_request(self) -> None:
        import src.db.session as session_module

        fake_session = FakeSession()
        original_session_local = session_module.SessionLocal
        session_module.SessionLocal = lambda: fake_session
        try:
            dependency = session_module.get_db()
            self.assertIs(fake_session, next(dependency))
            with self.assertRaises(StopIteration):
                next(dependency)
        finally:
            session_module.SessionLocal = original_session_local

        self.assertTrue(fake_session.committed)
        self.assertFalse(fake_session.rolled_back)
        self.assertTrue(fake_session.closed)

    def test_get_db_rolls_back_after_error(self) -> None:
        import src.db.session as session_module

        fake_session = FakeSession()
        original_session_local = session_module.SessionLocal
        session_module.SessionLocal = lambda: fake_session
        try:
            dependency = session_module.get_db()
            self.assertIs(fake_session, next(dependency))
            with self.assertRaises(RuntimeError):
                dependency.throw(RuntimeError("boom"))
        finally:
            session_module.SessionLocal = original_session_local

        self.assertFalse(fake_session.committed)
        self.assertTrue(fake_session.rolled_back)
        self.assertTrue(fake_session.closed)


if __name__ == "__main__":
    unittest.main()
