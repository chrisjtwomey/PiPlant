import inspect
import logging
import importlib


class DynamicPackage:
    def __new__(cls, package, mock=False):
        log = logging.getLogger(cls.__name__)

        def import_pkg(module_path):
            log.info("Importing package {}".format(module_path))
            module = importlib.import_module(module_path)
            classes = inspect.getmembers(module, inspect.isclass)

            target_class = None
            for _, class_ in classes:
                if class_.__module__ == module_path:
                    target_class = class_
                    break

            if target_class is None:
                raise ImportError(
                    "Could not find class to import at module {}".format(module_path)
                )

            log.debug(
                "Importing class {} from module {}".format(
                    target_class.__qualname__, module_path
                )
            )

            return class_

        kwargs = package["kwargs"] if "kwargs" in package else dict()
        custom_mock = False
        if "mock" in kwargs:
            custom_mock = kwargs["mock"]
        path = "package" + "." + package["module"]
        remote_path = package["remote_module"] if "remote_module" in package else None

        instance = None
        if custom_mock:
            pkg = path + ".mock."
            try:
                class_ = import_pkg(pkg)
            except ImportError as ie:
                log.warning(
                    "Error importing custom mock class. Retrying with stock mock class..."
                )
                log.exception(ie)

                path_segs = path.split(".")
                # TODO: this could be better
                pkg = path_segs[0] + "." + path_segs[1] + "." + path_segs[2] + ".mock"
                class_ = import_pkg(pkg)
            except Exception as e:
                log.error("Unexpected error importing custom mock class")
                log.exception(e)
        elif mock:
            path_segs = path.split(".")
            # TODO: this could be better
            pkg = path_segs[0] + "." + path_segs[1] + "." + path_segs[2] + ".mock"
            class_ = import_pkg(pkg)
        else:
            pkg = path
            if remote_path is not None:
                pkg = remote_path
            class_ = import_pkg(pkg)

        log.debug(
            "Initializing class {} with kwargs: {}".format(class_.__qualname__, kwargs)
        )

        instance = class_(**kwargs)

        return instance
