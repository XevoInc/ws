# Workspace tool
`ws` is a lightweight tool for managing a collection of code repositories. It is
intended to handle coarse dependencies between projects, building multiple
projects in the right order and passing the correct flags to each (such as
`PKG_CONFIG_PATH` and similar). It is not intended to be a full-fledged build
system, but instead should merely build each project in the right order and with
the right environment glue. Everything it does can be done by-hand, so rather
than a replacing existing build tools, it merely automates the tedious task of
manually specifying `--prefix`, setting env vars, and rebuilding projects in the
right order when they change.

Inside each workspace, projects are installed inside a localized `install`
directory so that no installations ever leak out of a workspace. Projects
dependent on other projects automatically link to the other projects' install
directories by setting `PKG_CONFIG_PATH`, `LD_LIBRARY_PATH`, and everything else
necessary.

Note that `ws` does not directly handle source code syncing. That job is left to
[repo](https://code.google.com/archive/p/git-repo/) and similar tools.

## Dependencies
`ws` depends on the Python 3 PyYAML, which you can get either with `sudo apt
install python3-yaml` or via `pip3 install -r requirements.txt` from the top of
the repository.

## Installing
To install `ws`, you can use the `setup.py` script at the top level of the
repository: `python3 setup.py install <add any custom options here>`. You can
also use pip: `pip3 install .` from the top of the repository. Finally, if you
want the installed `ws` to directly symlink into your source directory instead
of being a one-time copy of the code, use `pip3 install -e .`, which activates
pip "developer mode". This way, code changes immediately take effect without
re-running the install step.

## ws
The `ws` script is the main point of interaction with your workspaces. It
assumes you have already synced a bunch of code using `repo` or some other tool
and, unless you use special options, it assumes you are currently somewhere
inside the root of the source that `ws` manages. However, you can be anywhere
inside that tree and do not have to be at the top of it.

The normal workflow for `ws` is as follows:

```
repo init -u MANIFEST-REPO-URL
repo sync
ws init -s repo
ws build
```

By default, `ws init` will look for a file called `ws-manifest.yaml` at the root
of the repository containing the `git-repo` manifest (the one we passed `-u`
into when we called `repo init`). This file contains dependency and build system
information for the projects that `ws` manages. Note that `ws` does not have to
manage all the same projects that `repo` manages, but it can. The full format
for `ws-manifest.yaml` is at the bottom of the README.

If you don't use the `git-repo` tool, you can instead pass in your own ws
manifest via `ws init -s fs -m`. This lets you manage the manifest however you
like (e.g. submodules, or manually).

## bash-completion
If you like bash-completions and typing things fast, you can do:
```
. bash-completion/ws
```
And get auto-completion for ws commands.

### ws init
When you run `ws init`, ws creates a `.ws` directory in the current working
directory. This directory can contain multiple workspaces, but there is always
a default workspace, which is the one that gets used if you don't specify an
alternate workspace with the `-w` option. One reason to create multiple
workspaces is to manage multiple build configurations, such as separate debug
and release builds. However, all workspaces in the same `.ws` directory will
still operate on the same source code (the repositories configured in
`ws-manifest.yaml`).

If you wish to create multiple workspaces, you can use `ws init` with an
argument to do so. For example, `ws init new` would create a new workspace
called `new`. However, it would not be used by default until you run `ws
default new`. That said, you can also use `-w` to operate on it (e.g. `ws -w
new build`).

If you specify `-m`, you can manually point to a `ws-manifest.yaml` to use. By
default, this is relative to a repository containing a git-repo manifest (e.g.
if you have a `.repo` directory after running `repo init`, then it is relative
to `.repo/manifests`). If you specify `-s fs`, then it can point
anywhere on the filesystem instead.

### ws default
`ws default` is used to change the default workspace (the one used when you
don't specify a `-w` option).

### ws build
`ws build` is the main command you run. If you specify no arguments, it will
build every project that repo knows about. If you instead specify a project or
list of projects, it will build only those, plus any dependencies of them.
Additionally, `ws` will checksum the source code on a per-repo basis and avoid
rebuilding anything that hasn't changed. The checksumming logic uses git for
speed and reliability, so source managed by `ws` has to use git.

### ws clean
`ws clean` cleans the specified projects, or all projects if no arguments
are given. By default, it just runs the clean command for the underlying build
system (meson, cmake, etc.). If you also use the `-f/--force` switch, it will
instead remove the entire build directory instead of trusting the underlying
build system.

### ws env
`ws env` allows you to enter the build environment for a given project. If given
no arguments, it gives you an interactive shell inside the build directory for
the project. If given arguments, it instead runs the specified command from that
directory. In both cases, it sets up the right build enviroment so build
commands you might use will work correctly and you can inspect if something
seems wrong.

An example use of `ws env` is to manually build something or to tweak the build
configuration of a given project in a way that `ws` doesn't know how to handle.

### ws test
`ws test` allows you to run unit tests on a project that you built. The tests
are configured in the `ws` manifest  file and can be any set of arbitrary
commands. The tests will be run from the build directory of the project as if
you had run `ws env -b PROJECT TEST`.

The `cwd` paremeter to the tests allows tests to run in an alternate directory
that the build directory. Any of the template variables listed below can be used
for this.

### ws config
`ws config` sets either workspace-wide or per-project configuration settings.
The following settings are supported:

Workspace-wide settings:
- `type`: `debug` or `release`. This specifies the workspace build type.

Per-project settings:
- `enable`: sets whether or not to build the given project. Typically you want to
  build everything, but you might satisfy a particular dependency from the
  distro, or manually build and install it outside of the workspace.
- `args`: sets build arguments for a particular project, which get directly passed
  to the builder (e.g. `cmake` or `meson`). An example would be passing `-D
  KEY=VAL` to set a preprocessor variable.


## ws manifest
The `ws` manifest is a YAML file specifying a few things about the projects `ws`
manages:
- What build system they use (currently supports `meson`, `cmake`, and
  `setuptools`).
- What dependencies they have on other projects managed by `ws`.
- Any special environment variables they need.
- Any special builder options needed (e.g. `-DCMAKE_` type of options). These
  options are passed straight through into each build system without
  modification.
- Any other manifests that should be included. Include paths can be absolute or
  relative. If they are relative, they are interpreted relative to the parent
  directory of the including manifest. Directories can also be included, in
  which case every manifest file in the directory file is included.
- Any search paths to search for manifests listed in "include". Can be either
  absolute or relative. If relative, it's relative to the parent directory of
  this manifest.

The syntax is as follows:
```
include:
    - some-other-manifest.yaml
    - some-directory-of-manifests

search-path:
    - ../projects # a directory containing manifests

projects:
    some-project:
        build: meson
        deps:
            - gstreamer
            - ...
        targets:
            - docs
            - install
        env:
            GST_PLUGIN_PATH: ${LIBDIR}/gstreamer-1.0
        tests:
            - some test command here
            - some other test command here
            - cwd: ${SRCDIR}
              cmds:
                  - these commands
                  - will be run from the source directory
                  - instead of the build directory

    gstreamer:
        build: meson
        args:
            - -D gtk_doc=disabled
```

In this case, `some-project` builds with `meson`, and requires `gstreamer` and
some other dependencies. In order to find gstreamer plugins, it needs
`GST_PLUGIN_PATH` set. It uses template syntax to refer to `${LIBDIR}`, which will
be filled in with the library path for the project.

Here is the complete list of usable template variables:
```
- ${BUILDDIR}: the project build directory
- ${SRCDIR}: the project source directory (top of the project's git repository)
- ${LIBDIR}: the library path for the project (what `LD_LIBRARY_PATH` will be
  set to for the project's build environment.
- ${PREFIX}: the project's prefix (what you would pass to `--prefix`).
```
