import inspect
import logging
import importlib


class ModulePath:
    PATH_DELIMITER = "."

    def __init__(self, path):
        if self.PATH_DELIMITER not in path:
            raise ValueError("{} not a valid module path".format(path))

        self._path = path
        self._parts = path.split(self.PATH_DELIMITER)

    @property
    def parent(self):
        new_parts = self._parts[:-1]
        new_path = self.PATH_DELIMITER.join(new_parts)

        if len(new_path) == 0:
            raise ValueError("No parent exists for module {}".format(self._path))

        return ModulePath(new_path)

    def add_child(self, child):
        new_parts = self._parts + [child]
        new_path = self.PATH_DELIMITER.join(new_parts)

        return ModulePath(new_path)

    def __eq__(self, other) -> bool:
        return self._parts == str(other).split(".")

    def __str__(self) -> str:
        return self._path

    def __repr__(self) -> str:
        self.__str__()


class DynamicPackage:
    def __new__(cls, package, mock=False):
        log = logging.getLogger(cls.__name__)

        def import_pkg(module_path):
            log.info("Importing package {}".format(module_path))
            module = importlib.import_module(str(module_path))
            classes = inspect.getmembers(module, inspect.isclass)

            target_class = None
            for _, found_class in classes:
                found_module_path = ModulePath(found_class.__module__)
                if found_module_path == module_path:
                    target_class = found_class
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

            return target_class

        kwargs = package["kwargs"] if "kwargs" in package else dict()
        custom_mock = False
        if "mock" in kwargs:
            custom_mock = kwargs["mock"]
        path = ModulePath("package" + "." + package["module"])
        remote_path = (
            ModulePath(package["remote_module"]) if "remote_module" in package else None
        )

        instance = None
        if custom_mock:
            pkg = path.parent.add_child("mock")
            try:
                class_ = import_pkg(pkg)
            except (ImportError, ModuleNotFoundError) as e:
                log.error(e)
                log.debug(e, exc_info=1)
            except Exception as e:
                log.error("Unexpected error importing custom mock class")
                log.exception(e)
        elif mock:
            pkg = path.parent.parent.add_child("mock")
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
