set shell := ["bash", "-euo", "pipefail", "-c"]

fonts_css := "https://fonts.googleapis.com/css2?family=Archivo:wght@500;600;700&family=Newsreader:opsz,wght@6..72,300;6..72,400;6..72,500&family=IBM+Plex+Mono:wght@400;500;600&display=swap"
ua := "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# Liste les recettes disponibles.
default:
    @just --list

# Installe les prérequis : Ruby/Bundler, gems Jekyll, polices locales.
init:
    @echo "==> Vérification des outils"
    @command -v curl >/dev/null || { echo "manquant : curl"; exit 1; }
    @command -v ruby >/dev/null || { echo "manquant : ruby (apt install ruby-full build-essential zlib1g-dev)"; exit 1; }
    @echo "    curl $(curl --version | head -1 | cut -d' ' -f2)"
    @echo "    ruby $(ruby -e 'print RUBY_VERSION')"

    @echo "==> Bundler"
    @command -v bundle >/dev/null || gem install --user-install --no-document bundler
    @command -v bundle >/dev/null || echo "    ajoutez $(ruby -e 'print Gem.user_dir')/bin à votre PATH"

    @echo "==> Installation des gems (vendor/bundle)"
    @bundle config set --local path vendor/bundle
    @bundle install

    @just fonts
    @echo "==> Prêt. Lancez : just serve"

# Télécharge les polices dans assets/fonts pour un rendu hors ligne.
fonts:
    @echo "==> Polices (Archivo, Newsreader, IBM Plex Mono)"
    @mkdir -p assets/fonts
    @curl -sSfL -A "{{ua}}" "{{fonts_css}}" -o assets/fonts/fonts.css
    @grep -o 'https://fonts.gstatic.com/[^)]*' assets/fonts/fonts.css | sort -u | while read -r url; do \
        curl -sSfL -o "assets/fonts/$(basename "$url")" "$url"; \
    done
    @sed -i 's|https://fonts\.gstatic\.com/[^)]*/||g' assets/fonts/fonts.css
    @echo "    $(ls assets/fonts/*.woff2 2>/dev/null | wc -l) fichiers de police"

# Sert le rapport sur http://localhost:PORT (par défaut 4000).
serve port="4000":
    @bundle exec jekyll serve --host 127.0.0.1 --port {{port}} --livereload

# Construit le site statique dans _site/, tel que GitHub Pages le publiera.
build:
    @bundle exec jekyll build
    @echo "==> _site/ prêt"

# Régénère report.body.html, le fragment publié comme Artifact Claude.
artifact:
    @./build-artifact.sh

# Supprime les fichiers générés, les gems et les polices téléchargées.
clean:
    @rm -rf _site .jekyll-cache vendor assets/fonts
    @echo "==> Nettoyé (les sources _includes/ sont conservées)"
