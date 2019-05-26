import logging

from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _
from rest_framework import exceptions
from rest_framework.reverse import reverse
from rest_framework.views import exception_handler as drf_exception_handler

logger = logging.getLogger('drf_problems')


def exception_handler(exc, context):
    # Convert Django exceptions (from DRF).
    if isinstance(exc, Http404):
        exc = exceptions.NotFound()
    elif isinstance(exc, PermissionDenied):
        exc = exceptions.PermissionDenied()
    elif not isinstance(exc, exceptions.APIException):
        # Fallback handler to convert remaining exceptions to API exception.
        logger.exception(exc)
        exc = exceptions.APIException(exc)

    response = drf_exception_handler(exc, context)

    response.content_type = 'application/problem+json'
    data = response.data

    problem_title = getattr(exc, 'title', exc.default_detail)
    problem_status = response.status_code
    problem_code = getattr(exc, 'code', exc.default_code)
    problem_type = reverse('drf_problems:error-documentation',
                           kwargs={'code': problem_code}, request=context['request'])
    if isinstance(data, dict):
        data['title'] = problem_title
        data['status'] = problem_status
        data['type'] = problem_type
    else:
        data = dict(errors=response.data, title=problem_title,
                    status=problem_status, type=problem_type)
    response.data = data

    return response


class InvalidVersionRequestedException(exceptions.NotAcceptable):
    default_code = 'invalid_version'
    default_detail = _('Invalid API version provided.')
    format_detail = _('Provided version "{request_version}" is invalid.')
    description = _(
        'Malformed or unsupported version string is provided with the request.')

    def __init__(self, request_version, detail=None, code=None):
        if detail is None:
            detail = force_text(self.format_detail).format(
                request_version=request_version)
        super(InvalidVersionRequestedException, self).__init__(detail, code)


class DeprecatedVersionUsedException(exceptions.PermissionDenied):
    default_code = 'deprecated_version'
    default_detail = _('Deprecated API version provided.')
    format_detail = _(
        'Minimum version supported is "{min_version}", but the request used "{request_version}"')
    description = _(
        'API only supports versions above the minimum requirement.')

    def __init__(self, request_version, min_version, detail=None, code=None):
        if detail is None:
            detail = force_text(self.format_detail).format(
                request_version=request_version, min_version=min_version)
        super(DeprecatedVersionUsedException, self).__init__(detail, code)