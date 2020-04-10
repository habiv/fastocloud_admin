import json
import os
from abc import ABC, abstractmethod
from datetime import datetime
from enum import IntEnum
from urllib.parse import urlparse

import pyfastocloud_models.constants as constants
from pyfastocloud_models.common_entries import InputUrl, OutputUrl
from pyfastocloud_models.service.entry import ServiceSettings
from pyfastocloud_models.stream.entry import IStream, ProxyStream, HardwareStream, RelayStream, EncodeStream, \
    TimeshiftRecorderStream, CatchupStream, TimeshiftPlayerStream, TestLifeStream, CodRelayStream, CodEncodeStream, \
    ProxyVodStream, VodRelayStream, VodEncodeStream, EventStream

from app.service.service_client import ServiceClient


class ConfigFields:
    ID_FIELD = 'id'
    TYPE_FIELD = 'type'
    FEEDBACK_DIR_FIELD = 'feedback_directory'
    LOG_LEVEL_FIELD = 'log_level'
    INPUT_FIELD = 'input'
    OUTPUT_FIELD = 'output'
    AUDIO_SELECT_FIELD = 'audio_select'
    HAVE_VIDEO_FIELD = 'have_video'
    HAVE_AUDIO_FIELD = 'have_audio'
    LOOP_FIELD = 'loop'
    AUTO_EXIT_TIME_FIELD = 'auto_exit_time'
    RESTART_ATTEMPTS_FIELD = 'restart_attempts'

    # encode
    RELAY_VIDEO_FIELD = 'relay_video'
    RELAY_AUDIO_FIELD = 'relay_audio'
    DEINTERLACE_FIELD = 'deinterlace'
    FRAME_RATE_FIELD = 'framerate'
    VOLUME_FIELD = 'volume'
    VIDEO_CODEC_FIELD = 'video_codec'
    AUDIO_CODEC_FIELD = 'audio_codec'
    AUDIO_CHANNELS_COUNT_FIELD = 'audio_channels'
    SIZE_FIELD = 'size'
    VIDEO_BIT_RATE_FIELD = 'video_bitrate'
    AUDIO_BIT_RATE_FIELD = 'audio_bitrate'
    LOGO_FIELD = 'logo'
    RSVG_LOGO_FIELD = 'rsvg_logo'
    ASPCET_RATIO_FIELD = 'aspect_ratio'
    # relay
    VIDEO_PARSER_FIELD = 'video_parser'
    AUDIO_PARSER_FIELD = 'audio_parser'
    # timeshift recorder
    TIMESHIFT_CHUNK_DURATION = 'timeshift_chunk_duration'
    TIMESHIFT_CHUNK_LIFE_TIME = 'timeshift_chunk_life_time'
    TIMESHIFT_DIR = 'timeshift_dir'
    # timeshift player
    TIMESHIFT_DELAY = 'timeshift_delay'
    # vods
    VODS_CLEANUP_TS = 'cleanup_ts'


class StreamStatus(IntEnum):
    NEW = 0
    INIT = 1
    STARTED = 2
    READY = 3
    PLAYING = 4
    FROZEN = 5
    WAITING = 6


