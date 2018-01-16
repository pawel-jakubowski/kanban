#!/bin/bash
sudo cp kanban.gschema.xml /usr/share/glib-2.0/schemas
glib-compile-schemas /usr/share/glib-2.0/schemas
