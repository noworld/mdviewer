import logging
import re

from django.conf import settings
from rest_framework.exceptions import Throttled
from rest_framework.response import Response
from rest_framework.views import APIView

from library.models import MdLibrary
from library.serializers import MdLibraryDetailSerializer, MdLibraryMetaSerializer
from library.throttles import (
    LibraryClearThrottle,
    LibraryCreateThrottle,
    LibraryDeleteThrottle,
    LibraryDetailThrottle,
    LibraryListThrottle,
    LibraryStatsThrottle,
    LibraryUpdateThrottle,
)

logger = logging.getLogger('library')

FILE_NAME_RE = re.compile(r'^[A-Za-z0-9\-_.]+$')


class LibraryBaseView(APIView):
    """Base view that formats throttle violations per the API response schema."""

    def handle_exception(self, exc):
        if isinstance(exc, Throttled):
            client_ip = self.request.META.get('REMOTE_ADDR', 'unknown')
            logger.warning(
                'Rate limit exceeded: endpoint=%s, ip=%s',
                self.request.path,
                client_ip,
            )
            return Response(
                {
                    'status': 'RATE_LIMITED',
                    'error': 'Request rate limit exceeded. Please wait before retrying.',
                },
                status=429,
            )
        return super().handle_exception(exc)


class LibraryListCreateView(LibraryBaseView):

    def get_throttles(self):
        if self.request.method == 'POST':
            return [LibraryCreateThrottle()]
        return [LibraryListThrottle()]

    def get(self, request):
        try:
            qs = MdLibrary.objects.all()

            if 'file_name' in request.query_params:
                file_name = request.query_params['file_name']
                if not file_name:
                    logger.warning('Validation failure: file_name')
                    return Response(
                        {'status': 'MISSING_PARAMETER', 'error': 'file_name must not be blank.'},
                        status=400,
                    )
                qs = qs.filter(file_name__icontains=file_name)

            if 'deleted' in request.query_params:
                deleted_param = request.query_params['deleted'].lower()
                if deleted_param == 'true':
                    qs = qs.filter(deleted=True)
                elif deleted_param == 'false':
                    qs = qs.filter(deleted=False)

            qs = qs.order_by('file_name', '-file_version')
            serializer = MdLibraryMetaSerializer(qs, many=True)
            data = serializer.data
            return Response({'status': 'SUCCESS', 'count': len(data), 'results': data})
        except Exception:
            logger.exception('Unhandled exception in LibraryListCreateView.get')
            return Response(
                {'status': 'FAILURE', 'error': 'An internal server error occurred.'},
                status=500,
            )

    def post(self, request):
        try:
            # Validate file_name
            file_name = request.data.get('file_name')
            if not file_name or not isinstance(file_name, str):
                logger.warning('Validation failure: file_name')
                return Response(
                    {'status': 'MISSING_PARAMETER', 'error': 'file_name is required and must not be blank.'},
                    status=400,
                )
            if len(file_name) > 255 or not FILE_NAME_RE.match(file_name):
                logger.warning('Validation failure: file_name')
                return Response(
                    {
                        'status': 'MISSING_PARAMETER',
                        'error': (
                            'file_name must be 255 characters or fewer and contain only '
                            'alphanumeric characters, hyphens, underscores, or dots.'
                        ),
                    },
                    status=400,
                )

            # Validate file_contents
            file_contents = request.data.get('file_contents')
            if not isinstance(file_contents, str) or not file_contents.strip():
                logger.warning('Validation failure: file_contents')
                return Response(
                    {'status': 'MISSING_PARAMETER', 'error': 'file_contents is required and must not be blank.'},
                    status=400,
                )
            max_bytes = settings.YAML_CONFIG['max_upload_bytes']
            if len(file_contents.encode('utf-8')) > max_bytes:
                logger.warning('Validation failure: file_contents')
                return Response(
                    {
                        'status': 'MISSING_PARAMETER',
                        'error': f'file_contents exceeds the maximum allowed size of {max_bytes} bytes.',
                    },
                    status=400,
                )

            # Determine file_version — include deleted records to avoid UNIQUE constraint violations
            existing = (
                MdLibrary.objects.filter(file_name=file_name)
                .order_by('-file_version')
                .first()
            )
            file_version = (existing.file_version + 1) if existing else 1

            record = MdLibrary.objects.create(
                file_name=file_name,
                file_version=file_version,
                file_contents=file_contents,
            )
            logger.info('File uploaded: file_name=%s, file_version=%d', file_name, file_version)

            serializer = MdLibraryMetaSerializer(record)
            response = Response({'status': 'SUCCESS', 'result': serializer.data}, status=201)
            response['Location'] = f'/api/v1/library/{record.id}/'
            return response
        except Exception:
            logger.exception('Unhandled exception in LibraryListCreateView.post')
            return Response(
                {'status': 'FAILURE', 'error': 'An internal server error occurred.'},
                status=500,
            )


