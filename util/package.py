import importlib

def get_package_instance(package_name, **kwargs):
    module_path = package_name + ".get_class_instance"

    get_class_instance = None
    try:
        module = importlib.import_module(module_path)
        get_class_instance = getattr(module, "get_class_instance")
    except Exception as e:
        raise e
    
    instance = get_class_instance(**kwargs)

    return instance