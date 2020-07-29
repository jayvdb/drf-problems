import sys

from pytest_djangoapp import configure_djangoapp_plugin
from pytest_djangoapp.configuration import Configuration

import pytest

from django.urls import include, path

settings = {
    'REST_FRAMEWORK': {
        'EXCEPTION_HANDLER': 'drf_problems.exceptions.exception_handler',
    },
}

pytest_plugins = configure_djangoapp_plugin(settings, app_name='drf_problems')


@pytest.fixture()
def rf():
    """RequestFactory instance"""
    from django.test.client import RequestFactory

    return RequestFactory()


@pytest.fixture
def view():
    from rest_framework.views import APIView

    class TestingView(APIView):
        pass

    return TestingView()


@pytest.fixture(scope="session")
def djangoapp_options():
    yield Configuration.get()[Configuration._prefix]


@pytest.fixture(scope="session")
def app_name(djangoapp_options):
    yield djangoapp_options[Configuration._KEY_APP]


@pytest.fixture(scope="session")
def fake_global_urlconf_module():
    def fake_module(name):
        module = type(sys)(name)
        sys.modules[name] = module
        return module

    name = '_urls'

    urlconf = sys.modules.get(name)
    if not urlconf:
        urlconf = fake_module(name)
        urlconf.urlpatterns = []

    yield urlconf


@pytest.fixture(scope="session")
def fake_global_urlpatterns(fake_global_urlconf_module):
    yield fake_global_urlconf_module.urlpatterns


@pytest.fixture()
def urlpatterns(settings, fake_global_urlconf_module):
    settings.update({
        'ROOT_URLCONF': fake_global_urlconf_module.__name__,
    })

    with settings:
        yield fake_global_urlconf_module.urlpatterns


@pytest.fixture()
def inject_app_urls(urlpatterns, app_name):
    urls_module = '{}.urls'.format(app_name)

    if any(urlpattern.urlconf_module.__name__ == urls_module for urlpattern in urlpatterns):
        return

    urlpatterns.append(path('', include(urls_module)))
