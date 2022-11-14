import shutil
from rthemelib.plugins.gnome_shell import constants

import rthemelib.plugin_manager as pm
import rthemelib.theme_classes as tc
import subprocess
import os
import gi

gi.require_version("Gdk", "3.0")
from gi.repository import Gdk

HOME_ = os.path.expanduser('~')
CSS_DIR_ = f"{HOME_}/.config/rtheme/shell"
CSS_FILE_ = f"{CSS_DIR_}/.config/rtheme/shell/shell.css"
DATA_ = os.path.join(os.path.dirname(__file__), "data")
automatic = constants.automatic


class Plugin(pm.Plugin):
    def __init__(self, plugin_manager: pm.PluginManager):
        super().__init__(plugin_manager)
        self.name = "gnome_shell"
        self.description = "A plugin for gnome-shell. Requires sassc and rtheme gnome extension to be enabled."
        self.version = "43"
        self.author = "PizzaLovingNerd"
        self.plugin_properties = list(automatic.keys())

    def on_load(self):  # Runs when the plugin is loaded
        pass

    def purge_theme(self):  # Purges the gnome43.
        if os.path.exists(CSS_DIR_):
            shutil.rmtree(CSS_DIR_)

    def apply_theme(self, subvariant: tc.Subvariant):  # Ran when applying a gnome43.
        self.purge_theme()
        if not os.path.exists(CSS_DIR_):
            os.makedirs(CSS_DIR_)

        # Getting parent variant
        variant = subvariant.parent_variant
        dark_subvariant = variant.get_subvariant_from_name("dark")
        light_subvariant = variant.get_subvariant_from_name("light")
        generated_properties = {}

        # Getting automatic properties
        if dark_subvariant is not None and light_subvariant is None:
            for prop in dark_subvariant.properties:
                if dark_subvariant.properties[prop] is not None:
                    generated_properties[f"{prop}_dark"] = dark_subvariant.properties[prop]
                    generated_properties[f"{prop}_light"] = dark_subvariant.properties[prop]
        elif dark_subvariant is None and light_subvariant is not None:
            for prop in light_subvariant.properties:
                if light_subvariant.properties[prop] is not None:
                    generated_properties[f"{prop}_dark"] = light_subvariant.properties[prop]
                    generated_properties[f"{prop}_light"] = light_subvariant.properties[prop]
        else:
            for prop in dark_subvariant.properties:
                if dark_subvariant.properties[prop] is not None:
                    generated_properties[f"{prop}_dark"] = dark_subvariant.properties[prop]
            for prop in light_subvariant.properties:
                if light_subvariant.properties[prop] is not None:
                    generated_properties[f"{prop}_light"] = light_subvariant.properties[prop]

        # Copying theme-template to directory
        shutil.copytree(
            f"{DATA_}/gnome43",
            CSS_DIR_, dirs_exist_ok=True
        )

        # Updating icons
        # Getting hex for icon color
        icon_color = Gdk.RGBA()
        patch_icons = True
        if "gnome_shell" in subvariant.plugin_properties and \
                "accent_fg_color_dark" in subvariant.plugin_properties["gnome_shell"]:
            icon_color.parse(subvariant.plugin_properties["gnome_shell"]["accent_fg_color_dark"])
        elif "accent_fg_color_dark" in generated_properties:
            icon_color.parse(generated_properties["accent_fg_color_dark"])
        else:
            patch_icons = False

        # Writing patched icons
        if patch_icons:
            for icon in os.listdir(CSS_DIR_):
                if icon.endswith(".svg"):
                    with open(f"{CSS_DIR_}/{icon}", "r") as f:
                        contents = f.read()
                        contents = contents.replace("#3584e4", icon_color.to_string())
                    with open(f"{CSS_DIR_}/{icon}", "w") as f:
                        f.write(contents)

        with open(f"{CSS_DIR_}/gnome-shell-sass/_colors.scss", "r") as f:
            contents = f.read()
            for prop in automatic:
                if "gnome_shell" in subvariant.plugin_properties and \
                        prop in subvariant.plugin_properties["gnome_shell"]:
                    contents = contents.replace(f"**{prop}**", subvariant.plugin_properties["gnome_shell"][prop])
                elif automatic[prop][0] in generated_properties:
                    contents = contents.replace(f"**{prop}**", generated_properties[automatic[prop][0]])
                else:
                    contents = contents.replace(f"**{prop}**", automatic[prop][1])
        with open(f"{CSS_DIR_}/gnome-shell-sass/_colors.scss", "w") as f:
            f.write(contents)

        # Compiling sass
        subprocess.run(
            ["sassc", "-a", f"{CSS_DIR_}/gnome-shell.scss", "gnome-shell.css"], cwd=CSS_DIR_
        )


        # Setting rtheme to use colors icons
        with open(f"{CSS_DIR_}/rtheme.css", "r") as f:
            contents = f.read()
            contents = contents.replace("**", CSS_DIR_)
        with open(f"{CSS_DIR_}/rtheme.css", "w") as f:
            f.write(contents)