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

import collections
import copy
import errno
import hashlib
import os
import yaml

from wst import (
    DEFAULT_TARGETS,
    dry_run,
    log,
    WSError
)
from wst.shell import (
    call_git,
    call_output,
    remove
)

from wst.builder.cmake import CMakeBuilder  # noqa: E402
from wst.builder.meson import MesonBuilder  # noqa: E402
from wst.builder.setuptools import SetuptoolsBuilder  # noqa: E402


_REQUIRED_KEYS = {'build'}
_OPTIONAL_KEYS = {'deps', 'env', 'args', 'targets'}
_ALL_KEYS = _REQUIRED_KEYS.union(_OPTIONAL_KEYS)
def parse_yaml(root, manifest):  # noqa: E302
    '''Parses the given manifest for YAML and syntax correctness, or bails if
    something went wrong.'''
    try:
        with open(manifest, 'r') as f:
            d = yaml.safe_load(f)
    except IOError:
        raise WSError('ws manifest %s not found' % manifest)

    try:
        includes = d['include']
    except KeyError:
        includes = ()
        d['include'] = includes
    else:
        if not isinstance(includes, list):
            raise WSError('"include" key %s in %s is not a list'
                          % (includes, manifest))
        if len(includes) == 0:
            raise WSError('"include" key in %s is an empty list!' % manifest)

    try:
        search_paths = d['search-path']
    except KeyError:
        search_paths = ()
        d['search-path'] = search_paths
    else:
        if not isinstance(search_paths, list):
            raise WSError('"search-path" key %s in %s is not a list'
                          % (search_paths, manifest))
        if len(search_paths) == 0:
            raise WSError('include in %s is an empty list!' % manifest)

    try:
        projects = d['projects']
    except KeyError:
        if len(includes) == 0:
            raise WSError('"projects" key missing in manifest %s' % manifest)
        else:
            return d

    for proj, props in projects.items():
        for prop in _REQUIRED_KEYS:
            if prop not in props:
                raise WSError('"%s" key missing from project %s in manifest'
                              % (prop, proj))

        for prop in props:
            if prop not in _ALL_KEYS:
                raise WSError('unknown key "%s" for project %s specified in '
                              'manifest' % (prop, proj))

    # Add computed keys.
    parent = os.path.realpath(os.path.join(root, os.pardir))
    for proj, props in projects.items():
        try:
            deps = props['deps']
        except KeyError:
            props['deps'] = ()
        else:
            if not isinstance(deps, list):
                raise WSError('"deps" key in project %s must be a list' % proj)
            if len(set(deps)) != len(deps):
                raise WSError('project %s has duplicate dependency' % proj)

        try:
            env = props['env']
        except KeyError:
            props['env'] = {}
        else:
            if not isinstance(env, dict):
                raise WSError('"env" key in project %s must be a dictionary'
                              % proj)
            for k, v in env.items():
                if not isinstance(k, str):
                    raise WSError('env key %s in project %s must be a string' %
                                  (k, proj))
                if not isinstance(v, str):
                    raise WSError('env value "%s" (key "%s") in project %s '
                                  'must be a string' % (v, k, proj))

        try:
            args = props['args']
        except KeyError:
            props['args'] = []
        else:
            if not isinstance(args, list):
                raise WSError('"args" key in project %s must be a list' % proj)
            for opt in args:
                if not isinstance(opt, str):
                    raise WSError('option "%s" in project %s must be a string'
                                  % (opt, proj))
            args = []
            for opt in props['args']:
                args.extend(opt.split())
            props['args'] = args

        try:
            args = props['targets']
        except KeyError:
            props['targets'] = DEFAULT_TARGETS
        else:
            if props['targets'] is None:
                props['targets'] = ()
            else:
                if not isinstance(props['targets'], list):
                    raise WSError('"targets" key in project %s must be a list'
                                  % proj)
                for target in props['targets']:
                    if not isinstance(target, str):
                        raise WSError('target "%s" in project %s must be a '
                                      'string' % (opt, proj))

        props['path'] = os.path.join(parent, proj)

    return d