class IStreamObject(ABC):
    DEFAULT_STREAM_NAME = 'Stream'

    _stream = None
    _settings = None

    def __init__(self, stream: IStream, settings: ServiceSettings):
        self._stream = stream
        self._settings = settings

    @abstractmethod
    def get_log_request(self, host, port):
        pass

    @abstractmethod
    def get_pipeline_request(self, host, port):
        pass

    @abstractmethod
    def start_request(self):
        pass

    @abstractmethod
    def stop_request(self):
        pass

    @abstractmethod
    def restart_request(self):
        pass

    def stream(self) -> IStream:
        return self._stream

    @property
    def id(self):
        return self._stream.id

    @property
    def type(self) -> constants.StreamType:
        return self._stream.get_type()

    def get_id(self) -> str:
        stream = self.stream()
        return stream.get_id()

    def is_started(self) -> bool:
        return True

    def output_dict(self) -> list:
        result = []
        for out in self._stream.output:
            out_dict = out.to_front_dict()
            result.append(out_dict)

        return result

    def to_front_dict(self) -> dict:
        return self._stream.to_front_dict()

    def config(self) -> dict:
        return {
            ConfigFields.ID_FIELD: self.get_id(),  # required
            ConfigFields.TYPE_FIELD: self._stream.get_type(),  # required
            ConfigFields.OUTPUT_FIELD: self.output_dict()  # required empty in timeshift_record
        }

    def reset(self):
        return

    def update_runtime_fields(self, params: dict):
        assert self._stream.get_id() == params[IStream.ID_FIELD]
        assert self._stream.get_type() == params[IStream.TYPE_FIELD]

    def stable(self, *args, **kwargs):
        pass


class ProxyStreamObject(IStreamObject):
    def get_log_request(self, host, port):
        pass

    def get_pipeline_request(self, host, port):
        pass

    def start_request(self):
        pass

    def stop_request(self):
        pass

    def restart_request(self):
        pass

    def __init__(self, stream: ProxyStream, settings: ServiceSettings):
        super(ProxyStreamObject, self).__init__(stream, settings)

    @classmethod
    def make_stream(cls, settings):
        proxy = ProxyStream(name=IStreamObject.DEFAULT_STREAM_NAME)
        proxy.output = [OutputUrl(id=OutputUrl.generate_id())]
        return cls(proxy, settings)


