from stevedore import extension


class EntryPoints:
    """Singleton container for stevedore extensions.

    Loads each namespace when requested for the first time.
    """
    _managers = {}

    @classmethod
    def get_class(self, namespace, name):
        manager = EntryPoints._managers.get(namespace)
        if manager is None:
            manager = extension.ExtensionManager(namespace)
            EntryPoints._managers[namespace] = manager
        return manager[name].plugin
