from core.helpers import get_landing, settings
import importlib.util


def mime_list():
    return {
        "image/jpg": "jpg",
        "image/jpeg": "jpeg",
        "image/png": "png",
        "image/svg": "svg",
        "image/svg+xml": "svg",
        "image/webp": "webp",
        "video/mp4": "mp4",
        "video/x-m4v": "mp4",
        "video/webm": "webm",
    }


def alt_blocks_check(module, file=None):
    landing = get_landing().domain
    app_name = landing.replace("-", "_").replace(".", "__")
    base_dir = settings(landing).BASE_DIR

    try:
        app_settings_template = importlib.import_module(f"_sites.{app_name}.settings")
        page_template = app_settings_template.TEMPLATE_SITE or app_name
    except (ImportError, AttributeError):
        page_template = app_name if "__blank__sinergium" in app_name else None

    modules_path = base_dir / f"_sites/{page_template}/data/modules.py"

    if not modules_path.exists():
        return None

    spec = importlib.util.spec_from_file_location("modules", str(modules_path))
    if spec is None:
        return None

    modules = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modules)

    DATA = modules.DATA
    
    for key, value in DATA['list'].items():
        module_match = value.get('module') == module
        file_value = value.get('file') if value.get('file') else None
        file_match = (file is None and file_value is None) or file_value == file
        
        if module_match and file_match:
            return value.get('alt_blocks', None)
    return None