class LibraryDetailView(LibraryBaseView):

    def get_throttles(self):
        if self.request.method == 'PATCH':
            return [LibraryUpdateThrottle()]
        if self.request.method == 'DELETE':
            return [LibraryDeleteThrottle()]
        return [LibraryDetailThrottle()]

    def get(self, request, pk):
        try:
            try:
                record = MdLibrary.objects.get(pk=pk)
            except MdLibrary.DoesNotExist:
                return Response(
                    {'status': 'NO_RESULTS', 'error': 'Record not found.'},
                    status=404,
                )
            serializer = MdLibraryDetailSerializer(record)
            return Response({'status': 'SUCCESS', 'result': serializer.data})
        except Exception:
            logger.exception('Unhandled exception in LibraryDetailView.get')
            return Response(
                {'status': 'FAILURE', 'error': 'An internal server error occurred.'},
                status=500,
            )

    def patch(self, request, pk):
        try:
            try:
                record = MdLibrary.objects.get(pk=pk)
            except MdLibrary.DoesNotExist:
                return Response(
                    {'status': 'NO_RESULTS', 'error': 'Record not found.'},
                    status=404,
                )

            has_file_contents = 'file_contents' in request.data
            has_deleted = 'deleted' in request.data
            if not has_file_contents and not has_deleted:
                logger.warning('Validation failure: file_contents or deleted')
                return Response(
                    {
                        'status': 'MISSING_PARAMETER',
                        'error': 'At least one of file_contents or deleted is required.',
                    },
                    status=400,
                )

            if has_file_contents:
                file_contents = request.data['file_contents']
                if not isinstance(file_contents, str) or not file_contents.strip():
                    logger.warning('Validation failure: file_contents')
                    return Response(
                        {'status': 'MISSING_PARAMETER', 'error': 'file_contents must not be blank.'},
                        status=400,
                    )
                max_bytes = settings.YAML_CONFIG['max_upload_bytes']
                if len(file_contents.encode('utf-8')) > max_bytes:
                    logger.warning('Validation failure: file_contents')
                    return Response(
                        {
                            'status': 'MISSING_PARAMETER',
                            'error': f'file_contents exceeds the maximum allowed size of {max_bytes} bytes.',
                        },
                        status=400,
                    )
                record.file_contents = file_contents

            if has_deleted:
                deleted_value = request.data['deleted']
                if not isinstance(deleted_value, bool):
                    logger.warning('Validation failure: deleted')
                    return Response(
                        {'status': 'MISSING_PARAMETER', 'error': 'deleted must be a boolean.'},
                        status=400,
                    )
                record.deleted = deleted_value

            record.save()
            serializer = MdLibraryMetaSerializer(record)
            return Response({'status': 'SUCCESS', 'result': serializer.data})
        except Exception:
            logger.exception('Unhandled exception in LibraryDetailView.patch')
            return Response(
                {'status': 'FAILURE', 'error': 'An internal server error occurred.'},
                status=500,
            )

    def delete(self, request, pk):
        try:
            try:
                record = MdLibrary.objects.get(pk=pk)
            except MdLibrary.DoesNotExist:
                return Response(
                    {'status': 'NO_RESULTS', 'error': 'Record not found.'},
                    status=404,
                )
            record.deleted = True
            record.save()
            return Response(status=204)
        except Exception:
            logger.exception('Unhandled exception in LibraryDetailView.delete')
            return Response(
                {'status': 'FAILURE', 'error': 'An internal server error occurred.'},
                status=500,
            )


class LibraryClearView(LibraryBaseView):
    throttle_classes = [LibraryClearThrottle]

    def delete(self, request):
        try:
            deleted_count, _ = MdLibrary.objects.all().delete()
            logger.info('Database cleared: %d record(s) permanently deleted', deleted_count)
            return Response(status=204)
        except Exception:
            logger.exception('Unhandled exception in LibraryClearView.delete')
            return Response(
                {'status': 'FAILURE', 'error': 'An internal server error occurred.'},
                status=500,
            )


class LibraryStatsView(LibraryBaseView):
    throttle_classes = [LibraryStatsThrottle]

    def get(self, request):
        try:
            active_files = (
                MdLibrary.objects.filter(deleted=False)
                .values('file_name')
                .distinct()
                .count()
            )
            total_records = MdLibrary.objects.count()
            deleted_records = MdLibrary.objects.filter(deleted=True).count()
            return Response({
                'status': 'SUCCESS',
                'active_files': active_files,
                'total_records': total_records,
                'deleted_records': deleted_records,
            })
        except Exception:
            logger.exception('Unhandled exception in LibraryStatsView.get')
            return Response(
                {'status': 'FAILURE', 'error': 'An internal server error occurred.'},
                status=500,
            )
