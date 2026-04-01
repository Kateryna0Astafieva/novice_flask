from flask.testing import FlaskClient


class FlaskLoginClient(FlaskClient):

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        fresh = kwargs.pop("fresh_login", True)

        super().__init__(*args, **kwargs)

        if user:
            with self.session_transaction() as sess:
                sess["_user_id"] = user.get_id()
                sess["_fresh"] = fresh
