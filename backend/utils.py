
def remove_empty_element(data):
    copied_keys = tuple(data.keys())
    for key in copied_keys:
        if isinstance(data[key], dict) and data[key]:
            remove_empty_element(data[key])
        if not data[key]:
            data.pop(key)

