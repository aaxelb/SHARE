from functools import total_ordering


@total_ordering
class AcceptedContentType:
    # see https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Accept
    # and https://httpwg.org/specs/rfc7231.html#header.accept

    LIST_SEPARATOR = ','
    SUBTYPE_SEPARATOR = '/'
    PARAM_SEPARATOR = ';'
    PARAM_EQUAL = '='
    QUALITY_PARAM = 'q'

    ANY = '*'

    def __init__(self, content_type):
        # TODO-quest: nice error handling

        (media, *params) = content_type.split(AcceptedContentType.PARAM_SEPARATOR)

        (media_type, media_subtype) = media.split(AcceptedContentType.SUBTYPE_SEPARATOR)

        self.media_type = media_type.strip()
        self.media_subtype = media_subtype.strip()
        self.quality_value = 1.0

        self.media_params = {}
        for param in params:
            (param_key, param_value) = param.split(AcceptedContentType.PARAM_EQUAL)
            param_key = param_key.strip()
            param_value = param_value.strip()

            if param_key == AcceptedContentType.QUALITY_PARAM:
                self.quality_value = float(param_value)
                break  # any remaining are "Accept extension parameters", which do not exist (yet)
            else:
                self.media_params[param_key] = param_value

    @property
    def specificity(self):
        specif = 0
        if self.media_type != AcceptedContentType.ANY:
            specif += 1
        if self.media_subtype != AcceptedContentType.ANY:
            specif += 1
        specif += len(self.media_params)
        return specif

    @classmethod
    def gather_from_accept_headers(cls, *accept_header_values):
        accepted_content_types = []
        for accept_value in accept_header_values:
            accepted_content_types.extend((
                cls(content_type)
                for content_type in accept_value.split(cls.LIST_SEPARATOR)
                if content_type
            ))
        accepted_content_types.sort(key=cls.sort_key)
        return accepted_content_types

    def sort_key(self):
        return (self.quality_value, self.specificity)
