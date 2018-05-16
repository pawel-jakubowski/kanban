pkgdatadir = join_paths(get_option('prefix'), get_option('datadir'), meson.project_name())
moduledir = join_paths(pkgdatadir, 'kanban')
gnome = import('gnome')

gnome.compile_resources('kanban',
  'kanban.gresource.xml',
  gresource_bundle: true,
  install: true,
  install_dir: pkgdatadir,
)

python3 = import('python3')

conf = configuration_data()
conf.set('PYTHON', python3.find_python().path())
conf.set('VERSION', meson.project_version())
conf.set('localedir', join_paths(get_option('prefix'), get_option('localedir')))
conf.set('pkgdatadir', pkgdatadir)

configure_file(
  input: 'kanban.in',
  output: 'kanban',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir')
)

kanban_sources = [
  'importer/trello_importer.py',
  'model/Board.py',
  'model/Task.py',
  'model/TaskList.py',
  'view/BoardListView.py',
  'view/BoardView.py',
  'view/KanbanListView.py',
  'view/NewTask.py',
  'view/TaskListView.py',
  'view/TaskView.py',
  'view/TextEntry.py',
  '__init__.py',
  'gi_composites.py',
  'main.py',
  'settings.py',
  'window.py',
]

install_data(kanban_sources, install_dir: moduledir)
