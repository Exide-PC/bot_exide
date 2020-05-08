def first(items, condition):
    return next((i for i in items if condition(i)), None)