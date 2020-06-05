#!/bin/bash
create_db_extension() {
  local database_name="${1}"
  local extension_name="${2}"

  if [ -z "${database_name}"  ]; then
    local database_name="atat"
  fi

  if [ -z "${extension_name}"  ]; then
    local extension_name="uuid-ossp"
  fi

	echo "Creating ${extension_name} in ${database_name}"
  psql "${database_name}" -c "CREATE EXTENSION IF NOT EXISTS \"${extension_name}\""
}

if [  "$(caller)" = "0 NULL"  ]; then
  # will only run if you actually call this script rather than source it
  create_db_extension "${1}" "${2}"
fi


