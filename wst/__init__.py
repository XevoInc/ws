class WSError(Exception):
    def __init__(self, msg):
        super().__init__(msg)


_DRY_RUN = False
def dry_run():  # noqa: E302
    '''Retrieves the current dry run setting.'''
    global _DRY_RUN
    return _DRY_RUN


def set_dry_run():
    '''Sets whether or not to use dry run mode.'''
    global _DRY_RUN
    _DRY_RUN = True
