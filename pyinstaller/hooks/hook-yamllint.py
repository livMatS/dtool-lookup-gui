from PyInstaller.utils.hooks import collect_data_files

# Collect yamllint's data files, which include the default configuration
datas = collect_data_files('yamllint')