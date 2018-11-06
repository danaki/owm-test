import json
from flask_testing import TestCase
from project.server import app, db

class BaseTestCase(TestCase):
    def create_app(self):
        app.config.from_object('project.server.config.TestingConfig')
        return app

    def setUp(self):
        pass

    def tearDown(self):
        db.user.delete_many({})
        db.item.delete_many({})

    def register_user(self, username, password):
        return self.client.post(
            '/auth/register',
            data=json.dumps(dict(
                username=username,
                password=password
            )),
            content_type='application/json',
        )

    def login_user(self, username, password):
        return self.client.post(
            '/auth/login',
            data=json.dumps(dict(
                username=username,
                password=password
            )),
            content_type='application/json',
        )

class ItemCRUDTestCase(BaseTestCase):
    tokens = {}

    def setUp(self):
        BaseTestCase.setUp(self)

        self.tokens = dict(
            user1=self.register_and_login('user1', '123456'),
            user2=self.register_and_login('user2', '123456')
        )

    def register_and_login(self, username, password):
        with self.client:
            self.register_user(username, password)
            response = self.login_user(username, password)

            return json.loads(
                response.data.decode()
            )['auth_token']

    def authorized_any(self, method, username, *args, **kwargs):
        kwargs.update(dict(
            headers=dict(
                Authorization='Bearer ' + self.tokens[username]
            )
        ))

        with self.client:
            return getattr(self.client, method)(*args, **kwargs)

    def authorized_get(self, username, url, data={}):
        return self.authorized_any('get', username, url, query_string=data)

    def authorized_post(self, username, url, data={}):
        return self.authorized_any(
            'post',
            username,
            url,
            json=data
        )

    def authorized_put(self, username, url, data={}):
        return self.authorized_any(
            'put',
            username,
            url,
            json=data
        )

    def authorized_delete(self, username, url):
        return self.authorized_any(
            'delete',
            username,
            url
        )

    def create_item(self, username, data):
        response = self.authorized_post(username, '/item', data)

        return json.loads(response.data.decode())['id']
