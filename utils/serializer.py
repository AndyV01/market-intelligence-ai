def sanitize(obj):
    import numpy as np

    # dict
    if isinstance(obj, dict):
        return {str(k): sanitize(v) for k, v in obj.items()}

    # list / tuple / set
    elif isinstance(obj, (list, tuple, set)):
        return [sanitize(v) for v in obj]

    # numpy types
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, (np.integer,)):
        return int(obj)
    elif isinstance(obj, (np.floating,)):
        return float(obj)

    # numpy array
    elif isinstance(obj, np.ndarray):
        return obj.tolist()

    # None
    elif obj is None:
        return None

    return obj