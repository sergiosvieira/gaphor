"""Gaphor is the simple modeling tool written in Python."""

import os

import gi

gtk_version = "4.0" if os.getenv("GAPHOR_USE_GTK") == "4" else "3.0"
gtk_source_version = "5" if os.getenv("GAPHOR_USE_GTK") == "4" else "4"

if gtk_version == "4.0":
    # Monkey patch PyGObject
    import gi.overrides.Gtk

    del gi.overrides.Gtk.TreeView.enable_model_drag_source
    del gi.overrides.Gtk.TreeView.enable_model_drag_dest

gi.require_version("PangoCairo", "1.0")
gi.require_version("Gtk", gtk_version)
gi.require_version("Gdk", gtk_version)

if gtk_version == "3.0":
    gi.require_version("GtkSource", gtk_source_version)
