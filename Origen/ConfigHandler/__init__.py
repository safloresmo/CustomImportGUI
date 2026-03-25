import configparser
from pathlib import Path
import logging


class ConfigHandler:
    def __init__(self, config_path):
        self.config = configparser.ConfigParser()
        self.config_path = config_path
        self.config_is_set = False

        self.defaults = {
            "SRC_PATH": str(Path.home() / "Downloads"),
            "DEST_PATH": str(Path.home() / "KiCad"),
            "library_name": "CustomLibrary",
            "library_variable": "${CUSTOM_LIBRARY}",
        }

        # Predefined profiles (paths relative to user's home)
        self.predefined_profiles = {
            "MictlanTeam": {
                "SRC_PATH": str(Path.home() / "Downloads"),
                "DEST_PATH": str(Path.home() / "Documents" / "KiCad" / "MictlanTeam-Library"),
                "library_name": "MictlanTeam",
                "library_variable": "${Mictlan_Team}",
            },
            "CustomLibrary": {
                "SRC_PATH": str(Path.home() / "Downloads"),
                "DEST_PATH": str(Path.home() / "Documents" / "KiCad" / "CustomLibrary"),
                "library_name": "CustomLibrary",
                "library_variable": "${CUSTOM_LIBRARY}",
            },
        }

        try:
            if self.config.read(self.config_path):
                if "config" not in self.config:
                    self.config.add_section("config")

                for key, default_value in self.defaults.items():
                    if (
                        key not in self.config["config"]
                        or not self.config["config"][key]
                    ):
                        self.config["config"][key] = default_value

                self.config_is_set = True
                self._initialize_predefined_profiles()
            else:
                self._create_default_config()
        except Exception as e:
            logging.error(f"Error when reading in the configuration: {e}")
            self._create_default_config()

        if not self.config_is_set:
            self.save_config()

    def _create_default_config(self):
        self.config = configparser.ConfigParser()
        self.config.add_section("config")

        for key, value in self.defaults.items():
            self.config["config"][key] = value

        self.config_is_set = False
        self._initialize_predefined_profiles()

    def get_SRC_PATH(self):
        return self.config["config"]["SRC_PATH"]

    def set_SRC_PATH(self, var):
        self.config["config"]["SRC_PATH"] = var
        self.save_config()

    def get_DEST_PATH(self):
        return self.config["config"]["DEST_PATH"]

    def set_DEST_PATH(self, var):
        self.config["config"]["DEST_PATH"] = var
        self.save_config()

    def get_value(self, key, section="config"):
        try:
            return self.config[section][key]
        except KeyError:
            return None

    def set_value(self, key, value, section="config"):
        if section not in self.config:
            self.config.add_section(section)

        self.config[section][key] = value
        self.save_config()

    def save_config(self):
        try:
            with open(self.config_path, "w") as configfile:
                self.config.write(configfile)
        except Exception as e:
            logging.error(f"Error saving the configuration: {e}")

    # Profile management methods
    def _initialize_predefined_profiles(self):
        """Initialize predefined profiles in config if they don't exist."""
        for profile_name, profile_data in self.predefined_profiles.items():
            section_name = f"profile_{profile_name}"
            if section_name not in self.config:
                self.config.add_section(section_name)
                for key, value in profile_data.items():
                    self.config[section_name][key] = value
        self.save_config()

    def get_available_profiles(self):
        """Get list of available profile names."""
        profiles = []
        for section in self.config.sections():
            if section.startswith("profile_"):
                profile_name = section.replace("profile_", "")
                profiles.append(profile_name)
        return profiles

    def load_profile(self, profile_name):
        """Load a profile and apply its settings."""
        section_name = f"profile_{profile_name}"
        if section_name not in self.config:
            logging.error(f"Profile '{profile_name}' not found")
            return False

        try:
            # Load all settings from profile
            self.config["config"]["SRC_PATH"] = self.config[section_name]["SRC_PATH"]
            self.config["config"]["DEST_PATH"] = self.config[section_name]["DEST_PATH"]
            self.config["config"]["library_name"] = self.config[section_name]["library_name"]
            self.config["config"]["library_variable"] = self.config[section_name]["library_variable"]
            self.config["config"]["current_profile"] = profile_name
            self.save_config()
            logging.info(f"Profile '{profile_name}' loaded successfully")
            return True
        except Exception as e:
            logging.error(f"Error loading profile '{profile_name}': {e}")
            return False

    def save_current_as_profile(self, profile_name):
        """Save current settings as a new profile."""
        section_name = f"profile_{profile_name}"

        # Create section if it doesn't exist
        if section_name not in self.config:
            self.config.add_section(section_name)

        # Save current settings
        self.config[section_name]["SRC_PATH"] = self.config["config"]["SRC_PATH"]
        self.config[section_name]["DEST_PATH"] = self.config["config"]["DEST_PATH"]
        self.config[section_name]["library_name"] = self.config["config"]["library_name"]
        self.config[section_name]["library_variable"] = self.config["config"]["library_variable"]

        self.save_config()
        logging.info(f"Profile '{profile_name}' saved successfully")
        return True

    def delete_profile(self, profile_name):
        """Delete a profile (predefined profiles cannot be deleted)."""
        if profile_name in self.predefined_profiles:
            logging.warning(f"Cannot delete predefined profile '{profile_name}'")
            return False

        section_name = f"profile_{profile_name}"
        if section_name in self.config:
            self.config.remove_section(section_name)
            self.save_config()
            logging.info(f"Profile '{profile_name}' deleted successfully")
            return True
        else:
            logging.error(f"Profile '{profile_name}' not found")
            return False

    # Library configuration methods
    def get_library_name(self):
        """Get the library name."""
        return self.config["config"].get("library_name", "CustomLibrary")

    def set_library_name(self, name):
        """Set the library name."""
        self.config["config"]["library_name"] = name
        self.save_config()

    def get_library_variable(self):
        """Get the library environment variable."""
        return self.config["config"].get("library_variable", "${CUSTOM_LIBRARY}")

    def set_library_variable(self, variable):
        """Set the library environment variable."""
        self.config["config"]["library_variable"] = variable
        self.save_config()

    def get_current_profile(self):
        """Get the currently active profile name."""
        return self.config["config"].get("current_profile", "")

    def set_current_profile(self, profile_name):
        """Set the currently active profile name."""
        self.config["config"]["current_profile"] = profile_name
        self.save_config()
