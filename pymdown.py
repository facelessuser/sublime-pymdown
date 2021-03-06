"""
PyMdown for Sublime.

Licensed under MIT
Copyright (c) 2014 - 2015 Isaac Muse <isaacmuse@gmail.com>
"""
import sublime
import sublime_plugin
from os.path import join, basename, dirname, exists, isfile, splitext
import _thread as thread
import subprocess
import sys
import traceback
try:
    from SubNotify.sub_notify import SubNotifyIsReadyCommand as Notify
except Exception:
    class Notify:

        """Notify fallback class."""

        @classmethod
        def is_ready(cls):
            """Return false to disable notifications."""

            return False

if sys.platform.startswith('win'):
    _PLATFORM = "windows"
elif sys.platform == "darwin":
    _PLATFORM = "osx"
else:
    _PLATFORM = "linux"

DANGER_PATTER_MSG = \
    '''Are you sure you want to use the pattern: %s?
`
This may try and convert more than you bargined for.'''


def get_environ():
    """Get environment and force utf-8."""

    import os
    env = {}
    env.update(os.environ)

    if _PLATFORM != 'windows':
        shell = env['SHELL']
        p = subprocess.Popen(
            [shell, '-l', '-c', 'echo "#@#@#${PATH}#@#@#"'],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        result = p.communicate()[0].decode('utf8').split('#@#@#')
        if len(result) > 1:
            bin_paths = result[1].split(':')
            if len(bin_paths):
                env['PATH'] = ':'.join(bin_paths)

    env['PYTHONIOENCODING'] = 'utf8'
    env['LANG'] = 'en_US.UTF-8'
    env['LC_CTYPE'] = 'en_US.UTF-8'

    return env


###############################
# General Helper Methods
###############################
def log(msg):
    """Log messages."""

    print("PyMdown:\n%s" % msg)


def status_notify(msg):
    """Notify in status bar."""

    sublime.status_message(msg)


def err_dialog(msg):
    """Error message via dialog."""

    sublime.error_message("PyMdown:\n%s" % msg)


def notify(msg):
    """Notification message."""

    settings = sublime.load_settings("pymdown.sublime-settings")
    if settings.get("use_sub_notify", False) and Notify.is_ready():
        sublime.run_command("sub_notify", {"title": "PyMdown", "msg": msg})
    else:
        status_notify(msg)


def error(msg):
    """Error message."""

    settings = sublime.load_settings("pymdown.sublime-settings")
    if settings.get("use_sub_notify", False) and Notify.is_ready():
        sublime.run_command("sub_notify", {"title": "PyMdown", "msg": msg, "level": "error"})
    else:
        err_dialog(msg)


def parse_file_name(file_name):
    """Parse the file name."""

    if file_name is None or not exists(file_name):
        title = "Untitled"
        basepath = None
    else:
        title = splitext(basename(file_name))[0]
        basepath = dirname(file_name)
    return title, basepath


def handle_line_endings(text):
    """Strip out carriage returns."""

    return text.replace('\r', '')


###############################
# PyMdown Worker (Threaded by calls)
###############################
class PyMdownWorker(object):

    """Worker object that calls PyMdown and returns results."""

    working = False

    def __init__(self, **kwargs):
        """Initialize."""

        settings = sublime.load_settings("pymdown.sublime-settings")
        self.binary = settings.get("binary", {}).get(_PLATFORM, "")
        self.paths = kwargs.get('paths', [])
        self.buffer = kwargs.get('buffer', [])
        self.patterns = list(kwargs.get('patterns', settings.get('batch_convert_patterns', [])))
        self.critic_mode = kwargs.get('critic_mode', 'view')
        self.critic_dump = bool(kwargs.get('critic_dump', False))
        self.title = kwargs.get('title', None)
        self.basepath = str(kwargs.get('basepath', None))
        self.batch = bool(kwargs.get('batch', False))
        self.preview = bool(kwargs.get('preview', False))
        self.settings = kwargs.get('settings', None)
        self.quiet = bool(kwargs.get('quiet', False))
        self.callback = kwargs.get('callback', None)
        self.plain = bool(kwargs.get('plain', False))
        self.force_stdout = bool(kwargs.get('force_stdout', False))
        self.force_no_template = bool(kwargs.get('force_no_template', False))
        self.results = ''
        self.cmd = []

    def parse_options(self):
        """Parse options."""

        cmd = []
        if self.binary:
            cmd.append(self.binary)
            if self.title:
                cmd += ["--title", self.title]
            if self.basepath:
                cmd += ["--basepath", self.basepath]
            if self.settings:
                cmd.append += ["-s", self.settings]
            if self.critic_mode == 'accept':
                cmd.append('-a')
            elif self.critic_mode == 'reject':
                cmd.append('-r')
            elif self.critic_mode == 'view':
                cmd += ['-r', '-a']
            if self.batch:
                cmd.append('-b')
            if self.plain:
                cmd.append('-P')
            if self.force_stdout:
                cmd.append('--force-stdout')
            if self.force_no_template:
                cmd.append('--force-no-template')
            if self.preview:
                cmd.append('-p')
            if self.quiet:
                cmd.append('-q')
            if self.critic_dump:
                cmd.append('--critic-dump')
        return cmd

    def get_process(self, cmd):
        """Get the subprocess object."""

        if _PLATFORM == "windows":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            p = subprocess.Popen(
                cmd, startupinfo=startupinfo,
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                env=get_environ()
            )
        else:
            p = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                env=get_environ()
            )
        return p

    def execute_buffer(self, cmd):
        """Execute on a buffer."""

        returncode = 0
        try:
            p = self.get_process(cmd)
            for line in self.buffer:
                p.stdin.write(line.encode('utf-8'))
            results, errors = p.communicate()
            self.results += (results + errors).decode("utf-8")
            returncode = p.returncode
        except Exception:
            self.results += str(traceback.format_exc())
            returncode = 1
        return returncode

    def execute(self, cmd):
        """Execute on file paths."""

        returncode = 0
        try:
            p = self.get_process(cmd)
            results, errors = p.communicate()
            self.results += (results + errors).decode("utf-8")
            returncode = p.returncode
        except Exception:
            self.results += str(traceback.format_exc())
            returncode = 1
        return returncode

    def process_pattern(self, pth):
        """Process file patterns."""

        if isfile(pth):
            ptrns = [pth]
        else:
            ptrns = [join(pth, p) for p in self.patterns]
        return ptrns

    def call_callback(self, err):
        """Call the callback function."""

        if self.callback and callable(self.callback):
            sublime.set_timeout(
                lambda results=self.results, err=err: self.callback(self.results, err),
                0
            )

    def run(self):
        """Run PyMdown on provided buffer or paths."""

        err = False
        self.cmd = self.parse_options()
        self.results = ''
        if PyMdownWorker.working:
            self.results = "PyMdown Worker is already running!"
            self.call_callback(True)
        else:
            PyMdownWorker.working = True
            if len(self.cmd) and len(self.buffer):
                if self.execute_buffer(self.cmd):
                    err = True
            if len(self.cmd) and len(self.paths):
                for pth in self.paths:
                    if len(self.patterns):
                        self.cmd += self.process_pattern(pth)
                    elif exists(pth):
                        self.cmd.append(pth)
                    else:
                        continue

                    if self.execute(self.cmd):
                        err = True
            self.call_callback(err)
            PyMdownWorker.working = False


