import time
import json
import unittest

from project.tests.base import BaseTestCase, ItemCRUDTestCase

class TestRegistration(BaseTestCase):
    def test_registration(self):
        response = self.register_user('joe', '123456')
        self.assertEqual(response.status_code, 201)

    def test_double_registration_fails(self):
        self.register_user('joe', '123456')
        response = self.register_user('joe', '123456')

        self.assertEqual(response.status_code, 409)

class TestLogin(BaseTestCase):
    def setUp(self):
        BaseTestCase.setUp(self)
        self.register_user('user', '123456')

    def test_registered_user_login(self):
        response = self.login_user('user', '123456')
        self.assertEqual(response.status_code, 201)

    def test_non_registered_user_login_fails(self):
        response = self.login_user('nonuser', '123456')
        self.assertEqual(response.status_code, 403)

class TestItemCreate(ItemCRUDTestCase):
    def setUp(self):
        ItemCRUDTestCase.setUp(self)

    def test_unauthorized_fails(self):
        with self.client:
            response = self.client.post('/item')
            self.assertEqual(response.status_code, 401)

    def test_json_returned(self):
        response = self.authorized_post('user1', '/item', dict(field='myitem'))
        self.assertTrue(response.content_type == 'application/json')

    def test_status_code_201_returned_on_success(self):
        response = self.authorized_post('user1', '/item', dict(field='myitem'))
        self.assertEqual(response.status_code, 201)

    def test_item_created(self):
        response = self.authorized_post('user1', '/item', dict(field='myitem'))
        item_id = json.loads(response.data.decode())['id']
        response = self.authorized_get('user1', '/item/' + item_id)
        data = json.loads(response.data.decode())

        self.assertTrue(data['field'] == 'myitem')

class TestItemReplace(ItemCRUDTestCase):
    user1_item1_id = None

    def setUp(self):
        ItemCRUDTestCase.setUp(self)
        self.user1_item1_id = self.create_item('user1', dict(field='field1'))

    def test_unauthorized_fails(self):
        with self.client:
            response = self.client.put('/item/' + self.user1_item1_id)
            self.assertEqual(response.status_code, 401)

    def test_json_returned(self):
        response = self.authorized_put('user1', '/item/' + self.user1_item1_id, dict(field='myitem'))
        self.assertTrue(response.content_type == 'application/json')

    def test_status_code_204_returned_on_success(self):
        response = self.authorized_put('user1', '/item/' + self.user1_item1_id, dict(field='myitem'))
        self.assertEqual(response.status_code, 204)

    def test_forbidden_if_not_owner(self):
        response = self.authorized_put('user2', '/item/' + self.user1_item1_id, dict(field='myitem'))
        self.assertEqual(response.status_code, 403)

    def test_item_replaced(self):
        self.authorized_put('user1', '/item/' + self.user1_item1_id, dict(field='new_value'))
        response = self.authorized_get('user1', '/item/' + self.user1_item1_id)
        data = json.loads(response.data.decode())

        self.assertTrue(data['field'] == 'new_value')

class TestItemDelete(ItemCRUDTestCase):
    user1_item1_id = None

    def setUp(self):
        ItemCRUDTestCase.setUp(self)
        self.user1_item1_id = self.create_item('user1', dict(field='field1'))

    def test_unauthorized_fails(self):
        with self.client:
            response = self.client.delete('/item/' + self.user1_item1_id)
            self.assertEqual(response.status_code, 401)

    def test_json_returned(self):
        response = self.authorized_delete('user1', '/item/' + self.user1_item1_id)
        self.assertTrue(response.content_type == 'application/json')

    def test_status_code_204_returned_on_success(self):
        response = self.authorized_delete('user1', '/item/' + self.user1_item1_id)
        self.assertEqual(response.status_code, 204)

    def test_forbidden_if_not_owner(self):
        response = self.authorized_delete('user2', '/item/' + self.user1_item1_id)
        self.assertEqual(response.status_code, 403)

    def test_item_deleted(self):
        self.authorized_delete('user1', '/item/' + self.user1_item1_id)
        response = self.authorized_get('user1', '/item/' + self.user1_item1_id)

        self.assertEqual(response.status_code, 404)

