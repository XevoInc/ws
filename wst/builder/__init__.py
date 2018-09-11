class Builder(object):
    '''A builder, representing the interaction with an underlying build
    system, such as CMake or meson. Since this is really an interface and not a
    class, all methods on it should be class methods.'''
    @classmethod
    def env(cls, proj, prefix, build_dir, source_dir, env, build_type):
        raise NotImplementedError

    @classmethod
    def conf(cls, proj, prefix, build_dir, source_dir, env, build_type):
        raise NotImplementedError

    @classmethod
    def build(cls, proj, source_dir, build_dir, env):
        raise NotImplementedError

    @classmethod
    def clean(cls, proj, build_dir, env):
        raise NotImplementedError
