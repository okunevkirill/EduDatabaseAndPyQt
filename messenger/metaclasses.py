import dis


def _get_methods(namespace: dict) -> tuple:
    """Getting methods from disassembled code"""
    _global_methods = set()  # получаем с помощью 'LOAD_GLOBAL'
    _tos_methods = set()  # получаем с помощью 'LOAD_METHOD'
    _attrs = set()  # получаем с помощью 'LOAD_ATTR'
    for name in namespace:
        try:
            instructions = dis.get_instructions(namespace[name])
        except TypeError:
            continue
        else:
            for instruction in instructions:
                if instruction.opname == 'LOAD_GLOBAL' and instruction.argval not in _global_methods:
                    _global_methods.add(instruction.argval)
                elif instruction.opname == 'LOAD_METHOD' and instruction.argval not in _tos_methods:
                    _tos_methods.add(instruction.argval)
                elif instruction.opname == 'LOAD_ATTR' and instruction.argval not in _attrs:
                    _attrs.add(instruction.argval)

    return _global_methods, _tos_methods, _attrs


class ClientVerifier(type):
    def __init__(cls, name, bases, namespace):
        _global_methods, _tos_methods, _attrs = _get_methods(namespace)

        if 'accept' in _tos_methods or 'listen' in _tos_methods:
            raise TypeError('The use of a forbidden method was detected in the class')
        if not ('SOCK_STREAM' in _attrs and 'AF_INET' in _attrs):
            raise TypeError('Incorrect socket initialization')

        super().__init__(name, bases, namespace)


class ServerVerifier(type):
    def __init__(cls, name, bases, namespace):
        _global_methods, _tos_methods, _attrs = _get_methods(namespace)

        if 'connect' in _tos_methods:
            raise TypeError('The use of a forbidden method was detected in the class')
        if not ('SOCK_STREAM' in _attrs and 'AF_INET' in _attrs):
            raise TypeError('Incorrect socket initialization')

        super().__init__(name, bases, namespace)
