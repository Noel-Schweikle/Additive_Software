import sys
import os
import numpy as np
import trimesh
import pyvista as pv
from PyQt5.QtWidgets import (QApplication, QMainWindow, QFrame, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QFileDialog, QMessageBox, QWidget)
from pyvistaqt import QtInteractor

class ThreeDViewer(QMainWindow):
    def __init__(self):
        super().__init__()

        # Grundeinstellungen des Fensters
        self.setWindowTitle("STL & 3MF Viewer mit PyQt5")
        self.resize(1000, 800)

        # Haupt-Container erstellen
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # Button Layout erstellen (Horizontal)
        self.button_layout = QHBoxLayout()
        self.layout.addLayout(self.button_layout)

        # Button zum Laden erstellen
        self.btn_load = QPushButton("3D Datei öffnen (.stl, .3mf)")
        self.btn_load.clicked.connect(self.open_file_dialog)
        self.button_layout.addWidget(self.btn_load)

        # Button zum Auswählen erstellen
        self.btn_select = QPushButton("Select Model")
        self.btn_select.setCheckable(True) # Button bleibt gedrückt
        self.btn_select.clicked.connect(self.toggle_model_selection)
        self.button_layout.addWidget(self.btn_select)

        # Button zum Auswählen von Flächen erstellen
        self.btn_select_faces = QPushButton("Select Faces")
        self.btn_select_faces.setCheckable(True)
        self.btn_select_faces.clicked.connect(self.toggle_face_selection)
        self.button_layout.addWidget(self.btn_select_faces)

        # --- Der 3D Viewer (QtInteractor) ---
        # Dies ist das Widget, das PyVista in PyQt einbettet
        self.plotter = QtInteractor(self.central_widget)
        self.layout.addWidget(self.plotter.interactor)
        
        # Einstellungen für den Plotter
        self.plotter.set_background("white")
        self.plotter.add_axes()
        self.plotter.enable_trackball_style() # Intuitive Maussteuerung
        
        self.selected_actor = None
        self.original_color = "lightblue"

        self.selected_actor = None
        self.selected_face_actor = None
        self.original_color = "lightblue"
        self.pv_mesh = None # Speichern für Zugriff in Callbacks

    def toggle_model_selection(self):
        """Aktiviert oder deaktiviert den Modellauswahlmodus."""
        # Immer erst altes Picking deaktivieren, um Fehler zu vermeiden
        self.plotter.disable_picking()
        
        if self.btn_select.isChecked():
            # Anderen Modus deaktivieren
            self.btn_select_faces.setChecked(False)
            self.btn_select_faces.setText("Select Faces")
            
            self.btn_select.setText("Selection Mode: ON")
            # Picking aktivieren
            self.plotter.enable_mesh_picking(callback=self.highlight_mesh, show=False, left_clicking=True)
            
            # Alten Face-Selection Actor entfernen falls vorhanden
            if self.selected_face_actor:
                self.plotter.remove_actor(self.selected_face_actor)
                self.selected_face_actor = None
        else:
            self.btn_select.setText("Select Model")
            # Reset selection visualization if needed
            if self.selected_actor:
                self.selected_actor.prop.color = self.original_color
                self.selected_actor = None

    def toggle_face_selection(self):
        """Aktiviert oder deaktiviert den Flächenauswahlmodus."""
        # Immer erst altes Picking deaktivieren
        self.plotter.disable_picking()
        
        if self.btn_select_faces.isChecked():
            # Anderen Modus deaktivieren
            self.btn_select.setChecked(False)
            self.btn_select.setText("Select Model")
            # Reset model selection if active
            if self.selected_actor:
                self.selected_actor.prop.color = self.original_color
                self.selected_actor = None
            
            self.btn_select_faces.setText("Face Mode: ON")
            
            if self.pv_mesh:
                # Cell Picking aktivieren (Flächen)
                self.plotter.enable_cell_picking(mesh=self.pv_mesh, callback=self.highlight_face, show=False)
            else:
                # Falls kein Mesh geladen ist, kann man nichts picken, aber Button ist an.
                pass
        else:
            self.btn_select_faces.setText("Select Faces")
            if self.selected_face_actor:
                self.plotter.remove_actor(self.selected_face_actor)
                self.selected_face_actor = None

    def highlight_face(self, picked_mesh):
        """Callback wenn eine Fläche angeklickt wird."""
        # picked_mesh ist ein UnstructuredGrid, das die selektierte Zelle enthält
        
        # Alten Face-Selection Actor entfernen
        if self.selected_face_actor:
            self.plotter.remove_actor(self.selected_face_actor)
        
        # Neue Fläche hinzufügen (in Magenta)
        self.selected_face_actor = self.plotter.add_mesh(picked_mesh, color="magenta", show_edges=False, pickable=False)
        # pickable=False ist wichtig, damit wir nicht die Highlight-Fläche picken beim nächsten Klick

    def highlight_mesh(self, mesh):
        """Callback wenn ein Mesh angeklickt wird."""
        # mesh ist hier das vtk/pyvista Objekt
        
        # Wir müssen den Actor finden, der zu diesem Mesh gehört, um die Farbe zu ändern
        # PyVista's enable_mesh_picking callback gibt das Mesh zurück.
        # Wir können direkt auf das Mesh zugreifen, aber Farbe ist eine Eigenschaft des Actors.
        
        # Trick: Wir iterieren über die Actors im Renderer, um den passenden zu finden
        # Oder einfacher: Wir färben einfach das Mesh neu und updaten es?
        # Nein, Actor Properties sind besser.
        
        # In neueren PyVista Versionen kann man 'use_actor=True' setzen bei enable_mesh_picking
        # Aber um sicher zu gehen bei der installierten Version:
        
        # Wir setzen einfach alle Actors zurück und färben den geklickten (wenn wir ihn finden)
        # Da wir hier nur ein Mesh haben (meistens), ist es einfach.
        
        # Aber wait, enable_mesh_picking returns the mesh (PolyData).
        # Wir können das Mesh selbst nicht "färben" ohne es neu zu plotten oder den Actor zu ändern.
        
        # Versuch: Wir clearen und plotten neu? Nein, zu langsam.
        
        # Besser: Wir nutzen 'pickable=True' beim add_mesh und holen uns den Actor.
        # Leider gibt enable_mesh_picking nur das Mesh.
        
        # Alternative: Wir nutzen enable_point_picking oder ähnliches? Nein.
        
        # Workaround: Da wir nur ein Haupt-Mesh haben (final_mesh), wissen wir, welcher Actor es ist,
        # wenn wir ihn uns beim Laden merken.
        
        if self.actor:
            # Reset old color
            if self.selected_actor and self.selected_actor != self.actor:
                 self.selected_actor.prop.color = self.original_color
            
            self.selected_actor = self.actor
            self.selected_actor.prop.color = "red"
            self.plotter.render() # Update view

    def open_file_dialog(self):
        """Öffnet den Dateimanager und ruft die Lade-Funktion auf."""
        file_filter = "3D Files (*.stl *.3mf);;STL Files (*.stl);;3MF Files (*.3mf)"
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Öffne 3D Modell",
            os.getcwd(),
            file_filter
        )

        if filename:
            self.load_and_render(filename)

    def load_and_render(self, filename):
        """Lädt die Datei mit Trimesh und rendert sie mit PyVista."""
        try:
            # 1. Datei mit Trimesh laden (Unterstützt STL und 3MF sehr gut)
            mesh_data = trimesh.load(filename)

            # 2. Daten verarbeiten
            # .3mf Dateien sind oft "Szenen" (mehrere Objekte). 
            # Wir müssen sie für die Anzeige ggf. zusammenführen.
            if isinstance(mesh_data, trimesh.Scene):
                # Wenn es eine Szene ist, exportieren wir sie als einzelnes Mesh
                # oder dumpen die Geometrien zusammen.
                if len(mesh_data.geometry) == 0:
                    raise ValueError("Die 3MF Datei scheint leer zu sein.")
                
                # Wir konvertieren die Szene in ein einzelnes Trimesh-Objekt zur Anzeige
                # mesh_data.dump() gibt eine Liste von Trimesh-Objekten zurück (mit angewandten Transformationen)
                mesh_concat = trimesh.util.concatenate(mesh_data.dump())
                final_mesh = mesh_concat
            else:
                # Es ist bereits ein einzelnes Mesh (typisch für STL)
                final_mesh = mesh_data

            # 3. Konvertierung von Trimesh zu PyVista PolyData
            # PyVista benötigt 'faces' und 'vertices'
            # Trimesh faces sind (n, 3), PyVista erwartet Padding (n, 4) mit der '3' am Anfang
            faces = final_mesh.faces
            # Füge eine Spalte mit Dreien davor ein (für Dreiecke)
            padding = np.full((faces.shape[0], 1), 3)
            faces_padded = np.hstack((padding, faces)).flatten()
            
            self.pv_mesh = pv.PolyData(final_mesh.vertices, faces_padded)
            
            # 4. Anzeigen im Plotter
            self.plotter.clear() # Altes Modell entfernen
            self.actor = self.plotter.add_mesh(self.pv_mesh, color=self.original_color, show_edges=True, pickable=True)
            self.selected_actor = None # Reset selection
            self.selected_face_actor = None
            
            # Falls Face Selection an war, müssen wir es für das neue Mesh re-enablen?
            # Einfacher: Wir resetten die Buttons beim Laden neuer Datei
            self.btn_select.setChecked(False)
            self.btn_select.setText("Select Model")
            self.btn_select_faces.setChecked(False)
            self.btn_select_faces.setText("Select Faces")
            self.plotter.disable_picking()

            self.plotter.reset_camera() # Kamera auf das Objekt zentrieren
            self.plotter.add_axes()
            
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Datei konnte nicht geladen werden:\n{str(e)}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ThreeDViewer()
    window.show()
    sys.exit(app.exec_())
