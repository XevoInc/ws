#!/usr/bin/python3
#
# Functions for handling internal ws configuration.
#
# Copyright (c) 2018 Xevo Inc. All rights reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

import errno
import hashlib
import logging
import os
import yaml

from wst import (
    dry_run,
    log,
    WSError
)
from wst.shell import (
    call_git,
    call_output,
    remove
)

from wst.builder.cmake import CMakeBuilder
from wst.builder.meson import MesonBuilder
from wst.builder.setuptools import SetuptoolsBuilder


BUILD_TYPES = ('debug', 'release')
VALID_CONFIG = {
    'type': BUILD_TYPES
}


def parse_manifest_file(root, manifest):
    '''Parses the given ws manifest file, returning a dictionary of the
    manifest data.'''
    try:
        with open(manifest, 'r') as f:
            d = yaml.load(f)
    except IOError:
        raise WSError('ws manifest %s not found' % manifest)

    # Validate.
    required = {'build'}
    optional = {'deps', 'env', 'options'}
    total = required.union(optional)
    for proj, props in d.items():
        for prop in required:
            if prop not in props:
                raise WSError('%s key missing from project %s in manifest'
                              % (prop, proj))

        for prop in props:
            if prop not in total:
                raise WSError('unknown key %s for project %s specified in '
                              'manifest' % (prop, proj))

    # Add computed keys.
    parent = os.path.realpath(os.path.join(root, os.pardir))
    for proj, props in d.items():
        try:
            deps = props['deps']
        except KeyError:
            deps = tuple()
        else:
            if not isinstance(deps, list):
                raise WSError('deps key in project %s must be a list' % proj)
            deps = tuple(deps)
        props['deps'] = deps

        try:
            env = props['env']
        except KeyError:
            env = {}
        else:
            if not isinstance(env, dict):
                raise WSError('env key in project %s must be a dictionary'
                              % proj)
            for k, v in env.items():
                if not isinstance(k, str):
                    raise WSError('env key %s in project %s must be a string' %
                                  (k, proj))
                if not isinstance(v, str):
                    raise WSError('env value %s (key "%s") in project %s '
                                  'must be a string' % (v, k, proj))
        props['env'] = env

        try:
            options = props['options']
        except KeyError:
            options = tuple()
        else:
            if not isinstance(props['options'], list):
                raise WSError('options key in project %s must be a list' %
                              proj)
            for opt in props['options']:
                if not isinstance(opt, str):
                    raise WSError('option %s in project %s must be a string' %
                                  (opt, proj))
            options = tuple(opt.split() for opt in props['options'])
        props['options'] = options

        props['path'] = os.path.join(parent, proj)
        props['downstream'] = []

    # Compute reverse-dependency list.
    for proj, props in d.items():
        deps = props['deps']
        for dep in deps:
            if dep not in d:
                raise WSError('Project %s dependency %s not found in the '
                              'manifest' % (proj, dep))

            # Reverse-dependency list of downstream projects.
            d[dep]['downstream'].append(proj)

        if len(set(deps)) != len(deps):
            raise WSError('Project %s has duplicate dependency' % proj)

    return d


def parse_manifest(root):
    '''Parses the ws manifest, returning a dictionary of the manifest data.'''
    # Parse.
    return parse_manifest_file(root, get_manifest_link(root))


def dependency_closure(d, projects):
    '''Returns the dependency closure for a list of projects. This is the set
    of dependencies of each project, dependencies of that project, and so
    on.'''
    # This set is for detecting circular dependencies.
    order = []
    processed = set()

    def process(project):
        processed.add(project)
        for dep in d[project]['deps']:
            if dep not in order:
                if dep in processed:
                    raise WSError('Projects %s and %s circularly depend on '
                                  'each other' % (project, dep))
                process(dep)
        order.append(project)

    for project in projects:
        if project not in processed:
            process(project)
    return tuple(order)


def find_root():
    '''Recursively looks up in the directory hierarchy for a directory named
    .ws, and returns the first one found, or None if one was not found.'''
    path = os.path.realpath(os.getcwd())
    while path != '/':
        ws = os.path.join(path, '.ws')
        if os.path.isdir(ws):
            return ws
        path = os.path.realpath(os.path.join(path, os.pardir))
    return None


def get_default_manifest_name():
    '''Returns the name of the default ws manifest.'''
    return 'ws-manifest.yaml'


def get_ws_dir(root, ws):
    '''Returns the ws directory, given a directory obtained using
    find_root().'''
    return os.path.join(root, ws)


def get_ws_config_path(ws):
    '''Returns the ws internal config file, used for tracking the state of the
    workspace.'''
    return os.path.join(ws, 'config.yaml')


def get_ws_config(ws):
    '''Parses the current workspace config, returning a dictionary of the
    state.'''
    config = get_ws_config_path(ws)
    with open(config, 'r') as f:
        return yaml.load(f)


