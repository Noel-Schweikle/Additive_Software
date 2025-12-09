import sys
import os
import numpy as np
import trimesh
import pyvista as pv
from PyQt5.QtWidgets import (QApplication, QMainWindow, QFrame, QVBoxLayout, 
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

        # Button zum Laden erstellen
        self.btn_load = QPushButton("3D Datei öffnen (.stl, .3mf)")
        self.btn_load.clicked.connect(self.open_file_dialog)
        self.layout.addWidget(self.btn_load)

        # --- Der 3D Viewer (QtInteractor) ---
        # Dies ist das Widget, das PyVista in PyQt einbettet
        self.plotter = QtInteractor(self.central_widget)
        self.layout.addWidget(self.plotter.interactor)
        
        # Einstellungen für den Plotter
        self.plotter.set_background("white")
        self.plotter.add_axes()
        self.plotter.enable_trackball_style() # Intuitive Maussteuerung

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
                mesh_concat = trimesh.util.concatenate(
                    tuple(trimesh.graph.geometry(mesh_data, geom) for geom in mesh_data.geometry.keys())
                )
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
            
            pv_mesh = pv.PolyData(final_mesh.vertices, faces_padded)

            # 4. Anzeigen im Plotter
            self.plotter.clear() # Altes Modell entfernen
            self.plotter.add_mesh(pv_mesh, color="lightblue", show_edges=True)
            self.plotter.reset_camera() # Kamera auf das Objekt zentrieren
            self.plotter.add_axes()
            
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Datei konnte nicht geladen werden:\n{str(e)}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ThreeDViewer()
    window.show()
    sys.exit(app.exec_())
