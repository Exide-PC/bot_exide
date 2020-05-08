def replace_forbidden(name, replacer=None):
    illegal = ['NUL','\',''//',':','*','"','<','>','|']
    for i in illegal:
        name = name.replace(i, replacer or '-')
    return name