###############################
# Batch Processing Commands
###############################
BATCH_EMPTY = 0
BATCH_FILE = 1
BATCH_DIR = 2
BATCH_MIXED = 3
BATCH_MISSING = 4


class PyMdownBatchCommand(sublime_plugin.WindowCommand):

    """Sublime command to batch process markdown files."""

    kind = None
    CONVERT = "Convert"
    PREVIEW = "Preview"

    def run(self, paths=[], patterns=None, preview=False):
        """Run the command."""

        if not PyMdownWorker.working:
            settings = sublime.load_settings("pymdown.sublime-settings")
            options = {
                "paths": paths,
                "batch": True,
                "critic_accept": settings.get("critic_mode", 'view'),
                "preview": preview,
                "callback": self.callback
            }
            if patterns is not None:
                options['patterns'] = patterns
            thread.start_new_thread(PyMdownWorker(**options).run, ())

    def report(self, msg, console=False, err=False):
        """Report results."""

        if console:
            log(handle_line_endings(msg))
        else:
            if err:
                error(handle_line_endings(msg))
            else:
                notify(handle_line_endings(msg))

    def determine_type(self, paths=[]):
        """
        Determine run type.

        Is this a batch run, file run, directory run, etc.
        """

        kind = BATCH_EMPTY
        has_dirs = False
        has_files = False
        missing = False
        for path in paths:
            if not exists(path):
                kind = BATCH_MISSING
                missing = True
                break
            if isfile(path):
                has_files = True
                kind = BATCH_FILE
            else:
                has_dirs = True
                kind = BATCH_DIR

            if has_dirs and has_files:
                kind = BATCH_MIXED
                break
        if missing and kind == BATCH_FILE:
            kind = BATCH_MISSING
        elif kind == BATCH_MISSING and has_dirs:
            kind = BATCH_DIR
        self.kind = kind
        return kind

    def is_enabled(self, *args, **kwargs):
        """Check if the command is enabled."""

        enabled = True
        if not PyMdownWorker.working:
            batch_type = self.determine_type(kwargs.get('paths', []))
            if batch_type in (BATCH_MISSING, BATCH_MIXED, BATCH_EMPTY):
                enabled = False
        else:
            enabled = False
        return enabled

    def description(self, *args, **kwargs):
        """Description for menus."""

        description = '%s Folder(s)...'
        if not PyMdownWorker.working:
            batch_type = self.determine_type(kwargs.get('paths', []))
            if batch_type in (BATCH_MISSING, BATCH_MIXED, BATCH_EMPTY):
                description = 'NA'
            elif batch_type == BATCH_FILE:
                description = '%s File(s)...'
        else:
            description = 'NA'
        return description % (self.PREVIEW if kwargs.get('preview', False) else self.CONVERT)

    def callback(self, results, err):
        """To be called after conversion."""

        print("error_status %s" % str(err))
        self.report(results, console=True)
        if err:
            self.report("Batch Process Completed with Errors!", err=True)
        else:
            self.report("Batch Process Completed!")