def update_config(ws, config):
    '''Atomically updates the current ws config using the standard trick of
    writing to a tmp file in the same filesystem, syncing that file, and
    renaming it to replace the current contents.'''
    log('updating config at %s' % ws)
    if dry_run():
        return

    config_path = get_ws_config_path(ws)
    tmpfile = '%s.tmp' % config_path
    with open(tmpfile, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)
        f.flush()
        os.fdatasync(f)
    os.rename(tmpfile, config_path)


def get_default_ws_name():
    '''Returns the name of the default workspace (the one you get when you
    don't explicitly give your workspace a name.'''
    return 'default'


def get_default_ws_link(root):
    '''Returns a path to the symlink that points to the current workspace.'''
    return os.path.join(root, get_default_ws_name())


def get_manifest_link_name():
    '''Returns the name of the symlink to the ws manifest.'''
    return 'manifest'


def get_manifest_link(root):
    '''Returns a path to the symlink that points to the ws manifest.'''
    return os.path.join(root, get_manifest_link_name())


def get_checksum_dir(ws):
    '''Returns the directory containing project build checksums.'''
    return os.path.join(ws, 'checksum')


def get_checksum_file(ws, proj):
    '''Returns the file containing the checksum for a given project.'''
    return os.path.join(get_checksum_dir(ws), proj)


def get_source_dir(root, d, proj):
    '''Returns the source code directory for a given project.'''
    parent = os.path.realpath(os.path.join(root, os.pardir))
    return os.path.join(parent, d[proj]['path'])


def get_toplevel_build_dir(ws):
    '''Returns the top-level directotory containing build artifacts for all
    projects.'''
    return os.path.join(ws, 'build')


def get_proj_dir(ws, proj):
    '''Returns the root directory for a given project.'''
    return os.path.join(get_toplevel_build_dir(ws), proj)


def get_source_link(ws, proj):
    '''Returns a path to the symlink inside the project directory that points
    back into the active source code (the code that the git-repo tool
    manages).'''
    return os.path.join(get_proj_dir(ws, proj), 'src')


def get_build_dir(ws, proj):
    '''Returns the build directory for a given project.'''
    return os.path.join(get_proj_dir(ws, proj), 'build')


def get_install_dir(ws, proj):
    '''Returns the install directory for a given project (the directory we use
    for --prefix and similar arguments.'''
    return os.path.join(get_build_dir(ws, proj), 'install')


_HOST_TRIPLET = None
def get_host_triplet():  # noqa: E302
    '''Gets the GCC host triplet for the current machine.'''
    global _HOST_TRIPLET
    if _HOST_TRIPLET is None:
        _HOST_TRIPLET = call_output(['gcc', '-dumpmachine'], override=True)
        _HOST_TRIPLET = _HOST_TRIPLET.rstrip()
    return _HOST_TRIPLET


def get_lib_paths(ws, proj):
    '''Gets the path to installed libraries for a project.'''
    noarch_lib_dir = os.path.join(get_install_dir(ws, proj), 'lib')
    arch_lib_arch_dir = os.path.join(noarch_lib_dir, get_host_triplet())
    return [noarch_lib_dir, arch_lib_arch_dir]


def get_pkgconfig_paths(ws, proj):
    '''Gets the path to the .pc files for a project.'''
    pkgconfig_paths = []
    for lib_path in get_lib_paths(ws, proj):
        pkgconfig_paths.append(os.path.join(lib_path, 'pkgconfig'))
    return pkgconfig_paths


def set_stored_checksum(ws, proj, checksum):
    '''Sets the stored project checksum. This should be called after building
    the project.'''
    # Note that we don't worry about atomically writing this. The worst cases
    # are:
    # - We crash or get power loss and have a partial write. This causes a
    # corrupt checksum, which will not match the calculated checksum, be
    # stale, and cause us to redo the build. But an incremental build system
    # will cause this to have pretty low cost.
    # - The checksum is never updated when it should have been. Again, we'll
    # get a stale checksum and a rebuild, which shouldn't much hurt us.
    checksum_file = get_checksum_file(ws, proj)
    with open(checksum_file, 'w') as f:
        f.write('%s\n' % checksum)


def invalidate_checksum(ws, proj):
    '''Invalidates the current project checksum. This can be used to force a
    project to rebuild, for example if one of its dependencies rebuilds.'''
    logging.debug('invalidating checksum for %s' % proj)
    if dry_run():
        return

    try:
        remove(get_checksum_file(ws, proj))
    except OSError as e:
        if e.errno != errno.ENOENT:
            raise


def get_stored_checksum(ws, proj):
    '''Retrieves the currently stored checksum for a given project, or None if
    there is no checksum (either because the project was cleaned, or because
    we've never built the project before).'''
    if dry_run():
        return 'bogus-stored-checksum'

    checksum_file = get_checksum_file(ws, proj)
    try:
        with open(checksum_file, 'r') as f:
            checksum = f.read().rstrip()
    except IOError:
        return None

    # Note that we don't need to check if the checksum is corrupt. If it is, it
    # will not match the calculated checksum, so we will correctly see a stale
    # checksum.

    return checksum


