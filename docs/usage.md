# User Guide {: .doctitle}
Configuring and using Sublime PyMdown.

---

# Overview
No commands are provided out of the box currently except for the batch convert commands for the sidebar.  Any additional desired commands must be manually configured.  Templates and styles are separately configured in the PyMdown binary's [setting file](http://facelessuser.github.io/PyMdown/user-guide/general-usage/#configuration-file) or in YAML frontmatter that can be provided at the beginning of a markdown file.  This plugin simply threads calls to PyMdown and feeds it the content of either a Sublime view or file in the sidebar.  The output is previewed in your default web browser, but if desired, it can also read copy the output to the clipboard or a Sublime view.

# Commands
Commands are constructed around either `py_mdown_convert` or `py_mdown_critic`.

py_mdown_convert
: 
    Command used for converting and previewing Markdown files.

    | Parameter | Type | Default | Description |
    |-----------|------|---------|-------------|
    | target | string | browser | This defines what the target output is.  This can be `browser`, `clipboard`, `sublime`, `save`. |
    | alternate_settings | string | None | This can be a path to a PyMdown settings file that overrides the default PyMdown settings. |
    | modes | [string] | ['template'] | This defines what mode(s) to let the user pick from.  The allowed values are `template`, `plain`, `no_template`. |

py_mdown_critic
: 
    Command used for converting and previewing Markdown with critic marks.

    | Parameter | Type | Default | Description |
    |-----------|------|---------|-------------|
    | alternate_settings | string | None | This can be a path to a PyMdown settings file that overrides the default PyMdown settings. |
    | modes | string | view | This defines what mode is used when handling CriticMarkup.  Acceptable options are: `view`, `accept`, `reject`. |

    - The `view` mode will do it's best to visually represent the Markdown output with the additional CriticMarkup HTML.
    - `accept` will accept the current suggested CriticMarkup.
    - 'reject` will reject the specified CriticMarkup.


## Examples
Here are some examples of commands.

```js
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
