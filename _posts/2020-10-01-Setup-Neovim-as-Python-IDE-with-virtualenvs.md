---
title: Setup Neovim as Python IDE with virtualenvs
description: Explanation of the steps necessary to install Neovim as a Python IDE (end of 2020)
date: '2020-10-01T22:14:10Z'
categories:
    - tech
    - howto
excerpt: Every now and then you feel overconfident and decide that a full reinstall of your whole system is in order. It always takes way more time than you anticipated, but in the end you’re left with something better (in the computer), and you understand the world a little bit better yourself.
toc: false
tags:
    - neovim
    - vim
    - python
    - ide
original_post_medium_url: https://claude-e-e.medium.com/setup-neovim-as-python-ide-with-virtualenvs-e507190d2655
header:
    teaser: /assets/images/2020/10/01/vim-as-ide.png
---
Every now and then you feel overconfident and decide that a full reinstall of your whole system is in order. It always takes way more time than you anticipated, but in the end you’re left with something better (in the computer), and you understand the world a little bit better yourself.

A large challenge every time is to get (neo)vim setup in _just_ the right way to work as a full fledged Python IDE (or, it should be noted that vim was never designed to be an IDE; however we want to at least set it up as a Python development system). One of the major things I struggle with is how to separate all the (python-)pieces. It’s very tempting to just install everything in global scope somewhere, but since in that case you’re using one scope for your tools _and_ the code that you’re writing, this is asking for problems (in addition, it’s generally a bad idea to put everything together in a global scope).

{% include figure
    image_path="/assets/images/2020/10/01/vim-as-ide.png"
    alt="Example of code completion in action"
    caption="Example of code completion in action"
%}

This blog is as much a description for me to read again next time I do a reinstall, as well as a helping hand in understanding the intricacies for others. I’m using a MacBook with MacOs 10.15.7, iTerm (3.3.12) with solarized-dark theme, zsh (5.8) and neovim (0.4.4) — I would expect things to work pretty much the same for linux / bash / (not too sure about vim8). Note: this is not a beginners guide and it’s assumed you know your way around bash, vim, python and the config files.

I choose to use the following components:

*   `pyenv` in order to easily switch between python versions (installing the latest python is relatively easy using homebrew, but if you ever want to install an older python version, or have multiple at the same time, `pyenv` is the way to go.
*   `python -m venv` to manage my virtual envs. Note that this only works for newer python versions (>3.6 iirc). It should be just as easy to use something like `virtualenv` to support older versions.
*   `coc.vim` with `coc-python` extension.
*   `vim-plug` as vim plugin manager
*   `jedi` for code completion ( `coc-python` gives the choice between `jedi` and `MSPL` ; which I assume stands for MicroSoft Python Languageserver). I have not been able to find a good description of the difference between these 2 advantages and disadvantages of both, but considering that `jedi` is written by a guy who asks the occasional beer in return (and I have been an contributor to the project in the past), as opposed to a multi-dollar-corporation, I choose `jedi` ). I want `jedi` to be installed in its own virtual environment.
*   `pylint` for linting. I’ve always used `flake8` for linting, and I kept running into small but irritating issues. One actually led to a [stackoverflow question today](https://stackoverflow.com/questions/64155860/better-alternative-to-flake8s-e902-tokenerror-eof-in-multi-line-statement/), after which some back and forth on gitlab with the maintainer seems to have resolved it, but in general I always was a bit unhappy with how `flake8` seems to throw all errors on 1 big stack: It does have `Exxx` and `Wxxx` codes, supposedly for errors and warnings, but both a syntax error in my code and a line that is 1 character to long are an error. This means that in vim, while I’m just hacking away, I constantly see "errors" because of line-length (and therefore don’t see the real errors). Obviously my choice from `pylint` may be a case of the grass being greener on the other side, and I may change again in the future (it does seem to be slower than `flake8`). For now, I want `pylint` , obviously in it’s own virtualenv.
*   `black` for code formatting. Haven’t used it yet, but I like their mentality.

Since neovim also needs a python interpreter that has the `neovim` python package installed, in total we require 4 virtual environments (in addition to the one we’re coding in).

First thing is using homebrew to install the stuff you need (we need to install `node` for `coc.vim` to work:

    $ brew install neovim pyenv node

Install python versions, and make 3.8.5 the default python version.

```
$ pyenv install 3.8.5  
....  
$ pyenv global 3.8.5  
....  
```  

Make the virtual envs for `jedi`, `black`, `neovim` and `pylint` and install the tools (creating a `venv` directly activates it, so no need to separately activate it). Note that `pylint` does not behave well with virtual envs, and for instance when checking imports, it will check again the `pylint` virtual env, not the active virtualenv. In order to resolve that, we need an extra package: `pylint-venv`.

```
$ python -m venv ~/venvs/jedi && source ~/venvs/jedi/bin/activate && pip install jedi

$ python -m venv ~/venvs/neovim && source ~/venvs/neovim/bin/activate && pip install neovim

$ python -m venv ~/venvs/black && source ~/venvs/black/bin/activate && pip install black

$ python -m venv ~/venvs/pylint && source ~/venvs/pylint/bin/activate && pip install pylint pylint-venv
```

We also need to install `yarn`, since this is used to build the `coc` extensions (because we install them through `vim-plug` rather than the `CocInstall` command; I prefer to have the list there in my `init.vim` file rather than in some magic spot). Since I don’t develop much in node, I’m happy installing `yarn` globally, however I can imagine that one would want to separate that into some virtual env as well.

    $ npm install -g yarn

And finally, we install `vim-plug` (please see [https://github.com/junegunn/vim-plug](https://github.com/junegunn/vim-plug) for how to do this).

```vim
The important part of my `init.vim` file:

call plug#begin('~/.vim/plugged')

" Make sure you use single quotes  
Plug 'neoclide/coc.nvim', {'branch': 'release'}  
Plug 'neoclide/coc-python', {'do': 'yarn install --frozen-lockfile'}  
Plug 'neoclide/coc-tabnine', {'do': 'yarn install --frozen-lockfile'}  
Plug 'neoclide/coc-yaml', {'do': 'yarn install --frozen-lockfile'}  
Plug 'neoclide/coc-json', {'do': 'yarn install --frozen-lockfile'}  
" Initialize plugin system  
call plug#end()

runtime coc-init.vim
```

where `coc-init.vim` is the interesting parts of the example `init.vim` file here: [https://github.com/neoclide/coc.nvim](https://github.com/neoclide/coc.nvim).

Afterwards `:PlugInstall` installs the plug, including all the coc extensions. The `coc-settings.json` file in the same directory looks like this:

```json
{  
    // python  
    "python.pythonPath": "python",  
    "python.venvPath": "~/venvs/",

    // jedi  
    "python.jediPath": "~/venvs/jedi/lib/python3.8/site-packages/",  
    "python.jediEnabled": true,  
    "suggest.timeout": 5000,

    //formatting  
    "python.formatting.provider": "black",  
    "python.formatting.blackPath": "~/venvs/black/bin/black",

    //linting  
    "python.linting.pylintEnabled": true,  
    "python.linting.flake8Enabled": false,  
    "python.linting.pylintPath": "~/venvs/pylint/bin/pylint"  
}
```

Finally (thanks to [Cyprian Guerra](https://medium.com/u/b9fc185d4907) for pointing out the omission), we need to make sure that neovim actually knows to use the python version in the neovim venv, so in `init.nvim`, we add the line:

    let g:python3_host_prog="~/venvs/neovim/bin/python"

(Personally I cannot be bothered with python2, but if you need that too, make a new venv with python2 and neovim, and add a `let g:python_host_prog=...` line to point to that).

Some notes:

*   I’m not 100% sure what the `python.venvPath` does in this case.
*   I have `suggest.timeout` at 5 seconds (5000ms). This is because sometimes I work in very large projects and `jedi` can be a bit slow then.
*   Note that all paths / links to executables point to their own `venv`s. This means that the linter/formatter will be executed in their `venv`, even though the `VIRTUAL_ENV` environment variable will not be touched. For `black` this does not seem to be a problem (however I haven’t tested this 100% yet), `pylint` will complain that it cannot find imports that are in the `venv` that we’re developing in (that `neovim` runs in) rather than in the `pylint` `venv`. The solution for this is to create a `pylintrc` file with the following text (an easy way to generate a `pylintrc` file is through `/Users/username/venvs/pylint/bin/pylint --generate-rcfile > ~/.config/pylintrc` ):

```toml
[MASTER]
init-hook=  
    import pylint_venv  
    pylint_venv.inithook(force_venv_activation=True)
```

An alternative would be to add the init-hook to `python.linting.pylintArgs` in the `coc-settings.json` file.

This setup has been tested with activating the virtual env in which one wants to work _before_ starting `neovim`. I have not tested how it interoperates with tools that change the virtual env from within vim.