class PyMdownCustomBatchCommand(PyMdownBatchCommand):

    """Custom batch conversion command."""

    CONVERT = "Custom Convert"
    PREVIEW = "Custom Preview"

    def run(self, paths=[], preview=False):
        """Run the command."""

        self.paths = paths
        self.preview = preview
        settings = sublime.load_settings("pymdown.sublime-settings")
        default = ';'.join(settings.get('batch_convert_patterns', []))
        view = self.window.show_input_panel(
            "File Pattern", default, self.process_patterns, None, None
        )
        view.sel().add(sublime.Region(0, view.size()))

    def process_patterns(self, value):
        """Process the file patterns."""

        if value != "":
            patterns = []
            for p in [v.strip() for v in value.split(';')]:
                if p == '':
                    continue
                if p.endswith('*'):
                    if sublime.ok_cancel_dialog(DANGER_PATTER_MSG % p):
                        patterns.append(p)
                else:
                    patterns.append(p)
            if len(patterns):
                self.window.run_command(
                    'py_mdown_batch',
                    {"paths": self.paths, "patterns": patterns, "preview": self.preview}
                )


###############################
# Sublime Buffer Commands
###############################
class PyMdownEditText(sublime_plugin.TextCommand):

    """Command for editting th view buffer."""

    wbfr = None

    def run(self, edit, mode='insert', save=False):
        """
        Run the command.

        Can insert or replace.
        """

        cls = PyMdownEditText
        if mode == 'insert':
            self.view.insert(edit, 0, handle_line_endings(cls.wbfr))
        elif mode == 'replace':
            self.view.replace(edit, sublime.Region(0, self.view.size()), handle_line_endings(cls.wbfr))
        else:
            error('Invalid edit mode!')
            cls.clear_wbfr()
            return
        cls.clear_wbfr()
        if save:
            self.view.run_command('save')

    @classmethod
    def set_wbfr(cls, text):
        """Set the buffer to write."""

        cls.wbfr = text

    @classmethod
    def clear_wbfr(cls):
        """Clear the write buffer."""

        cls.wbfr = None


class PyMdownCommand(sublime_plugin.TextCommand):

    """Base class for Buffer conversion."""

    message = "<placeholder>"

    def setup(self, alternate_settings=None):
        """Setup of genreal settings."""

        settings = sublime.load_settings("pymdown.sublime-settings")
        self.file_name = self.view.file_name()
        title, basepath = parse_file_name(self.view.file_name())
        self.options = {
            'title': title if title is not None else 'Untitled',
            'basepath': basepath,
            'critic_mode': settings.get("mode", "view"),
            'settings': alternate_settings,
            'callback': self.callback
        }

    def callback(self, results, err):
        """Callback after conversion."""

    def convert(self, edit):
        """Convert from Markdown to HTML."""

    def call(self):
        """Call the worker."""

        if not PyMdownWorker.working:
            thread.start_new_thread(PyMdownWorker(**self.options).run, ())
        else:
            error("PyMdown Worker is already running!")

    def error_message(self):
        """Error message."""

        error(self.message)

    def is_enabled(self, *args, **kwargs):
        """Check if command is enabled."""

        return not PyMdownWorker.working