class HardwareStreamObject(IStreamObject):
    INPUT_STREAMS_FIELD = 'input_streams'
    OUTPUT_STREAMS_FIELD = 'output_streams'
    LOOP_START_TIME_FIELD = 'loop_start_time'
    RSS_FIELD = 'rss'
    CPU_FIELD = 'cpu'
    STATUS_FIELD = 'status'
    RESTARTS_FIELD = 'restarts'
    START_TIME_FIELD = 'start_time'
    TIMESTAMP_FIELD = 'timestamp'
    IDLE_TIME_FIELD = 'idle_time'
    QUALITY_FIELD = 'quality'

    # runtime
    _status = StreamStatus.NEW
    _cpu = 0.0
    _timestamp = 0
    _idle_time = 0
    _rss = 0
    _loop_start_time = 0
    _restarts = 0
    _start_time = 0
    _input_streams = []
    _output_streams = []
    _client = None

    def __init__(self, stream: HardwareStream, settings: ServiceSettings, client: ServiceClient):
        super(HardwareStreamObject, self).__init__(stream, settings)
        self._client = client

    def get_log_request(self, host, port):
        self._client.get_log_stream(host, port, self.get_id(), self.generate_feedback_dir())

    def get_pipeline_request(self, host, port):
        self._client.get_pipeline_stream(host, port, self.get_id(), self.generate_feedback_dir())

    def start_request(self):
        if not self.is_started():
            self._client.start_stream(self.config())

    def stop_request(self):
        if self.is_started():
            self._client.stop_stream(self.get_id())

    def restart_request(self):
        if self.is_started():
            self._client.restart_stream(self.get_id())

    def generate_feedback_dir(self):
        return '{0}/{1}/{2}'.format(self._settings.feedback_directory, self.type, self.get_id())

    def input_dict(self) -> list:
        result = []
        for inp in self._stream.input:
            out_dict = inp.to_front_dict()
            result.append(out_dict)

        return result

    def is_started(self) -> bool:
        return self._start_time != 0

    def reset(self):
        self._status = StreamStatus.NEW
        self._cpu = 0.0
        self._timestamp = 0
        self._idle_time = 0
        self._rss = 0
        self._loop_start_time = 0
        self._restarts = 0
        self._start_time = 0
        self._input_streams = []
        self._output_streams = []

    def update_runtime_fields(self, params: dict):
        super(HardwareStreamObject, self).update_runtime_fields(params)
        self._status = StreamStatus(params[HardwareStreamObject.STATUS_FIELD])
        self._cpu = params[HardwareStreamObject.CPU_FIELD]
        self._timestamp = params[HardwareStreamObject.TIMESTAMP_FIELD]
        self._idle_time = params[HardwareStreamObject.IDLE_TIME_FIELD]
        self._rss = params[HardwareStreamObject.RSS_FIELD]
        self._loop_start_time = params[HardwareStreamObject.LOOP_START_TIME_FIELD]
        self._restarts = params[HardwareStreamObject.RESTARTS_FIELD]
        self._start_time = params[HardwareStreamObject.START_TIME_FIELD]
        self._input_streams = params[HardwareStreamObject.INPUT_STREAMS_FIELD]
        self._output_streams = params[HardwareStreamObject.OUTPUT_STREAMS_FIELD]

    def to_front_dict(self) -> dict:
        front = super(HardwareStreamObject, self).to_front_dict()
        front[HardwareStreamObject.STATUS_FIELD] = self._status
        front[HardwareStreamObject.CPU_FIELD] = self._cpu
        front[HardwareStreamObject.TIMESTAMP_FIELD] = self._timestamp
        front[HardwareStreamObject.IDLE_TIME_FIELD] = self._idle_time
        front[HardwareStreamObject.RSS_FIELD] = self._rss
        front[HardwareStreamObject.LOOP_START_TIME_FIELD] = self._loop_start_time
        front[HardwareStreamObject.RESTARTS_FIELD] = self._restarts
        front[HardwareStreamObject.START_TIME_FIELD] = self._start_time
        front[HardwareStreamObject.INPUT_STREAMS_FIELD] = self._input_streams
        front[HardwareStreamObject.OUTPUT_STREAMS_FIELD] = self._output_streams
        # runtime
        work_time = self._timestamp - self._start_time
        quality = 100 - (100 * self._idle_time / work_time) if work_time else 100
        front[HardwareStreamObject.QUALITY_FIELD] = quality
        return front

    def config(self) -> dict:
        conf = super(HardwareStreamObject, self).config()
        conf[ConfigFields.FEEDBACK_DIR_FIELD] = self.generate_feedback_dir()
        conf[ConfigFields.LOG_LEVEL_FIELD] = self._stream.get_log_level()
        conf[ConfigFields.AUTO_EXIT_TIME_FIELD] = self._stream.get_auto_exit_time()
        conf[ConfigFields.LOOP_FIELD] = self._stream.get_loop()
        conf[ConfigFields.HAVE_VIDEO_FIELD] = self._stream.get_have_video()  # required
        conf[ConfigFields.HAVE_AUDIO_FIELD] = self._stream.get_have_audio()  # required
        conf[ConfigFields.RESTART_ATTEMPTS_FIELD] = self._stream.get_restart_attempts()
        conf[ConfigFields.INPUT_FIELD] = self.input_dict()  # required empty in timeshift_player

        audio_select = self._stream.get_audio_select()
        if audio_select != constants.INVALID_AUDIO_SELECT:
            conf[ConfigFields.AUDIO_SELECT_FIELD] = audio_select

        try:
            args = json.loads(self._stream.extra_config_fields)
            for key, value in args.items():
                conf[key] = value
        except:
            pass

        return conf

    def generate_http_link(self, hls_type: constants.HlsType,
                           playlist_name=constants.DEFAULT_HLS_PLAYLIST, oid=OutputUrl.generate_id()) -> OutputUrl:
        http_root = self._generate_http_root_dir(oid)
        link = '{0}/{1}'.format(http_root, playlist_name)
        return OutputUrl(id=oid, uri=self._settings.generate_http_link(link), http_root=http_root, hls_type=hls_type)

    def generate_vod_link(self, hls_type: constants.HlsType, playlist_name=constants.DEFAULT_HLS_PLAYLIST,
                          oid=OutputUrl.generate_id()) -> OutputUrl:
        vods_root = self._generate_vods_root_dir(oid)
        link = '{0}/{1}'.format(vods_root, playlist_name)
        return OutputUrl(id=oid, uri=self._settings.generate_vods_link(link), http_root=vods_root, hls_type=hls_type)

    def generate_cod_link(self, hls_type: constants.HlsType, playlist_name=constants.DEFAULT_HLS_PLAYLIST,
                          oid=OutputUrl.generate_id()) -> OutputUrl:
        cods_root = self._generate_cods_root_dir(oid)
        link = '{0}/{1}'.format(cods_root, playlist_name)
        return OutputUrl(id=oid, uri=self._settings.generate_cods_link(link), http_root=cods_root, hls_type=hls_type)

    def fixup_output_urls(self):
        return

    def stable(self, *args, **kwargs):
        self.fixup_output_urls()
        return self._stream.save(*args, **kwargs)

    @classmethod
    def make_stream(cls, settings: ServiceSettings, client: ServiceClient):
        hard = HardwareStream(name=IStreamObject.DEFAULT_STREAM_NAME)
        hard.input = [InputUrl(id=InputUrl.generate_id())]
        hard.output = [OutputUrl(id=OutputUrl.generate_id())]
        return cls(hard, settings, client)

    # private
    def _generate_http_root_dir(self, oid: int):
        return '{0}/{1}/{2}/{3}'.format(self._settings.hls_directory, self._stream.get_type(), self._stream.get_id(),
                                        oid)

    def _generate_vods_root_dir(self, oid: int):
        return '{0}/{1}/{2}/{3}'.format(self._settings.vods_directory, self._stream.get_type(), self._stream.get_id(),
                                        oid)

    def _generate_cods_root_dir(self, oid: int):
        return '{0}/{1}/{2}/{3}'.format(self._settings.cods_directory, self._stream.get_type(), self._stream.get_id(),
                                        oid)

    def _fixup_http_output_urls(self):
        for idx, val in enumerate(self._stream.output):
            url = val.uri
            if url == constants.DEFAULT_TEST_URL:
                return

            parsed_uri = urlparse(url)
            if parsed_uri.scheme == 'http':
                filename = os.path.basename(parsed_uri.path)
                self._stream.output[idx] = self.generate_http_link(val.hls_type, filename, val.id)

    def _fixup_vod_output_urls(self):
        for idx, val in enumerate(self._stream.output):
            url = val.uri
            if url == constants.DEFAULT_TEST_URL:
                return

            parsed_uri = urlparse(url)
            if parsed_uri.scheme == 'http':
                filename = os.path.basename(parsed_uri.path)
                self._stream.output[idx] = self.generate_vod_link(val.hls_type, filename, val.id)

    def _fixup_cod_output_urls(self):
        for idx, val in enumerate(self._stream.output):
            url = val.uri
            if url == constants.DEFAULT_TEST_URL:
                return

            parsed_uri = urlparse(url)
            if parsed_uri.scheme == 'http':
                filename = os.path.basename(parsed_uri.path)
                self._stream.output[idx] = self.generate_cod_link(val.hls_type, filename, val.id)


