import inspect
import logging
import importlib
import util.utils as utils


class PackageNotImportedError(Exception):
    def __init__(self, message):
        super().__init__(message)


class PackageNotFoundError(Exception):
    def __init__(self, message):
        super().__init__(message)


class PackageImporterError(Exception):
    def __init__(self, message):
        super().__init__(message)


class PackageImporter:
    PACKAGE_REF_KEY = "package_ref"
    PACKAGE_REFS_KEY = "package_refs"

    def __init__(self, package_entries, mock=False):
        self._package_entries = package_entries
        self._use_mock_pkgs = mock

        self._package_instances = dict()

    def get_package_entry(self, name):
        for entry in self._package_entries:
            if name == entry["name"]:
                return entry

        raise PackageNotFoundError("{} not a package configured for import")

    def add_instance(self, name, instance):
        self._package_instances[name] = instance

    def get_instance(self, name):
        if name not in self._package_instances:
            raise PackageNotImportedError("{} not an imported package".format(name))

        return self._package_instances[name]

    def get_instances(self, names):
        return [self.get_instance(name) for name in names]

    def import_packages(self, mock=False):
        orderset = self._get_orderset()

        for package_ref in orderset:
            entry = self.get_package_entry(package_ref)
            name = entry["name"]
            packages_embedded_entry = self.config_embed_packages(entry)
            package_config = packages_embedded_entry["package"]

            instance = DynamicPackage(package_config, mock)
            self.add_instance(name, instance)

    def config_embed_packages(self, config):
        paths = utils.find_paths_to_key(config, self.PACKAGE_REF_KEY)

        for keys in paths:
            package_refs = utils.get_by_path(config, keys)
            package_ref = package_refs[0]

            inst = self.get_instance(package_ref)
            utils.del_by_path(config, keys)
            utils.set_by_path(config, keys[:-1], inst)

        paths = utils.find_paths_to_key(config, self.PACKAGE_REFS_KEY)
        for keys in paths:
            package_refs = utils.get_by_path(config, keys)

            insts = self.get_instances(package_refs)
            utils.del_by_path(config, keys)
            utils.set_by_path(config, keys[:-1], insts)

        return config

    def _get_orderset(self):
        def recursive_order(root_config, branch_config):
            root_package_ref = root_config["name"]
            package_refs = []
            order = [root_package_ref]

            paths = utils.find_paths_to_key(
                branch_config, self.PACKAGE_REF_KEY, self.PACKAGE_REFS_KEY
            )
            for keys in paths:
                package_ref = utils.get_by_path(branch_config, keys)
                package_refs = package_refs + package_ref

            if root_package_ref in package_refs:
                raise PackageImporterError(
                    "cannot import package {}: circular dependency with package {} as it's a listed {}.".format(
                        root_package_ref, branch_config["name"], self.PACKAGE_REF_KEY
                    )
                )

            for ref in package_refs:
                config = self.get_package_entry(ref)
                order = recursive_order(root_config, config) + order

            return order

        orderset = list()
        for package in self._package_entries:
            package_import_order = recursive_order(package, package)

            for dependent in package_import_order:
                if dependent in orderset:
                    continue
                orderset.append(dependent)

        return orderset


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
            raise ValueError("no parent exists for module {}".format(self._path))

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
                    "could not find class to import at module {}".format(module_path)
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
                log.error("unexpected error importing custom mock class")
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
