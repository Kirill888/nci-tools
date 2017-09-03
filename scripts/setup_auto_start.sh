#!/bin/bash

jp_launch_script="${HOME}/.config/autostart/run.d/50-jupyter.sh"
mkdir -p "${HOME}/.config/autostart/run.d"

# this creates gnome auto-start entry that runs scripts
cat << 'EOF' > "${HOME}/.config/autostart/user-scripts.desktop"
[Desktop Entry]
Type=Application
Exec=bash -c 'run-parts "$HOME/.config/autostart/run.d"'
Hidden=false
X-GNOME-Autostart-enabled=true
Name=user-scripts
Comment=Run user startup scripts
EOF

#this creates jupyter launch script
cat << 'EOF' > "${jp_launch_script}"
#!/bin/bash
nb_dir="${HOME}/notebooks"

#cleanup stale notebook files
find "${HOME}/.local/share/jupyter/runtime/" -name 'nbserver-*.json' -delete

module use '/g/data/v10/public/modules/modulefiles'
module load agdc-py3-prod
port=$(shuf -n 1 -i 8300-8400)
mkdir -p "${nb_dir}"

exec nohup jupyter-notebook \
     --notebook-dir="${nb_dir}" \
     --no-browser \
     --ip "${HOSTNAME}" --port "${port}" \
     2>/dev/null >/dev/null </dev/null&
EOF
chmod 755 "${jp_launch_script}"

echo "Created default launch script: ${jp_launch_script}"
echo "You can customize it for your needs"
