## vim-config

### Start with installing zsh, oh-my-zsh and all its plugins.

I. **install zsh**

```bash
sudo apt install zsh
```

II. **install oh-my-zsh**  

```bash
sh -c "$(curl -fsSL https://raw.github.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"
```

or check the website of oh-my-zsh: [link](https://ohmyz.sh/#install)  

III. **install zsh plugins**  

```bash
# Auto-suggestion
git clone https://github.com/zsh-users/zsh-autosuggestions ~/.zsh/plugins/zsh-autosuggestions

# syntax highlighting
git clone https://github.com/zsh-users/zsh-syntax-highlighting ~/.zsh/plugins/zsh-syntax-highlighting
```

IV. **add plugins in .zshrc**  

```bash
ZSH_THEME="wedisagree"

source ~/.zsh/plugins/zsh-autosuggestions/zsh-autosuggestions.zsh
source ~/.zsh/plugins/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh

autoload -U colors && colors

setopt prompt_subst

PROMPT='❰%{$fg[green]%}%n%{$reset_color%}|%{$fg[yellow]%}%1~%{$reset_color%}%{$fg[blue]%}$(git branch --show-current 2&> /dev/null | xargs -I branch echo "(branch)")%{$reset_color%}❱ '

plugins=(
   git
   zsh-autosuggestions
   zsh-syntax-highlighting
)
```

V. **install power** [github](https://github.com/romkatv/powerlevel10k)

```bash
# Manual
git clone --depth=1 https://github.com/romkatv/powerlevel10k.git ~/powerlevel10k
echo 'source ~/powerlevel10k/powerlevel10k.zsh-theme' >>~/.zshrc

# oh-my-zsh
git clone --depth=1 https://github.com/romkatv/powerlevel10k.git ${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}/themes/powerlevel10k

# restart zsh and run:
# p10k configure
```

### Start installing vim's plugins and customize vim

I. vim-plug [github](https://github.com/junegunn/vim-plug)

```bash
# install vim-plug
curl -fLo ~/.vim/autoload/plug.vim --create-dirs \
    https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim
```

II. Write these to .vimrc

```bash

```

