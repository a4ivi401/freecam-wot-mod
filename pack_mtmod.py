import os
import py_compile
import sys
import zipfile

MOD_NAME = 'f1nder_FreeCam'
ENTRYPOINT = 'mod_FreeCam_Hangar_and_Replays.py'
ICON_PATH = 'res/gui/maps/icons/FreeCam.png'
META_PATH = 'meta.xml'
PACKAGE_ENTRYPOINT = 'res/scripts/client/gui/mods/mod_FreeCam_Hangar_and_Replays.pyc'


def _require_file(path):
    if not os.path.isfile(path):
        raise IOError('Required file not found: {0}'.format(path))


def pack_mod(version):
    mod_filename = '{0}_{1}.mtmod'.format(MOD_NAME, version)
    compiled_entrypoint = ENTRYPOINT + 'c'

    _require_file(META_PATH)
    _require_file(ICON_PATH)
    _require_file(ENTRYPOINT)

    py_compile.compile(ENTRYPOINT, cfile=compiled_entrypoint, doraise=True)

    try:
        print 'Packing mod to', mod_filename

        with zipfile.ZipFile(mod_filename, 'w', zipfile.ZIP_STORED) as z:
            z.write(META_PATH, 'meta.xml')
            z.write(ICON_PATH, ICON_PATH)
            z.write(compiled_entrypoint, PACKAGE_ENTRYPOINT)

        print 'Mod packed successfully!'
    finally:
        if os.path.isfile(compiled_entrypoint):
            os.remove(compiled_entrypoint)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        raise SystemExit('Usage: pack_mtmod.py <version>')
    pack_mod(sys.argv[1])
