# .bash_profile

# Get the aliases and functions
# if [ -f ~/.bashrc ]; then
#         . ~/.bashrc
# fi

# User specific environment and startup programs

parse_git_branch() {
        git branch 2> /dev/null | sed -e '/^[^*]/d' -e 's/* \(.*\)/(\1)/'
}

PATH=$PATH:$HOME/.local/bin:$HOME/bin

export PATH
source /usr/local/.mde-user/.nvm/nvm.sh
export PATH="$PATH:$HOME/.dotnet/tools"

GIT="\[\e[1;37;43m\]"
GIT_TRIANGLE="\[\e[0;33;42m\]"
BEGIN="\[\e[1;37;42m\]"
BEGIN_TRIANGLE="\[\e[0;32;46m\]"
TIME="\[\e[1;37;46m\]"
TIME_TRIANGLE="\[\e[0;36;47m\]"
MIDDLE="\[\e[0;37;47m\]"
MIDDLE_TRIANGLE="\[\e[0;37m\]"
END="\[\e[m\]"
export PS1="${GIT} $(parse_git_branch) ${GIT_TRIANGLE}${BEGIN} \u ${BEGIN_TRIANGLE} ${TIME}\t+09:00 ${TIME_TRIANGLE}${MIDDLE} \W ${MIDDLE_TRIANGLE}${END} "
