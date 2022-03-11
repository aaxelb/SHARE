

def simple___repr__(*attr_names):
    def my___repr__(obj):
        attr_reprs = (
            f'{attr_name}="{getattr(obj, attr_name)}"'
            for attr_name in attr_names
        )
        return f'{obj.__class__.__name__}({", ".join(attr_reprs)})'
    return my___repr__
