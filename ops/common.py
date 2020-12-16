def download_file(
    storage_account: str, container_name: str, file_name: str, dest_path: str
) -> int:

    result = subprocess.run(
        "az storage blob exists --account-name {storage_account} --container-name {container_name} --name {file_name} -o tsv".split(),
        capture_output=True,
    )
    if result.stdout == "False":
        echo(f"{file_name} not found")
        raise FileNotFoundError(file_name)

    result = subprocess.run(
        f"az storage blob download --account-name {storage_account} --container-name {container_name} --name {file_name} -f {dest_path} --no-progress".split(),
        text=True,
        capture_output=True,
    )

    if result.returncode != 0:
        echo(result.stdout)
        echo(result.stderr)
        echo("Could not find the target file in the storage account.")
        echo(f"You need to upload {file_name} manually to the storage account.")
        raise FileNotFoundError(file_name)

    if not os.stat(dest_path).st_size:
        echo("Could not find the target file in the storage account.")
        echo(f"You need to upload {file_name} manually to the storage account.")
        raise FileNotFoundError(dest_path)

    return result.returncode
