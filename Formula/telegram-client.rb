class TelegramClient < Formula
  include Language::Python::Virtualenv

  desc "CLI and real-time listener for Telegram"
  homepage "https://github.com/mainpart/telegram-client"
  head "https://github.com/mainpart/telegram-client.git", branch: "main"

  depends_on "python@3.13"

  def install
    virtualenv_create(libexec, "python3.13")
    system libexec/"bin/pip", "install", "."
    bin.install_symlink libexec/"bin/telegram-cli"
    bin.install_symlink libexec/"bin/telegram-listen"

    bash_completion.install "completions/telegram-cli.bash" => "telegram-cli"
    bash_completion.install "completions/telegram-listen.bash" => "telegram-listen"
    zsh_completion.install "completions/_telegram-cli"
    zsh_completion.install "completions/_telegram-listen"
    fish_completion.install "completions/telegram-cli.fish"
    fish_completion.install "completions/telegram-listen.fish"
  end

  test do
    system bin/"telegram-cli", "--help"
  end
end
