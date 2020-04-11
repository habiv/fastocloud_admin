import pyfastocloud_models.constants as constants
from bson.objectid import ObjectId
from pymodm import MongoModel, fields


class M3uParseStreams(MongoModel):
    class Meta:
        collection_name = 'm3uparse_streams'

    def to_front_dict(self) -> dict:
        return {'id': str(self.id), 'name': self.name, 'epgid': self.tvg_id, 'logo': self.tvg_logo, 'group': self.group}

    @property
    def id(self):
        return self.pk

    @staticmethod
    def get_by_id(sid: ObjectId):
        try:
            m3u = M3uParseStreams.objects.get({'_id': sid})
        except M3uParseStreams.DoesNotExist:
            return None
        else:
            return m3u

    @staticmethod
    def get_by_name(name: str):
        try:
            m3u = M3uParseStreams.objects.get({'name': name})
        except M3uParseStreams.DoesNotExist:
            return None
        else:
            return m3u

    name = fields.CharField(max_length=constants.MAX_STREAM_NAME_LENGTH,
                            min_length=constants.MIN_STREAM_NAME_LENGTH,
                            required=True)
    tvg_id = fields.ListField(fields.CharField(), default=[])
    tvg_logo = fields.ListField(fields.CharField(), default=[])
    group = fields.ListField(fields.CharField(), default=[])


class M3uParseVods(MongoModel):
    class Meta:
        collection_name = 'm3uparse_vods'

    @staticmethod
    def get_by_id(sid: ObjectId):
        try:
            m3u = M3uParseVods.objects.get({'_id': sid})
        except M3uParseVods.DoesNotExist:
            return None
        else:
            return m3u

    @staticmethod
    def get_by_name(name: str):
        try:
            m3u = M3uParseVods.objects.get({'name': name})
        except M3uParseVods.DoesNotExist:
            return None
        else:
            return m3u

    def to_front_dict(self) -> dict:
        return {'id': str(self.id), 'name': self.name, 'logo': self.tvg_logo, 'group': self.group}

    @property
    def id(self):
        return self.pk

    name = fields.CharField(max_length=constants.MAX_STREAM_NAME_LENGTH,
                            min_length=constants.MIN_STREAM_NAME_LENGTH,
                            required=True)
    tvg_logo = fields.ListField(fields.CharField(), default=[])
    group = fields.ListField(fields.CharField(), default=[])
