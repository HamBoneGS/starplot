import json

from functools import wraps


def merge_dict(dict_1: dict, dict_2: dict) -> None:
    """

    Args:
        dict_1: Base dictionary to merge into
        dict_2: Dictionary to merge into the base (dict_1)

    Returns:
        None (dict_1 is modified directly)
    """
    for k in dict_2.keys():
        if k in dict_1 and isinstance(dict_1[k], dict) and isinstance(dict_2[k], dict):
            merge_dict(dict_1[k], dict_2[k])
        else:
            dict_1[k] = dict_2[k]


def use_style(style_class, style_attr: str = None):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            style = kwargs.get("style")
            style_args = {x:kwargs[x] for x in kwargs if x[:7] == "style__"}

            if style and isinstance(style, dict):
                if style_args:
                    raise Exception("Both versions of style override used. Use either kwargs OR dictionary") # not sure exactly what to say here
                if style_attr is not None:
                    # if style is a dict and there's a base style, then we just want to merge the changes
                    base_style = getattr(args[0].style, style_attr).model_dump_json()
                    base_style = json.loads(base_style)

                    merge_dict(base_style, style)

                    kwargs["style"] = style_class(**base_style)
                else:
                    kwargs["style"] = style_class(**style)

            elif style is None:
                if style_args:
                    if style_attr is not None:
                        # if style kwargs are used - build style dict and pass as "style" variable
                        styling_overrides = {}
                        for key, value in style_args.items():
                            parts = key.split("__")[1:]
                            temp = styling_overrides
                            for part in parts[:-1]:
                                temp.setdefault(part, {})
                                temp = temp[part]
                            temp[parts[-1]] = value
                            
                        base_style = getattr(args[0].style, style_attr).model_dump_json()
                        base_style = json.loads(base_style)

                        merge_dict(base_style, styling_overrides)
                        
                        kwargs["style"] = style_class(**base_style)
                    else:
                        kwargs["style"] = style_class(**styling_overrides)

                elif style_attr is not None:
                    # if no style overrides and there's a base style, then just pass the base style
                    kwargs["style"] = getattr(args[0].style, style_attr, None)

            return func(*args, **kwargs)

        return wrapper

    return decorator
