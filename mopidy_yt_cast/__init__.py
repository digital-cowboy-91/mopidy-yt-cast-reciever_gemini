import logging
import pathlib
import pkg_resources

from mopidy import config, ext

__version__ = '0.1.0'

logger = logging.getLogger(__name__)

class Extension(ext.Extension):

    dist_name = 'Mopidy-Yt-Cast'
    ext_name = 'yt_cast'
    version = __version__

    def get_default_config(self):
        return config.read(pathlib.Path(__file__).parent / 'ext.conf')

    def get_config_schema(self):
        schema = super().get_config_schema()
        schema['friendly_name'] = config.String()
        return schema

    def setup(self, registry):
        from .frontend import YtCastFrontend
        registry.add('frontend', YtCastFrontend)

        from .web import get_app_factory
        registry.add('http:app', {
            'name': 'yt_cast',
            'factory': get_app_factory,
        })
