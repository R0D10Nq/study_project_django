"""
Тесты для утилит проекта
"""
import os
import unittest
from django.test import TestCase
from django.core.cache import cache
from core.utils.landing_utils import make_host_key, get_current_host
from core.utils.html_utils import prettify_html, get_module_name
from core.utils.cache_utils import hash_string
from core.utils.file_utils import file_get_contents, convert_size

class LandingUtilsTest(TestCase):
    """Тесты для landing_utils"""
    
    def test_make_host_key(self):
        """Тест функции make_host_key"""
        self.assertEqual(make_host_key("example.com"), "example__com")
        self.assertEqual(make_host_key("sub-domain.example.com"), "sub_domain.example__com")
    
    def test_get_current_host_with_landing(self):
        """Тест функции get_current_host с лендингом"""
        # Mock Landing объект
        class MockLanding:
            domain = "test.com"
        
        landing = MockLanding()
        self.assertEqual(get_current_host(landing, raw=True), "test.com")
        self.assertEqual(get_current_host(landing), "test__com")


class HtmlUtilsTest(TestCase):
    """Тесты для html_utils"""
    
    def test_prettify_html(self):
        """Тест функции prettify_html"""
        html = "<div><p>Test</p></div>"
        pretty_html = prettify_html(html)
        self.assertIn("<div>", pretty_html)
        self.assertIn("<p>", pretty_html)
        self.assertIn("Test", pretty_html)
    
    def test_get_module_name(self):
        """Тест функции get_module_name"""
        self.assertEqual(get_module_name("m-test"), "m-test")
        self.assertEqual(get_module_name("modules/m-test"), "m-test")
        self.assertEqual(get_module_name("modules\\m-test"), "m-test")


class CacheUtilsTest(TestCase):
    """Тесты для cache_utils"""
    
    def test_hash_string(self):
        """Тест функции hash_string"""
        self.assertEqual(hash_string("test"), "098f6bcd4621d373cade4e832627b4f6")
        self.assertEqual(hash_string(""), "")


class FileUtilsTest(TestCase):
    """Тесты для file_utils"""
    
    def test_convert_size(self):
        """Тест функции convert_size"""
        self.assertEqual(convert_size(0), "0B")
        self.assertEqual(convert_size(1024), "1.0 KB")
        self.assertEqual(convert_size(1048576), "1.0 MB")
        self.assertEqual(convert_size(1073741824), "1.0 GB")
    
    def test_file_get_contents(self):
        """Тест функции file_get_contents"""
        # Создаем временный файл
        with open("test_file.txt", "w") as f:
            f.write("test content")
        
        # Проверяем чтение файла
        self.assertEqual(file_get_contents("test_file.txt"), "test content")
        
        # Удаляем временный файл
        os.remove("test_file.txt")
        
        # Проверяем чтение несуществующего файла
        self.assertEqual(file_get_contents("non_existent_file.txt"), "")
