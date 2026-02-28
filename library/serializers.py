import markdown
import nh3
from rest_framework import serializers

from library.models import MdLibrary


class MdLibraryMetaSerializer(serializers.ModelSerializer):
    class Meta:
        model = MdLibrary
        fields = ['id', 'file_name', 'file_version', 'deleted', 'created_at', 'updated_at']


class MdLibraryDetailSerializer(serializers.ModelSerializer):
    rendered_html = serializers.SerializerMethodField()

    def get_rendered_html(self, obj):
        md = markdown.Markdown(
            extensions=['fenced_code', 'codehilite', 'tables', 'nl2br'],
            extension_configs={'codehilite': {'css_class': 'highlight', 'guess_lang': False}},
        )
        md.preprocessors.deregister('html_block')
        rendered = md.convert(obj.file_contents)
        md.reset()
        return nh3.clean(
            rendered,
            tags={
                'a', 'abbr', 'b', 'blockquote', 'br', 'code', 'del', 'div', 'em',
                'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'hr', 'i', 'img', 'li', 'ol',
                'p', 'pre', 'span', 'strong', 'table', 'tbody', 'td', 'th', 'thead', 'tr', 'ul',
            },
            attributes={
                'a':   {'href', 'title'},
                'img': {'src', 'alt', 'title'},
                '*':   {'class'},
            },
            url_schemes={'http', 'https'},
            strip_comments=True,
        )

    class Meta:
        model = MdLibrary
        fields = [
            'id', 'file_name', 'file_version', 'file_contents',
            'rendered_html', 'deleted', 'created_at', 'updated_at',
        ]