def include_paths(d, manifest):
    '''Return the manifest absolute paths included from the given parsed
    manifest.'''
    try:
        includes = d['include']
    except KeyError:
        return ()

    # The manifest's own directory is the default search path if none are
    # specified.
    search_paths = [os.path.realpath(os.path.join(manifest, os.pardir))]
    try:
        extra_search_paths = d['search-path']
    except KeyError:
        pass
    else:
        for path in extra_search_paths:
            path = os.path.realpath(os.path.join(manifest, os.pardir, path))
            search_paths.append(path)

    tweaked_includes = []
    for i, path in enumerate(includes):
        if path[0] == '/':
            # This is an absolute path, so no tweaking is necessary.
            tweaked_includes.append(path)
            continue

        # Relative path, so try to match it using the search paths.
        found_match = False
        for search_path in search_paths:
            full_path = os.path.realpath(os.path.join(search_path, path))
            if os.path.exists(full_path):
                found_match = True
                break
        if not found_match:
            raise WSError('cannot find manifest %s included by %s\n'
                          'search paths: %s' % (path, manifest, search_paths))

        # For directories, we include every file in the directory.
        if os.path.isdir(full_path):
            for filename in os.listdir(full_path):
                if not (filename.endswith('.yaml') or filename.endswith('.yml')):  # noqa: E501
                    continue
                filepath = os.path.join(full_path, filename)
                if not os.path.isfile(filepath):
                    continue
                tweaked_includes.append(filepath)
        else:
            tweaked_includes.append(full_path)

    return tweaked_includes


def merge_manifest(parent, parent_path, child, child_path):
    '''Merges the keys from the child dictionary into the parent dictionary. If
    there are conflicts, bail out with an error.'''
    try:
        parent_projects = parent['projects']
    except KeyError:
        parent_projects = {}
        parent['projects'] = parent_projects
    try:
        child_projects = child['projects']
    except KeyError:
        child_projects = {}
        child['projects'] = child_projects

    intersection = set(parent_projects).intersection(set(child_projects))
    if len(intersection) != 0:
        raise WSError('cannot include %s from %s, as the two share projects %s'
                      % (child_path, parent_path, intersection))
    parent_projects.update(child_projects)


def merge_includes(root, d, parent_manifest):
    '''Recursively merge all the include lines from the manifest into the given
    dictionary. Include paths are relative to the including manifest's parent
    directory.'''
    included = set(include_paths(d, parent_manifest))
    queue = collections.deque(included)
    while len(queue) > 0:
        manifest = queue.popleft()
        d_include = parse_yaml(root, manifest)
        log('merging manifest %s into %s' % (manifest, parent_manifest))
        merge_manifest(d, parent_manifest, d_include, manifest)
        for path in include_paths(d_include, manifest):
            # Prevent double-inclusion.
            if path in included:
                continue
            queue.append(path)
            included.add(path)


def parse_manifest_file(root, manifest):
    '''Parses the given ws manifest file, returning a dictionary of the
    manifest data.'''
    d = parse_yaml(root, manifest)
    merge_includes(root, d, manifest)

    # Compute reverse-dependency list.
    projects = d['projects']
    for proj, props in projects.items():
        props['downstream'] = []
    for proj, props in projects.items():
        deps = props['deps']
        for dep in deps:
            try:
                dep_props = projects[dep]
            except KeyError:
                raise WSError('project %s dependency %s not found in the '
                              'manifest' % (proj, dep))
            else:
                # Reverse-dependency list of downstream projects.
                dep_props['downstream'].append(proj)

    return projects


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


def find_root(start_dir):
    '''Recursively looks up in the directory hierarchy for a directory named
    .ws, and returns the first one found, or None if one was not found.'''
    path = os.path.realpath(start_dir)
    while path != '/':
        ws = os.path.join(path, '.ws')
        if os.path.isdir(ws):
            return ws
        path = os.path.realpath(os.path.join(path, os.pardir))
    return None


def get_default_manifest_name():
    '''Returns the name of the default ws manifest.'''
    return 'ws.yaml'


