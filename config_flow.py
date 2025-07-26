
"""Config flow for Light Controls integration."""
from homeassistant import config_entries
import voluptuous as vol

DOMAIN = "lightcontrols"

class LightControlsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Light Controls."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        if user_input is not None:
            return self.async_create_entry(title="Light Controls", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({}),
            description_placeholders={"info": "This is a placeholder form."},
        )