class RelayStreamObject(HardwareStreamObject):
    def __init__(self, stream: RelayStream, settings: ServiceSettings, client: ServiceClient):
        super(RelayStreamObject, self).__init__(stream, settings, client)

    def config(self) -> dict:
        conf = super(RelayStreamObject, self).config()
        conf[ConfigFields.VIDEO_PARSER_FIELD] = self._stream.get_video_parser()
        conf[ConfigFields.AUDIO_PARSER_FIELD] = self._stream.get_audio_parser()
        return conf

    def fixup_output_urls(self):
        return self._fixup_http_output_urls()

    @classmethod
    def make_stream(cls, settings: ServiceSettings, client: ServiceClient):
        relay = RelayStream(name=IStreamObject.DEFAULT_STREAM_NAME)
        relay.input = [InputUrl(id=InputUrl.generate_id())]
        relay.output = [OutputUrl(id=OutputUrl.generate_id())]
        return cls(relay, settings, client)


class EncodeStreamObject(HardwareStreamObject):
    def __init__(self, stream: EncodeStream, settings: ServiceSettings, client: ServiceClient):
        super(EncodeStreamObject, self).__init__(stream, settings, client)

    def config(self) -> dict:
        conf = super(EncodeStreamObject, self).config()
        conf[ConfigFields.RELAY_VIDEO_FIELD] = self._stream.get_relay_video()
        conf[ConfigFields.RELAY_AUDIO_FIELD] = self._stream.get_relay_audio()
        conf[ConfigFields.DEINTERLACE_FIELD] = self._stream.get_deinterlace()
        frame_rate = self._stream.get_frame_rate()
        if frame_rate != constants.INVALID_FRAME_RATE:
            conf[ConfigFields.FRAME_RATE_FIELD] = frame_rate
        conf[ConfigFields.VOLUME_FIELD] = self._stream.get_volume()
        conf[ConfigFields.VIDEO_CODEC_FIELD] = self._stream.get_video_codec()
        conf[ConfigFields.AUDIO_CODEC_FIELD] = self._stream.get_audio_codec()
        audio_channels = self._stream.get_audio_channels_count()
        if audio_channels != constants.INVALID_AUDIO_CHANNELS_COUNT:
            conf[ConfigFields.AUDIO_CHANNELS_COUNT_FIELD] = audio_channels

        if self._stream.size.is_valid():
            conf[ConfigFields.SIZE_FIELD] = str(self._stream.size)

        vid_rate = self._stream.get_video_bit_rate()
        if vid_rate != constants.INVALID_VIDEO_BIT_RATE:
            conf[ConfigFields.VIDEO_BIT_RATE_FIELD] = vid_rate
        audio_rate = self._stream.get_audio_bit_rate()
        if audio_rate != constants.INVALID_AUDIO_BIT_RATE:
            conf[ConfigFields.AUDIO_BIT_RATE_FIELD] = self._stream.get_audio_bit_rate()
        if self._stream.logo.is_valid():
            conf[ConfigFields.LOGO_FIELD] = self._stream.logo.to_front_dict()
        if self._stream.rsvg_logo.is_valid():
            conf[ConfigFields.RSVG_LOGO_FIELD] = self._stream.rsvg_logo.to_front_dict()
        if self._stream.aspect_ratio.is_valid():
            conf[ConfigFields.ASPCET_RATIO_FIELD] = str(self._stream.aspect_ratio)
        return conf

    def fixup_output_urls(self):
        return self._fixup_http_output_urls()

    @classmethod
    def make_stream(cls, settings: ServiceSettings, client: ServiceClient):
        encode = EncodeStream(name=IStreamObject.DEFAULT_STREAM_NAME)
        encode.input = [InputUrl(id=InputUrl.generate_id())]
        encode.output = [OutputUrl(id=OutputUrl.generate_id())]
        return cls(encode, settings, client)


