import unittest
from django.test import Client, TestCase


class TestExample(unittest.TestCase):
    """Демонстрирует принцип работы тестов"""
    @classmethod
    def setUpClass(cls):        
        print('setUpClass выполнен')

    @classmethod
    def tearDownClass(cls):
        print('tearDownClass выполнен')

    def setUp(self):
        print('setUp выполнен')

    def test_one(self): 
        print('Первый тест выполнен')

    def test_two(self): 
        print('Второй тест выполнен')


if __name__ == '__main__':
    unittest.main() 


something = 'sfhg'
def test_unexisting_page_correct_status():
    """Страница по адресу 'unexisting_page' вернёт ошибку 404."""
    response = self.guest_client.get('/unexisting_page/').status_code
    self.assertEqual(something, str)