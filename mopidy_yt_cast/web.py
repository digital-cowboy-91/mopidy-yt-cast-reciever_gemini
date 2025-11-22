import logging
import os
import tornado.web
import tornado.escape

logger = logging.getLogger(__name__)

class DeviceDescriptionHandler(tornado.web.RequestHandler):
    def initialize(self, config):
        self.friendly_name = config['yt_cast']['friendly_name']
        self.uuid = 'uuid:550e8400-e29b-41d4-a716-446655440000' # TODO: Generate or persist this

    def get(self):
        self.set_header('Content-Type', 'application/xml')
        # Minimal UPnP device description for DIAL
        xml = f"""<?xml version="1.0"?>
<root xmlns="urn:schemas-upnp-org:device-1-0">
  <specVersion>
    <major>1</major>
    <minor>0</minor>
  </specVersion>
  <device>
    <deviceType>urn:dial-multiscreen-org:device:dial:1</deviceType>
    <friendlyName>{self.friendly_name}</friendlyName>
    <manufacturer>Mopidy</manufacturer>
    <modelName>Mopidy YouTube Cast</modelName>
    <UDN>{self.uuid}</UDN>
    <serviceList>
      <service>
        <serviceType>urn:dial-multiscreen-org:service:dial:1</serviceType>
        <serviceId>urn:dial-multiscreen-org:serviceId:dial</serviceId>
        <controlURL>/ssdp/notfound</controlURL>
        <eventSubURL>/ssdp/notfound</eventSubURL>
        <SCPDURL>/ssdp/notfound</SCPDURL>
      </service>
    </serviceList>
  </device>
</root>
"""
        self.write(xml)

class YouTubeAppHandler(tornado.web.RequestHandler):
    def initialize(self, core):
        self.core = core

    def get(self):
        self.set_header('Content-Type', 'application/xml')
        # We can check if something is playing, but for now let's say it's stopped or running based on activity.
        # For simplicity, we'll just say it's stopped so they can launch it, or running if we are playing.
        # TODO: Check actual state.
        state = "stopped"
        
        xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<service xmlns="urn:dial-multiscreen-org:schemas:dial">
  <name>YouTube</name>
  <options allowStop="true"/>
  <state>{state}</state>
</service>
"""
        self.write(xml)

    def post(self):
        body = self.request.body.decode('utf-8')
        logger.info(f"Launch request body: {body}")
        
        # Body is usually "v=VIDEO_ID&..." or just "v=VIDEO_ID"
        # It's x-www-form-urlencoded usually, but sometimes just raw.
        # Let's parse it.
        args = tornado.escape.parse_qs_bytes(self.request.body)
        video_id = args.get(b'v', [b''])[0].decode('utf-8')
        
        if not video_id:
            # Sometimes it might be in the query string?
            video_id = self.get_argument('v', None)

        if video_id:
            logger.info(f"Launching YouTube video: {video_id}")
            uri = f"youtube:video:{video_id}"
            
            # Mopidy Core interactions should be done carefully.
            # We add to tracklist and play.
            self.core.tracklist.clear()
            self.core.tracklist.add(uris=[uri])
            self.core.playback.play()
            
            self.set_status(201)
            self.set_header('Location', f'{self.request.full_url()}/run')
        else:
            logger.warning("No video ID found in launch request")
            self.set_status(400)

    def delete(self):
        logger.info("Stopping YouTube playback")
        self.core.playback.stop()
        self.write("Stopped")

def get_app_factory(config, core):
    return [
        (r'/yt_cast/device-desc.xml', DeviceDescriptionHandler, {'config': config}),
        (r'/yt_cast/apps/YouTube', YouTubeAppHandler, {'core': core}),
        (r'/yt_cast/apps/YouTube/run', YouTubeAppHandler, {'core': core}), # Instance URL
    ]
