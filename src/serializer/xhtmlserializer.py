from htmlserializer import HTMLSerializer

class XHTMLSerializer(HTMLSerializer):
    defaults = {
        'quote_attr_values': True,
        'minimize_boolean_attributes': False,
        'use_trailing_solidus': True,
        'escape_lt_in_attrs': True,
        'omit_optional_tags': False
    }

    def __init__(self, **kwargs):
        options = self.defaults.copy()
        options.update(kwargs)
        HTMLSerializer.__init__(self, **options)
