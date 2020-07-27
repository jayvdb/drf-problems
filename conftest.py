import sys

from pytest_djangoapp import configure_djangoapp_plugin
import pytest

from django.urls import include, path

settings = {
    'DEBUG': True,
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


def fake_module(name):
    module = type(sys)(name)
    sys.modules[name] = module
    return module


# Set up urlconf
urlconf = fake_module('urls')
urlpatterns = []
urlconf.urlpatterns = urlpatterns


@pytest.fixture()
def fake_urlconf(settings):
    settings.update({
        'ROOT_URLCONF': 'urls',
    })

    urlpatterns.append(path('', include('drf_problems.urls')))

    yield
