Sublime PyMdown
===============
A plugin for sublime text that can convert/preview markdown via [PyMdown](https://github.com/facelessuser/PyMdown) (a python tool that utilizes [Python Markdown](https://pythonhosted.org/Markdown/) and [Pygments](http://pygments.org/) to convert).  PyMdown can also batch convert/preview folders as well in Sublime's sidebar.  Also provides commands to strip out critic marks out of a markdown file.

This is a personal package that I have no intentions of releasing to wider audiences, but I do not restrict others from using it.  Behavior and commands may be in flux as this is still in development.

# Recommended Commands
No commands are provided out of the box currently except for the batch convert commands for the sidebar.  Templates and styles are configured in the PyMdown binary's setting file.  This plugin simply threads calls to it, and in some cases reads it output to the clipboard or sublime view.

```javascript
    //////////////////////////////////
    // PyMdown
    //////////////////////////////////
    {
        "caption": "PyMdown: Preview Markdown",
        "command": "py_mdown_convert",
        "args": {"target": "browser"}
    },
    {
        "caption": "PyMdown: Save to Disk",
        "command": "py_mdown_convert",
        "args": {"target": "save"}
    },
    {
        "caption": "PyMdown: To Clipboard",
        "command": "py_mdown_convert",
        "args": {"target": "clipboard", "modes": ["template", "plain", "no_template"]}
    },
    {
        "caption": "PyMdown: Export to Sublime",
        "command": "py_mdown_convert",
        "args": {"target": "sublime", "modes": ["template", "plain", "no_template"]}
    },
    {
        "caption": "PyMdown: Critic Markdown (view)",
        "command": "py_mdown_critic",
        "args": {"critic_mode": "view"}
    },
    {
        "caption": "PyMdown: Critic Strip Markdown (accept)",
        "command": "py_mdown_critic",
        "args": {"critic_mode": "accept"}
    },
    {
        "caption": "PyMdown: Critic Strip Markdown (reject)",
        "command": "py_mdown_critic",
        "args": {"critic_mode": "reject"}
    },

```

# License
MIT license.

Copyright (c) 2014 Isaac Muse <isaacmuse@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
