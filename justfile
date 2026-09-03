set shell := ["bash", "-euo", "pipefail", "-c"]

fonts_css := "https://fonts.googleapis.com/css2?family=Archivo:wght@500;600;700&family=Newsreader:opsz,wght@6..72,300;6..72,400;6..72,500&family=IBM+Plex+Mono:wght@400;500;600&display=swap"
ua := "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
# Invoke Bundler through Ruby so the recipes also work when the `bundle`
# executable is not on PATH (common with distro-provided Ruby installs).
bundle := "ruby -rbundler -e 'exec Gem.bin_path(\"bundler\", \"bundle\"), *ARGV' --"

# List the available recipes.
default:
    @just --list

# Install the operating-system and project dependencies.
init:
    @echo "==> Checking system dependencies"
    @if ! command -v curl >/dev/null || ! command -v ruby >/dev/null || ! ruby -rrbconfig -e 'header = File.join(RbConfig::CONFIG.fetch("rubyhdrdir"), "ruby.h"); exit File.file?(header) ? 0 : 1'; then \
        command -v apt-get >/dev/null || { echo "Missing system dependencies. Install curl, ruby-full, ruby-dev, build-essential, and zlib1g-dev with your package manager."; exit 1; }; \
        echo "==> Installing system dependencies (sudo required)"; \
        sudo apt-get update; \
        sudo apt-get install -y curl ruby-full ruby-dev build-essential zlib1g-dev; \
    fi
    @echo "    curl $(curl --version | head -1 | cut -d' ' -f2)"
    @echo "    ruby $(ruby -e 'print RUBY_VERSION')"

    @echo "==> Bundler"
    @ruby -rbundler -e 'puts "    bundler #{Bundler::VERSION}"' || gem install --user-install --no-document bundler

    @echo "==> Installing Ruby gems (vendor/bundle)"
    @{{bundle}} config set --local path vendor/bundle
    @{{bundle}} install

    @just fonts
    @echo "==> Ready. Run: just serve"

# Download fonts to assets/fonts for offline rendering.
fonts:
    @echo "==> Fonts (Archivo, Newsreader, IBM Plex Mono)"
    @mkdir -p assets/fonts
    @curl -sSfL -A "{{ua}}" "{{fonts_css}}" -o assets/fonts/fonts.css
    @grep -o 'https://fonts.gstatic.com/[^)]*' assets/fonts/fonts.css | sort -u | while read -r url; do \
        curl -sSfL -o "assets/fonts/$(basename "$url")" "$url"; \
    done
    @sed -i 's|https://fonts\.gstatic\.com/[^)]*/||g' assets/fonts/fonts.css
    @echo "    $(ls assets/fonts/*.woff2 2>/dev/null | wc -l) font files"

# Serve the report at http://localhost:PORT (default: 4000).
serve port="4000":
    @ruby -rrbconfig -e 'header = File.join(RbConfig::CONFIG.fetch("rubyhdrdir"), "ruby.h"); abort "Missing Ruby headers. Run: just init" unless File.file?(header)'
    @{{bundle}} check >/dev/null 2>&1 || { echo "Jekyll dependencies are missing. Run: just init"; exit 1; }
    @{{bundle}} exec jekyll serve --host 127.0.0.1 --port {{port}} --livereload

# Build the static site in _site/, as GitHub Pages will publish it.
build:
    @ruby -rrbconfig -e 'header = File.join(RbConfig::CONFIG.fetch("rubyhdrdir"), "ruby.h"); abort "Missing Ruby headers. Run: just init" unless File.file?(header)'
    @{{bundle}} check >/dev/null 2>&1 || { echo "Jekyll dependencies are missing. Run: just init"; exit 1; }
    @{{bundle}} exec jekyll build
    @echo "==> _site/ is ready"

# Rejouer tous les collecteurs de données publiques (réseau requis).
collecte:
    @for f in scripts/fetch/[a-z]*.py; do echo "==> $f"; python3 "$f" || echo "    (échec, on continue)"; done

# Recalculer les notes sur 10 depuis les _data/*.json collectés.
notes:
    @python3 scripts/notes.py

# Réinjecter _data/criteres.yml dans le bloc JS du rapport.
donnees:
    @python3 scripts/build_donnees.py

# Regénérer la liste d'entreprises d'un bassin d'emploi : grenoble ou montpellier (réseau requis).
candidatures bassin="grenoble":
    @python3 scripts/candidatures_devops.py {{bassin}}
    @python3 scripts/candidatures_markdown.py {{bassin}}

# Regénérer la liste d'employeurs qui recrutent en télétravail intégral (réseau requis, ~3 min).
remote:
    @python3 scripts/candidatures_remote.py
    @python3 scripts/candidatures_remote_markdown.py

# Regenerate report.body.html, the fragment published as a Claude Artifact.
artifact:
    @./build-artifact.sh

# Remove generated files, gems, and downloaded fonts.
clean:
    @rm -rf _site .jekyll-cache vendor assets/fonts
    @echo "==> Cleaned (_includes/ source files were preserved)"
