from PyInstaller.utils.hooks import collect_entry_point, copy_metadata

# storage brokers and their entrypoints need the following special treatment,
# as they won't be discovered by pyinstaller's default tracing mechanisms
dtool_hidden_imports = ['dtool_http', 'dtool_smb', 'dtool_s3', 'dtool_symlink']
dtool_hidden_imports_datas = []
for module in dtool_hidden_imports:
    # recursive copy_metadata needed local reinstall of
    #    $ pip install --ignore-installed six
    # in minsys2/,ingw64, would otherwise fail with
    #    RuntimeError: No metadata path found for distribution 'six'.
    dtool_hidden_imports_datas.extend(copy_metadata(module, recursive=True))

dtool_storage_brokers_datas, dtool_storage_brokers_hidden_imports = collect_entry_point("dtool.storage_brokers")

datas = [*dtool_hidden_imports_datas, *dtool_storage_brokers_datas]
hiddenimports = [*dtool_hidden_imports, *dtool_storage_brokers_hidden_imports]