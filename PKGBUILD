# Maintainer: Your Name <youremail@example.com>
pkgname=whisper-wayland
pkgver=0.1.0
pkgrel=1
pkgdesc="Native, on-device voice-to-text pipeline for Arch Linux (Wayland/X11)"
arch=('any')
url="https://github.com/jrufer/whisper-wayland"
license=('MIT')
depends=('python' 'python-pyqt6' 'python-evdev' 'portaudio' 'wl-clipboard')
optdepends=('python-faster-whisper: for the transcription engine')
source=("whisper-wayland.desktop" "99-whisper-wayland.rules")
sha256sums=('SKIP' 'SKIP')

package() {
    mkdir -p "$pkgdir/opt/whisper-wayland"
    cp -r "$srcdir/../src/"* "$pkgdir/opt/whisper-wayland/"
    
    # Install desktop entry
    install -Dm644 "$srcdir/whisper-wayland.desktop" "$pkgdir/usr/share/applications/whisper-wayland.desktop"
    
    # Install udev rules
    install -Dm644 "$srcdir/99-whisper-wayland.rules" "$pkgdir/usr/lib/udev/rules.d/99-whisper-wayland.rules"
}
