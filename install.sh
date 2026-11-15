#!/bin/bash

# --- Colors and Text Formatting ---
GREEN=$(tput setaf 2)
CYAN=$(tput setaf 6)
YELLOW=$(tput setaf 3)
RESET=$(tput sgr0)
BOLD=$(tput bold)

# --- Spinner Animation Function ---
spinner() {
    local pid=$1
    local delay=0.1
    local spinstr='|/-\'
    while [ "$(ps a | awk '{print $1}' | grep $pid)" ]; do
        local temp=${spinstr#?}
        printf " [%c]  " "$spinstr"
        local spinstr=$temp${spinstr%"$temp"}
        sleep $delay
        printf "\b\b\b\b\b\b"
    done
    printf "    \b\b\b\b"
}

print_step() {
    echo -e "${CYAN}${BOLD}[*] $1...${RESET}"
}

print_success() {
    echo -e "${GREEN}${BOLD}[+] $1!${RESET}"
}

clear
echo -e "${YELLOW}${BOLD}"
echo "================================================="
echo "      🚀 SheerID Bot Environment Setup 🚀      "
echo "================================================="
echo -e "${RESET}"

# --- 1. Check and Install Google Chrome ---
print_step "Checking for Google Chrome"
if command -v google-chrome &> /dev/null || command -v google-chrome-stable &> /dev/null; then
    print_success "Google Chrome is already installed"
else
    echo -e "${YELLOW}[!] Google Chrome not found. Installing...${RESET}"
    # Downloads and installs Chrome via apt as specified in the project requirements
    (
        wget -q -O google-chrome.deb "https://dl.google.com/linux/direct/google-chrome-stable_current_$(dpkg --print-architecture).deb"
        sudo apt update -y -qq
        sudo apt install -y -qq "./google-chrome.deb"
        rm google-chrome.deb
    ) > /dev/null 2>&1 &
    spinner $!
    print_success "Google Chrome installed successfully"
fi

# --- 2. Create Python Virtual Environment ---
print_step "Creating Python virtual environment (venv)"
if [ ! -d "venv" ]; then
    (python3 -m venv venv) > /dev/null 2>&1 &
    spinner $!
    print_success "Virtual environment created"
else
    print_success "Virtual environment already exists"
fi

# --- 3. Install Dependencies ---
print_step "Installing required Python packages"
# Installs all necessary libraries for the bot to run including undetected-chromedriver
(
    source venv/bin/activate
    pip install --upgrade pip -q
    pip install undetected-chromedriver selenium requests python-telegram-bot python-dotenv pyvirtualdisplay -q
) > /dev/null 2>&1 &
spinner $!
print_success "All dependencies installed"

echo ""
echo -e "${GREEN}${BOLD}=================================================${RESET}"
echo -e "${GREEN}${BOLD}          SETUP COMPLETED SUCCESSFULLY           ${RESET}"
echo -e "${GREEN}${BOLD}=================================================${RESET}"
echo ""
echo -e "${CYAN}To activate the environment and run your script, copy and paste this command:${RESET}"
echo ""
echo -e "${YELLOW}${BOLD}source venv/bin/activate && python SheerID.py${RESET}"
echo ""