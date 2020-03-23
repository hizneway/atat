# bootstrap_functions.inc.sh: Functions used by the bootstrap script

install_python_packages() {
  local install_flags="${1}"

  poetry install ${install_flags}
  return $?
}

install_node_packages() {
  yarn install
  return $?
}