def get_ws_dir(root, ws):
    '''Returns the ws directory, given a directory obtained using
    find_root().'''
    return os.path.join(root, ws)


def get_ws_config_path(ws):
    '''Returns the ws internal config file, used for tracking the state of the
    workspace.'''
    return os.path.join(ws, 'config.yaml')


_ORIG_WS_CONFIG = None
_WS_CONFIG = None
def get_ws_config(ws):  # noqa: E302
    '''Parses the current workspace config, returning a dictionary of the
    state.'''
    global _WS_CONFIG
    if _WS_CONFIG is None:
        config_path = get_ws_config_path(ws)
        with open(config_path, 'r') as f:
            _WS_CONFIG = yaml.safe_load(f)
            global _ORIG_WS_CONFIG
            # Save a copy of the config so we know later whether or not to
            # write it out when someone asks to sync the config.
            _ORIG_WS_CONFIG = copy.deepcopy(_WS_CONFIG)

    # Split all project arguments by spaces so that args like '-D something'
    # turn into ['-D', 'something'], which is what exec requires. We do this
    # at parse time rather than in the "config" command to allow the user to
    # hand-edit in a natural way and have the config still work properly. The
    # next time the config is saved, it will be split by spaces.
    for proj, proj_map in _WS_CONFIG['projects'].items():
        parsed_args = []
        args = proj_map['args']
        for arg in args:
            parsed_args.extend(arg.split())
        proj_map['args'] = parsed_args

    return _WS_CONFIG


def _sync_file(f):
    '''Syncs a file to disk in whichever way we have available.'''
    # Not all systems have fdatasync. Empirically, the Mac appears not to have
    # it.
    if hasattr(os, 'fdatasync'):
        os.fdatasync(f)
    else:
        os.fsync(f)


def write_config(ws, config):
    '''Atomically updates the current ws config using the standard trick of
       writing to a tmp file in the same filesystem, syncing that file, and
       renaming it to replace the current contents.'''
    config_path = get_ws_config_path(ws)
    tmpfile = '%s.tmp' % config_path
    with open(tmpfile, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)
        f.flush()
        _sync_file(f)
    os.rename(tmpfile, config_path)

    global _WS_CONFIG
    _WS_CONFIG = config


def sync_config(ws):
    '''Writes out the config if and only if it changed since we first read
       it.'''
    if _WS_CONFIG == _ORIG_WS_CONFIG:
        log('ws config did not change, so not updating')
        return
    log('updating config at %s' % ws)

    if dry_run():
        return

    write_config(ws, _WS_CONFIG)


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


def get_bin_paths(ws, proj):
    '''Gets the path to installed libraries for a project.'''
    noarch_bin_dir = os.path.join(get_install_dir(ws, proj), 'bin')
    arch_bin_arch_dir = os.path.join(noarch_bin_dir, get_host_triplet())
    return [noarch_bin_dir, arch_bin_arch_dir]


def get_lib_paths(ws, proj):
    '''Gets the path to installed libraries for a project.'''
    noarch_lib_dir = os.path.join(get_install_dir(ws, proj), 'lib')
    arch_lib_dir = os.path.join(noarch_lib_dir, get_host_triplet())
    return [noarch_lib_dir, arch_lib_dir]


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
    log('invalidating checksum for %s' % proj)
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
    bin_dirs = get_bin_paths(ws, proj)

    pkgconfig_paths = get_pkgconfig_paths(ws, proj)
    lib_paths = get_lib_paths(ws, proj)
    merge_var(env, 'PKG_CONFIG_PATH', pkgconfig_paths)
    merge_var(env, 'LD_LIBRARY_PATH', lib_paths)
    if include_path:
        merge_var(env, 'PATH', [build_dir] + bin_dirs)

    # Add in any builder-specific environment tweaks.
    install_dir = get_install_dir(ws, proj)
    get_builder(d, proj).env(proj, install_dir, build_dir, env)

    # Add in any project-specific environment variables specified in the
    # manifest.
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