class TimeshiftRecorderStreamObject(RelayStreamObject):
    def __init__(self, stream: TimeshiftRecorderStream, settings: ServiceSettings, client: ServiceClient):
        super(TimeshiftRecorderStreamObject, self).__init__(stream, settings, client)

    def config(self) -> dict:
        conf = super(TimeshiftRecorderStreamObject, self).config()
        conf[ConfigFields.TIMESHIFT_CHUNK_DURATION] = self._stream.get_timeshift_chunk_duration()
        conf[ConfigFields.TIMESHIFT_DIR] = self.generate_timeshift_dir()
        conf[ConfigFields.TIMESHIFT_CHUNK_LIFE_TIME] = self._stream.timeshift_chunk_life_time
        return conf

    def generate_timeshift_dir(self):
        return '{0}/{1}'.format(self._settings.timeshifts_directory, self._stream.get_id())

    def fixup_output_urls(self):
        return

    @classmethod
    def make_stream(cls, settings: ServiceSettings, client: ServiceClient):
        tr = TimeshiftRecorderStream(name=IStreamObject.DEFAULT_STREAM_NAME)
        tr.visible = False
        tr.input = [InputUrl(id=InputUrl.generate_id())]
        return cls(tr, settings, client)


class CatchupStreamObject(TimeshiftRecorderStreamObject):
    def __init__(self, stream: CatchupStream, settings: ServiceSettings, client: ServiceClient):
        super(CatchupStreamObject, self).__init__(stream, settings, client)

    @classmethod
    def make_stream(cls, settings: ServiceSettings, client: ServiceClient):
        cat = CatchupStream(name=IStreamObject.DEFAULT_STREAM_NAME)
        cat.input = [InputUrl(id=InputUrl.generate_id())]
        cat.output = [OutputUrl(id=OutputUrl.generate_id())]
        return cls(cat, settings, client)

    def config(self) -> dict:
        conf = super(CatchupStreamObject, self).config()
        conf[ConfigFields.TIMESHIFT_DIR] = self._generate_catchup_dir()
        diff_msec = self._stream.stop - self._stream.start
        seconds = int(diff_msec.total_seconds())
        conf[ConfigFields.AUTO_EXIT_TIME_FIELD] = seconds
        return conf

    def start_request(self):
        now = datetime.now()
        if (now >= self._stream.start) and (now < self._stream.stop):
            super(CatchupStreamObject, self).start_request()

    # private:
    def _generate_catchup_dir(self):
        oid = self.stream().output[0].id
        return '{0}/{1}/{2}/{3}'.format(self._settings.hls_directory, self._stream.get_type(), self._stream.get_id(),
                                        oid)