class TestItemGetSingle(ItemCRUDTestCase):
    user1_item1_id = None
    user2_item1_id = None

    def setUp(self):
        ItemCRUDTestCase.setUp(self)
        self.user1_item1_id = self.create_item('user1', dict(field='field1'))
        self.user2_item1_id = self.create_item('user2', dict(field='other'))

    def test_unauthorized_fails(self):
        with self.client:
            response = self.client.get('/item/' + self.user1_item1_id)
            self.assertEqual(response.status_code, 401)

    def test_json_returned(self):
        response = self.authorized_get('user1', '/item/' + self.user1_item1_id)
        self.assertTrue(response.content_type == 'application/json')

    def test_status_code_200_returned_on_success(self):
        response = self.authorized_get('user1', '/item/' + self.user1_item1_id)
        self.assertEqual(response.status_code, 200)

    def test_own_item_returned(self):
        response = self.authorized_get('user1', '/item/' + self.user1_item1_id)
        data = json.loads(response.data.decode())

        self.assertTrue(data['field'] == 'field1')

    def test_other_user_item_returned(self):
        response = self.authorized_get('user1', '/item/' + self.user2_item1_id)
        data = json.loads(response.data.decode())

        self.assertTrue(data['field'] == 'other')

class TestItemSearch(ItemCRUDTestCase):
    user1_item1_id = None
    user1_item2_id = None
    user2_item1_id = None

    def setUp(self):
        ItemCRUDTestCase.setUp(self)

        self.user1_item1_id = self.create_item('user1', dict(field='field1'))
        self.user1_item2_id = self.create_item('user1', dict(field='field2'))
        self.user2_item1_id = self.create_item('user2', dict(field='other'))

    def has_dict(self, a, d):
        dict_compare = lambda d1, d2: len(set(d1.items()) ^ set(d2.items())) == 0
        return any([dict_compare(d, ad) for ad in a])

    def test_unauthorized_fails(self):
        with self.client:
            response = self.client.get('/item')
            self.assertEqual(response.status_code, 401)

    def test_json_returned(self):
        response = self.authorized_get('user1', '/item')
        self.assertTrue(response.content_type == 'application/json')

    def test_status_code_200_returned_on_success(self):
        response = self.authorized_get('user1', '/item')
        self.assertEqual(response.status_code, 200)

    def test_own_items_returned(self):
        response = self.authorized_get('user1', '/item')
        data = json.loads(response.data.decode())

        self.assertTrue(self.has_dict(data, dict(field='field1')))
        self.assertTrue(self.has_dict(data, dict(field='field2')))

    def test_other_user_items_returned(self):
        response = self.authorized_get('user1', '/item')
        data = json.loads(response.data.decode())

        self.assertTrue(self.has_dict(data, dict(field='other')))

    def test_items_filtered_by_owner_returned(self):
        response = self.authorized_get('user1', '/item', dict(owner='user1'))
        data = json.loads(response.data.decode())

        self.assertTrue(len(data) == 2)

class TestTransferCreate(ItemCRUDTestCase):
    user1_item1_id = None

    def setUp(self):
        ItemCRUDTestCase.setUp(self)
        self.user1_item1_id = self.create_item('user1', dict(field='field1'))

    def test_unauthorized_fails(self):
        with self.client:
            response = self.client.post('/item/' + self.user1_item1_id + '/transfer')
            self.assertEqual(response.status_code, 401)

    def test_json_returned(self):
        response = self.authorized_post('user1', '/item/' + self.user1_item1_id + '/transfer')
        self.assertTrue(response.content_type == 'application/json')

    def test_status_code_201_returned_on_success(self):
        response = self.authorized_post('user1', '/item/' + self.user1_item1_id + '/transfer', dict(to='user2'))
        self.assertEqual(response.status_code, 201)

class TestTransferClaim(ItemCRUDTestCase):
    user1_item1_id = None
    user1_item2_id = None

    def setUp(self):
        ItemCRUDTestCase.setUp(self)

        self.user1_item1_id = self.create_item('user1', dict(field='field1'))
        self.user1_item2_id = self.create_item('user1', dict(field='field2'))

        self.authorized_post('user1', '/item/' + self.user1_item1_id + '/transfer', dict(to='user2'))

    def test_unauthorized_fails(self):
        with self.client:
            response = self.client.post('/item/' + self.user1_item1_id + '/transfer/claim')
            self.assertEqual(response.status_code, 401)

    def test_json_returned(self):
        response = self.authorized_post('user1', '/item/' + self.user1_item1_id + '/transfer/claim')
        self.assertTrue(response.content_type == 'application/json')

    def test_status_code_204_returned_on_success(self):
        response = self.authorized_post('user2', '/item/' + self.user1_item1_id + '/transfer/claim')
        self.assertEqual(response.status_code, 204)

    def test_ownership_moved(self):
        self.authorized_post('user2', '/item/' + self.user1_item1_id + '/transfer/claim')

        response = self.authorized_get('user1', '/item', dict(owner='user1'))
        self.assertTrue(len(json.loads(response.data.decode())) == 1)

        response = self.authorized_get('user1', '/item', dict(owner='user2'))
        self.assertTrue(len(json.loads(response.data.decode())) == 1)

if __name__ == '__main__':
    unittest.main()
