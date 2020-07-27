import should_be.all  # noqa

from rest_framework.exceptions import (
    APIException,
    ErrorDetail,
    NotAuthenticated,
    ValidationError,
)
from rest_framework.mixins import Response

from drf_problems.exceptions import exception_handler


def test_exception_handler_if_error_without_detail(template_context, fake_urlconf):
    data = {"data": "test"}
    exp = APIException(data)
    response = exception_handler(exp, template_context())

    response.data.should_include(["status", "title", "type"])

    response.data["status"].should_be(500)
    response.data["title"].should_be("A server error occurred.")
    response.data["type"].should_be("http://testserver/problems/error/")

    response.data.should_include(["data"])

    response.data["data"].should_be_a(ErrorDetail)
    str(response.data["data"]).should_be("test")
    response.data["data"].code.should_be("error")
    repr(response.data["data"]).should_be("ErrorDetail(string='test', code='error')")

    sorted(response.data.keys()).should_be(["data", "status", "title", "type"])

def test_exception_handler_if_error_is_list_of_string(template_context, fake_urlconf):
    exp = APIException(["testing error"])
    response = exception_handler(exp, template_context())

    response.data.should_include(["status", "title", "type"])

    response.data["status"].should_be(500)
    response.data["title"].should_be("A server error occurred.")
    response.data["type"].should_be("http://testserver/problems/error/")

    response.data.should_include(["errors"])

    response.data["errors"].should_be_a(list)
    len(response.data["errors"]).should_be(1)
    response.data["errors"][0].should_be_a(ErrorDetail)
    str(response.data["errors"][0]).should_be("testing error")
    response.data["errors"][0].code.should_be("error")
    repr(response.data["errors"][0]).should_be("ErrorDetail(string='testing error', code='error')")

    sorted(response.data.keys()).should_be(["errors", "status", "title", "type"])

def test_exception_handler_if_error_is_string(template_context, fake_urlconf):
    exp = APIException("testing error")
    response = exception_handler(exp, template_context())

    response.data.should_include(["status", "title", "type"])

    response.data["status"].should_be(500)
    response.data["title"].should_be("A server error occurred.")
    response.data["type"].should_be("http://testserver/problems/error/")

    response.data.should_include(["detail"])

    response.data["detail"].should_be("testing error")

    sorted(response.data.keys()).should_be(["detail", "status", "title", "type"])


def test_exception_handler_if_error_is_nested_dict(template_context, fake_urlconf):
    exp = ValidationError({"foo": {"bar": "testing error"}})
    response = exception_handler(exp, template_context())

    response.data.should_include(["status", "title", "type"])

    response.data["status"].should_be(400)
    response.data["title"].should_be("Invalid input.")
    response.data["type"].should_be("http://testserver/problems/invalid/")

    sorted(response.data.keys()).should_include(["foo"])

    response.data["foo"].should_be_a(dict)
    response.data["foo"].should_be({'bar': ErrorDetail(string="testing error", code="invalid")})
    response.data["foo"]["bar"].code.should_be("invalid")
    str(response.data["foo"]["bar"]).should_be("testing error")

    repr(response.data["foo"]).should_be("{'bar': ErrorDetail(string='testing error', code='invalid')}")
    str(response.data["foo"]).should_be(repr(response.data["foo"]))

    sorted(response.data.keys()).should_be(["foo", "status", "title", "type"])


def test_exception_handler_if_error_is_common(template_context, fake_urlconf):
    exp = APIException({"non_field_errors": "test"})
    response = exception_handler(exp, template_context())

    response.data.should_include(["status", "title", "type"])

    response.data["status"].should_be(500)
    response.data["title"].should_be("A server error occurred.")
    response.data["type"].should_be("http://testserver/problems/error/")

    response.data.should_include(["non_field_errors"])

    response.data["non_field_errors"].should_be("test")

    sorted(response.data.keys()).should_be(["non_field_errors", "status", "title", "type"])


def test_handle_exception_with_basic_exception_ok(rf, view, fake_urlconf):
    view.request = rf.get("")
    view.request.data = {}
    response = view.handle_exception(APIException("test"))
    assert isinstance(response, Response)

    response.data.should_include(["status", "title", "type"])

    response.data["status"].should_be(500)
    response.data["title"].should_be("A server error occurred.")
    response.data["type"].should_be("http://testserver/problems/error/")

    response.data.should_include(["detail"])

    response.data["detail"].should_be_a(ErrorDetail)
    response.data["detail"].should_be("test")
    response.data["detail"].code.should_be("error")

    sorted(response.data.keys()).should_be(["detail", "status", "title", "type"])


def test_handle_exception_with_not_auth_exception_ok(rf, view, fake_urlconf):
    view.request = rf.get("")
    view.request.data = {}
    response = view.handle_exception(NotAuthenticated("test"))
    assert isinstance(response, Response)
    assert response.status_code == 403

    response.data.should_include(["status", "title", "type"])

    response.data["status"].should_be(403)
    response.data["title"].should_be("Authentication credentials were not provided.")
    response.data["type"].should_be("http://testserver/problems/not_authenticated/")

    response.data.should_include(["detail"])

    response.data["detail"].should_be_a(ErrorDetail)
    response.data["detail"].should_be("test")
    response.data["detail"].code.should_be("not_authenticated")

    sorted(response.data.keys()).should_be(["detail", "status", "title", "type"])


def test_handle_exception_with_auth_headers_ok(mocker, rf, view, fake_urlconf):
    view.request = rf.get("")
    view.request.data = {}
    mocker.patch.object(view, "get_authenticate_header", return_value=True)
    response = view.handle_exception(NotAuthenticated("test"))
    assert response._headers["www-authenticate"] == (
        "WWW-Authenticate",
        "True",
    )

    response.data.should_include(["status", "title", "type"])

    response.data["status"].should_be(401)
    response.data["title"].should_be("Authentication credentials were not provided.")
    response.data["type"].should_be("http://testserver/problems/not_authenticated/")

    response.data.should_include(["detail"])

    response.data["detail"].should_be_a(ErrorDetail)
    response.data["detail"].should_be("test")
    response.data["detail"].code.should_be("not_authenticated")

    sorted(response.data.keys()).should_be(["detail", "status", "title", "type"])