class PyMdownConvertCommand(PyMdownCommand):

    """Convert the buffer."""

    message = "pymdown failed to generate html!"

    def run(
        self, edit, target="browser",
        alternate_settings=None,
        modes=['template']
    ):
        """Run the command."""

        window = self.view.window()
        if window is None:
            return

        self.setup(alternate_settings)
        self.target = target

        plain = False
        ignore_template = False
        self.modes = []
        options = []
        if 'template' in modes:
            self.modes.append('template')
            options.append('Template')
        if 'plain' in modes:
            plain = True
            self.modes.append('plain')
            options.append('Plain HTML')
        if 'no_template' in modes:
            ignore_template = True
            self.modes.append('no_template')
            options.append('No Template')
        if len(options) > 1:
            window.show_quick_panel(options, self.process_choice)
        else:
            self.launch_mode(plain, ignore_template)

    def process_choice(self, value):
        """Process the user arguments for conversion."""
        if value >= 0:
            plain = False
            ignore_template = False
            mode = self.modes[value]
            if mode == 'plain':
                plain = True
            elif mode == 'no_template':
                ignore_template = True
            self.launch_mode(plain, ignore_template)

    def launch_mode(self, plain=False, ignore_template=False):
        """Wrapper around conversion that sets additonal settings according to launch mode."""

        self.plain = plain
        self.ignore_template = ignore_template
        self.convert()

    def output(self, results):
        """Redirect to the appropriate output."""

        if self.target == "browser":
            # Nothing to do
            print(results)
            notify("Conversion complete!\nOpening in browser...")
        elif self.target == "clipboard":
            sublime.set_clipboard(results)
            notify("Conversion complete!\nResult copied to clipboard.")
        elif self.target == "sublime":
            window = self.view.window()
            if window is not None:
                view = window.new_file()
                PyMdownEditText.set_wbfr(results)
                view.run_command("py_mdown_edit_text")
                notify("Conversion complete!\nResult exported to Sublime.")
            else:
                error("Could not export!\nView has no window")
        elif self.target == "save" and not self.save_src_exists:
            # Save as...
            window = self.view.window()
            if window is not None:
                view = window.new_file()
                if view is not None:
                    PyMdownEditText.set_wbfr(results)
                    view.run_command("py_mdown_edit_text", {"save": True})
                    notify("Conversion complete!\nReady to save...")
                else:
                    error("Failed to create new view!")
            else:
                error("Could not save!\nView has no window")
        elif self.target == "save":
            notify("Conversion complete!\nHtml saved.")
        else:
            error("Unknown output type!")

    def convert(self):
        """Convert the buffer."""

        if self.target == "browser":
            self.options['preview'] = True
        else:
            self.options['quiet'] = True

        if self.target in ("sublime", "clipboard"):
            self.options['force_stdout'] = True

        if self.target == "save":
            if self.file_name is None or not exists(self.file_name):
                self.options['force_stdout'] = True
                self.save_src_exists = False
            else:
                self.save_src_exists = True

        if self.plain:
            self.options['plain'] = True
        elif self.ignore_template:
            self.options['force_no_template'] = True

        bfr = []
        sels = self.view.sel()
        regions = []
        if len(sels):
            for sel in sels:
                if sel.size():
                    regions.append(sel)
        if len(regions) == 0:
            regions.append(sublime.Region(0, self.view.size()))
        for region in regions:
            for line in self.view.lines(region):
                bfr.append(self.view.substr(line) + '\n')
        self.options['buffer'] = bfr

        self.call()

    def callback(self, results, err):
        """Callback after conversion."""

        if err:
            if self.target == "browser":
                log(handle_line_endings(results))
            self.error_message()
        else:
            self.output(results)


class PyMdownCriticCommand(PyMdownCommand):

    """Command to view, accept, or reject critic marks."""

    message = "pymdown failed to strip your critic comments!"
    modes = ('view', 'accept', 'reject')

    def run(self, edit, mode='view', alternate_settings=None):
        """Run the command."""

        self.setup(alternate_settings)
        self.mode = mode if mode in self.modes else 'view'
        self.convert()

    def convert(self):
        """Convert the buffer."""

        self.options['critic_dump'] = True
        self.options['quiet'] = True
        self.options['force_stdout'] = True
        self.options['critic_mode'] = self.mode
        bfr = []
        for line in self.view.lines(sublime.Region(0, self.view.size())):
            bfr.append(self.view.substr(line) + '\n')
        self.options['buffer'] = bfr
        self.call()

    def callback(self, results, err):
        """Callback after conversion."""

        if err:
            log(handle_line_endings(results))
            self.error_message()
        else:
            window = self.view.window()
            found = False
            if window is not None:
                _, i = window.get_view_index(self.view)
                if i != -1:
                    found = True
                    PyMdownEditText.set_wbfr(results)
                    self.view.run_command("py_mdown_edit_text", {"mode": "replace"})
                    window.focus_view(self.view)

            if not found:
                error("Original view appears to be missing!")
            else:
                notify("Critic stripping succesfully completed!")