class TimeshiftPlayerStreamObject(RelayStreamObject):
    def __init__(self, stream: TimeshiftPlayerStream, settings: ServiceSettings, client: ServiceClient):
        super(TimeshiftPlayerStreamObject, self).__init__(stream, settings, client)

    def config(self) -> dict:
        conf = super(TimeshiftPlayerStreamObject, self).config()
        conf[ConfigFields.TIMESHIFT_DIR] = self._stream.timeshift_dir
        conf[ConfigFields.TIMESHIFT_DELAY] = self._stream.timeshift_delay
        return conf

    @classmethod
    def make_stream(cls, settings: ServiceSettings, client: ServiceClient):
        tp = TimeshiftPlayerStream(name=IStreamObject.DEFAULT_STREAM_NAME)
        tp.input = [InputUrl(id=InputUrl.generate_id())]
        tp.output = [OutputUrl(id=OutputUrl.generate_id())]
        return cls(tp, settings, client)


class TestLifeStreamObject(RelayStreamObject):
    def __init__(self, stream: TestLifeStream, settings: ServiceSettings, client: ServiceClient):
        super(TestLifeStreamObject, self).__init__(stream, settings, client)

    def fixup_output_urls(self):
        return

    @classmethod
    def make_stream(cls, settings: ServiceSettings, client: ServiceClient):
        test = TestLifeStream(name=IStreamObject.DEFAULT_STREAM_NAME)
        test.visible = False
        test.input = [InputUrl(id=InputUrl.generate_id())]
        test.output = [OutputUrl(id=OutputUrl.generate_id(), uri=constants.DEFAULT_TEST_URL)]
        return cls(test, settings, client)


