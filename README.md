# Light Controls

A Home Assistant custom integration for auto-generating light control configurations using Jinja2 templates.

This tool reads a `lights.yaml` input file and dynamically generates per-room YAML packages with MQTT, automation, script, and template configuration for Home Assistant.

---

## 🚀 Features

- Generates output YAML files to `/config/packages/lightcontrols/<room>/<location>/`
- Supports:
  - MQTT topic mapping
  - Effect and brightness automations
  - Custom naming and device labeling
- Includes `generate_all` service to re-render and reload config on demand
- Retains Home Assistant compatibility and reloads only changed domains

---

## 🛠 Installation

1. Copy the `custom_components/lightcontrols/` folder into your Home Assistant config.
2. Define lights in `custom_components/lightcontrols/lights.yaml`.
3. Add or customize Jinja2 templates under `templates/`.
4. Restart Home Assistant.

---

## 🧪 Usage

- Call the service: `lightcontrols.generate_all`
- This will:
  - Read your light definitions
  - Generate any changed YAML files
  - Clean up obsolete files
  - Optionally call scripts and MQTT publish as needed
  - Show a persistent toast in the UI after completion

---

## 📁 File Structure
custom_components/lightcontrols/
├── init.py
├── config_flow.py
├── manifest.json
├── services.yaml
├── lights.yaml
├── icon.png
└── templates/
└── *.j2 (Jinja templates for automation, scripts, etc.)



---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

## 🙌 Contributing

PRs are welcome. Please ensure templates and logic match Home Assistant YAML format expectations and preserve structure when modifying.