def calculate_checksum(source_dir):
    '''Calculates and returns the SHA-1 checksum of a given git directory,
    including submodules and dirty files. This function should uniquely
    identify any source code that would impact the build but ignores files in
    .gitignore, as they are assumed to have no impact on the build. If this is
    not the case, it is likely a bug in the underlying project. Although we
    could use the find command instead of git, it is much slower and takes into
    account inconsequential files, like .cscope or .vim files that don't change
    the build (and that are typically put in .gitignore).

    It is very important that this function is both fast and accurate, as it is
    used to determine when projects need to be rebuilt, and thus gets run
    frequently. If this function gets too slow, working with ws will become
    painful. If this function is not accurate, then ws will have build bugs.'''
    # Collect the SHA-1 of HEAD and the diff of all dirty files.
    #
    # Note that it's very important to use the form "git diff HEAD" rather than
    # "git diff" or "git diff --cached" because "git diff HEAD" collects ALL
    # changes rather than just staged or unstaged changes.
    #
    # Additionally note the use of "submodule foreach --recursive", which will
    # recursively diff all submodules, submodules-inside-submodules, etc. This
    # ensures correctness even if deeply nested submodules change.
    head = call_git(source_dir, ('rev-parse', '--verify', 'HEAD'))
    repo_diff = call_git(source_dir,
                         ('diff',
                          'HEAD',
                          '--diff-algorithm=myers',
                          '--no-renames',
                          '--submodule=short'))
    submodule_diff = call_git(source_dir,
                              ('submodule',
                               'foreach',
                               '--recursive',
                               'git',
                               'diff',
                               'HEAD',
                               '--diff-algorithm=myers',
                               '--no-renames'))

    if dry_run():
        return 'bogus-calculated-checksum'

    # Finally, combine all data into one master hash.
    total = hashlib.sha1()
    total.update(head)
    total.update(repo_diff)
    total.update(submodule_diff)

    return total.hexdigest()


# These hooks contain functions to handle the build tasks for each build system
# we support. To add a new build system, add a new entry and supply the correct
# hooks.
_BUILD_TOOLS = {
    'meson': MesonBuilder,
    'cmake': CMakeBuilder,
    'setuptools': SetuptoolsBuilder
}


def get_builder(d, proj):
    '''Returns the build properties for a given project. This function should
    be used instead of directly referencing _BUILD_TOOLS.'''
    build = d[proj]['build']
    try:
        builder = _BUILD_TOOLS[build]
    except KeyError:
        raise WSError('unknown build tool %s for project %s'
                      % (build, proj))

    return builder


def merge_var(env, var, val):
    '''Merges the given value into the given environment variable using ":"
    syntax. This can be used to add an entry to LD_LIBRARY_PATH and other such
    environment variables.'''
    try:
        current = env[var]
    except KeyError:
        entries = val
    else:
        entries = current.split(':')
        if val not in entries:
            entries = val + entries
    env[var] = ':'.join(entries)


def expand_var(s, var, expansions):
    '''Expands a template string of the form ${VAR} with each entry of the
    expansions array, then join them in using the same scheme as the PATH
    variable. For example, given:
    s = ${ABC}/stuff
    var = ABC
    expansions = ['a', 'b', 'c'],
    then expand_sub would return 'a/stuff:b/stuff:c/stuff'.'''
    results = []
    for expansion in expansions:
        result = s.replace('${%s}' % var, expansion)
        # Don't add duplicate entries.
        if result not in results:
            results.append(result)
    return ':'.join(results)


def _merge_build_env(ws, d, proj, env, include_path):
    '''Merges the build environment for a single project into the given env.
    This is a helper function called by get_build_env for each dependency of a
    given project.'''
    build_dir = get_build_dir(ws, proj)
    install_dir = get_install_dir(ws, proj)
    bin_dir = os.path.join(install_dir, 'bin')

    pkgconfig_paths = get_pkgconfig_paths(ws, proj)
    ld_library_paths = get_lib_paths(ws, proj)
    merge_var(env, 'PKG_CONFIG_PATH', pkgconfig_paths)
    merge_var(env, 'LD_LIBRARY_PATH', ld_library_paths)
    if include_path:
        merge_var(env, 'PATH', [build_dir, bin_dir])

    # Add in any builder-specific environment tweaks.
    get_builder(d, proj).env(proj, install_dir, build_dir, env)

    # Add in any project-specific environment variables specified in the
    # manifest.
    lib_paths = get_lib_paths(ws, proj)
    install_dir = get_install_dir(ws, proj)
    for var, val in d[proj]['env'].items():
        val = expand_var(val, 'LIBDIR', lib_paths)
        val = expand_var(val, 'PREFIX', [install_dir])
        # Expand every environment variable.
        for k, v in env.items():
            val = expand_var(val, k, [v])
        merge_var(env, var, [val])


def get_build_env(ws, d, proj, include_path=False):
    '''Gets the environment that should be set during builds (and for the env
    command) for a given project.'''
    build_env = os.environ.copy()
    deps = dependency_closure(d, [proj])
    for dep in deps:
        _merge_build_env(ws, d, dep, build_env, include_path)

    return build_env