class CodRelayStreamObject(RelayStreamObject):
    def __init__(self, stream: CodRelayStream, settings: ServiceSettings, client: ServiceClient):
        super(CodRelayStreamObject, self).__init__(stream, settings, client)

    def fixup_output_urls(self):
        return self._fixup_cod_output_urls()

    @classmethod
    def make_stream(cls, settings: ServiceSettings, client: ServiceClient):
        cod = CodRelayStream(name=IStreamObject.DEFAULT_STREAM_NAME)
        cod.input = [InputUrl(id=InputUrl.generate_id())]
        cod.output = [OutputUrl(id=OutputUrl.generate_id())]
        return cls(cod, settings, client)


class CodEncodeStreamObject(EncodeStreamObject):
    def __init__(self, stream: CodEncodeStream, settings: ServiceSettings, client: ServiceClient):
        super(CodEncodeStreamObject, self).__init__(stream, settings, client)

    def fixup_output_urls(self):
        return self._fixup_cod_output_urls()

    @classmethod
    def make_stream(cls, settings: ServiceSettings, client: ServiceClient):
        cod = CodEncodeStream(name=IStreamObject.DEFAULT_STREAM_NAME)
        cod.input = [InputUrl(id=InputUrl.generate_id())]
        cod.output = [OutputUrl(id=OutputUrl.generate_id())]
        return cls(cod, settings, client)


# VODS


class ProxyVodStreamObject(ProxyStreamObject):
    def __init__(self, stream: ProxyVodStream, settings: ServiceSettings):
        super(ProxyVodStreamObject, self).__init__(stream, settings)

    @classmethod
    def make_stream(cls, settings: ServiceSettings):
        proxy = ProxyVodStream(name=IStreamObject.DEFAULT_STREAM_NAME)
        proxy.input = [InputUrl(id=InputUrl.generate_id())]
        proxy.output = [OutputUrl(id=OutputUrl.generate_id())]
        return cls(proxy, settings)


class VodRelayStreamObject(RelayStreamObject):
    def __init__(self, stream: VodRelayStream, settings: ServiceSettings, client: ServiceClient):
        super(VodRelayStreamObject, self).__init__(stream, settings, client)

    def config(self) -> dict:
        conf = super(RelayStreamObject, self).config()
        conf[ConfigFields.VODS_CLEANUP_TS] = True
        return conf

    def fixup_output_urls(self):
        return self._fixup_vod_output_urls()

    @classmethod
    def make_stream(cls, settings: ServiceSettings, client: ServiceClient):
        vod = VodRelayStream(name=IStreamObject.DEFAULT_STREAM_NAME)
        vod.loop = False
        vod.input = [InputUrl(id=InputUrl.generate_id())]
        vod.output = [OutputUrl(id=OutputUrl.generate_id())]
        return cls(vod, settings, client)


class VodEncodeStreamObject(EncodeStreamObject):
    def __init__(self, stream: VodEncodeStream, settings: ServiceSettings, client: ServiceClient):
        super(VodEncodeStreamObject, self).__init__(stream, settings, client)

    def config(self) -> dict:
        conf = super(EncodeStreamObject, self).config()
        conf[ConfigFields.VODS_CLEANUP_TS] = True
        return conf

    def fixup_output_urls(self):
        return self._fixup_vod_output_urls()

    @classmethod
    def make_stream(cls, settings: ServiceSettings, client: ServiceClient):
        vod = VodEncodeStream(name=IStreamObject.DEFAULT_STREAM_NAME)
        vod.loop = False
        vod.input = [InputUrl(id=InputUrl.generate_id())]
        vod.output = [OutputUrl(id=OutputUrl.generate_id())]
        return cls(vod, settings, client)


class EventStreamObject(VodEncodeStreamObject):
    @classmethod
    def make_stream(cls, settings: ServiceSettings, client: ServiceClient):
        event = EventStream(name=IStreamObject.DEFAULT_STREAM_NAME)
        event.input = [InputUrl(id=InputUrl.generate_id())]
        event.output = [OutputUrl(id=OutputUrl.generate_id())]
        return cls(event, settings, client)
