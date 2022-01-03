import logging
import importlib


class DynamicPackage:
    def __new__(cls, package, mock=False):
        def import_pkg(pkg):
            log.info("Importing package {}".format(pkg))
            module = importlib.import_module(pkg)
            return getattr(module, class_name)

        kwargs = package["kwargs"] if "kwargs" in package else dict()
        if "mock" in kwargs:
            mock = kwargs["mock"]
        path = package["module"]
        remote_path = package["remote_module"] if "remote_module" in package else None

        log = logging.getLogger(cls.__name__)

        class_name = package["class"]

        instance = None
        if mock:
            pkg = path + ".mock." + class_name.lower()
            class_ = import_pkg(pkg)
        else:
            pkg = path + class_name.lower()
            if remote_path is not None:
                pkg = remote_path
            class_ = import_pkg(pkg)

        instance = class_(**kwargs)

        return instance
