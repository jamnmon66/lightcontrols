"""Custom integration for lightcontrols."""

import logging
import yaml
from pathlib import Path
from datetime import datetime
from jinja2 import Environment, FileSystemLoader

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.components.persistent_notification import async_create

_LOGGER = logging.getLogger(__name__)

CONFIG_PATH = Path("/config/packages/lightcontrols")
LIGHTS_CONFIG_PATH = Path(__file__).parent / "lights.yaml"
TEMPLATE_DIR = Path(__file__).parent / "templates"

env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))

async def generate_lightcontrol_files(hass: HomeAssistant) -> bool:
    """Generate YAML files and return whether any files changed."""
    lights_yaml = await hass.async_add_executor_job(LIGHTS_CONFIG_PATH.read_text)
    lights = yaml.safe_load(lights_yaml)
    _LOGGER.warning("Loaded lightcontrols config from %s", LIGHTS_CONFIG_PATH)

    any_changes = False

    for light in lights:
        room = light["room"]
        location = light["location"]
        real_entity = light["entity"]
        auto_entity = light.get("auto_entity", "input_number.light_controls_brightness_setting")

        if room.lower() == "group" or not room or not location:
            continue

        prefix = f"{room}_{location}"
        device_name = prefix.replace("_", " ").title()
        title = f"{room} {location}".replace("_", " ").title()

        _LOGGER.warning("Rendering templates for light: %s", prefix)

        output_dir = CONFIG_PATH / room / location
        output_dir.mkdir(parents=True, exist_ok=True)

        expected_files = set()

        for template_file in TEMPLATE_DIR.glob("*.j2"):
            domain = template_file.stem
            filename = f"{prefix}_{domain}.yaml"
            output_path = output_dir / filename
            expected_files.add(filename)

            template = await hass.async_add_executor_job(env.get_template, template_file.name)
            rendered = template.render(
                room=room,
                location=location,
                prefix=prefix,
                real_entity=real_entity,
                auto_entity=auto_entity,
                device_name=device_name,
                title=title,
            )

            existing = ""
            if output_path.exists():
                existing = await hass.async_add_executor_job(output_path.read_text)

            if rendered.strip() != existing.strip():
                await hass.async_add_executor_job(output_path.write_text, rendered)
                _LOGGER.warning("Wrote %s", output_path)
                any_changes = True

        # Cleanup obsolete files
        for file in output_dir.glob("*.yaml"):
            if file.name not in expected_files:
                await hass.async_add_executor_job(file.unlink)
                _LOGGER.warning("Removed obsolete file: %s", file)
                any_changes = True

        # Check for created_on MQTT topic state
        created_on_entity = f"sensor.{prefix}_created_on"
        created_state = hass.states.get(created_on_entity)

        if not created_state or created_state.state in ["unknown", "unavailable", ""]:
            try:
                _LOGGER.warning("Running reset_all_%s_topics due to missing created_on", prefix)
                await hass.services.async_call(
                    "script",
                    f"reset_all_{prefix}_topics",
                    blocking=True
                )
                timestamp = datetime.now().isoformat()
                await hass.services.async_call(
                    "mqtt",
                    "publish",
                    {
                        "topic": f"lightcontrols/{room}/{location}/created_on",
                        "payload": timestamp,
                        "retain": True,
                    },
                    blocking=True,
                )
                _LOGGER.warning("Published created_on for %s: %s", prefix, timestamp)
            except Exception as e:
                _LOGGER.error("Failed reset or publish created_on for %s: %s", prefix, e)

    return any_changes

async def reload_all_yaml(hass: HomeAssistant):
    """Trigger global YAML configuration reload."""
    try:
        await hass.services.async_call("homeassistant", "reload_all", blocking=True)
        _LOGGER.warning("Triggered full homeassistant.reload_all")
    except Exception as e:
        _LOGGER.error("Failed to call homeassistant.reload_all: %s", e)

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the lightcontrols integration."""
    changed = await generate_lightcontrol_files(hass)
    if changed:
        await reload_all_yaml(hass)

    async def handle_generate_all(call: ServiceCall) -> None:
        _LOGGER.warning("Manual trigger: generate_all service called")
        changed = await generate_lightcontrol_files(hass)
        if changed:
            await reload_all_yaml(hass)
            async_create(
                hass,
                "✅ Lightcontrol YAML files regenerated and reloaded.",
                title="Lightcontrols",
                notification_id="lightcontrols_generate_all"
            )
        else:
            async_create(
                hass,
                "⚠️ No changes in generated files. Reload skipped.",
                title="Lightcontrols",
                notification_id="lightcontrols_generate_all"
            )

    hass.services.async_register("lightcontrols", "generate_all", handle_generate_all)
    return True
