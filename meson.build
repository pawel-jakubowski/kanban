project('kanban',
  version: '0.6.6',
  license: 'MIT_X11',
  meson_version: '>= 0.40.0',
)
i18n = import('i18n')


subdir('data')
subdir('src')
subdir('po')

meson.add_install_script('build-aux/meson/postinstall.py')
