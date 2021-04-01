import logging as log

log.basicConfig(level=log.DEBUG)


def process_incoming_request(_data):

    log.info(f'''
        from the task -> {_data}
    ''')
    
    return _data
