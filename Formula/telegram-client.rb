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

    bash_completion.install "completions/telegram-cli.bash" => "telegram-cli"
    zsh_completion.install "completions/_telegram-cli"
    fish_completion.install "completions/telegram-cli.fish"
  end

  test do
    system bin/"telegram-cli", "--help"
  end
end
