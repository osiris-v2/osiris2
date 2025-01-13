import zipfile
import xml.etree.ElementTree as ET
import os

def create_lmms_project():
    # Crear el XML básico para un proyecto de LMMS
    root = ET.Element("lmms-project")
    head = ET.SubElement(root, "head")
    project = ET.SubElement(root, "project", bpm="80", name="Playa al Atardecer")

    # Añadir pista de ruido de olas (ruido blanco filtrado)
    track_olas = ET.SubElement(project, "track", name="Olas", muted="0", solo="0")
    instrument_olas = ET.SubElement(track_olas, "instrumenttrack", plugin="AudioFileProcessor")
    sample_olas = ET.SubElement(instrument_olas, "sample", file="samples/white_noise.wav")
    pattern_olas = ET.SubElement(instrument_olas, "pattern")
    ET.SubElement(pattern_olas, "note", tick="0", note="60", volume="80")

    # Añadir pista de "pad" para la melodía del viento
    track_pad = ET.SubElement(project, "track", name="Viento", muted="0", solo="0")
    instrument_pad = ET.SubElement(track_pad, "instrumenttrack", plugin="TripleOscillator")
    triple_osc = ET.SubElement(instrument_pad, "tripleoscillator")
    triple_osc.set("waveform", "sine")
    triple_osc.set("volume", "50")
    pattern_pad = ET.SubElement(instrument_pad, "pattern")
    ET.SubElement(pattern_pad, "note", tick="0", note="65", volume="70", length="480")

    # Añadir percusión de gaviotas (simulada con un "shaker" ligero)
    track_gaviotas = ET.SubElement(project, "track", name="Gaviotas", muted="0", solo="0")
    instrument_gaviotas = ET.SubElement(track_gaviotas, "instrumenttrack", plugin="Kicker")
    pattern_gaviotas = ET.SubElement(instrument_gaviotas, "pattern")
    for i in range(0, 1920, 480):  # Distribuir los "golpes" cada 4 pasos
        ET.SubElement(pattern_gaviotas, "note", tick=str(i), note="60", volume="60")

    # Añadir arpegio de salpicaduras (con marimba)
    track_arpegio = ET.SubElement(project, "track", name="Arpegio Salpicaduras", muted="0", solo="0")
    instrument_arpegio = ET.SubElement(track_arpegio, "instrumenttrack", plugin="ZynAddSubFX")
    zyn = ET.SubElement(instrument_arpegio, "zynaddsubfx")
    zyn.set("preset", "Marimba")
    pattern_arpegio = ET.SubElement(instrument_arpegio, "pattern")
    for i in range(0, 960, 240):  # Cada cuarto de compás
        ET.SubElement(pattern_arpegio, "note", tick=str(i), note="72", volume="75")

    # Añadir bajo cálido (sintetizador sub-bass)
    track_bajo = ET.SubElement(project, "track", name="Bajo", muted="0", solo="0")
    instrument_bajo = ET.SubElement(track_bajo, "instrumenttrack", plugin="TripleOscillator")
    triple_osc_bajo = ET.SubElement(instrument_bajo, "tripleoscillator")
    triple_osc_bajo.set("waveform", "square")
    triple_osc_bajo.set("volume", "60")
    pattern_bajo = ET.SubElement(instrument_bajo, "pattern")
    ET.SubElement(pattern_bajo, "note", tick="0", note="40", volume="80", length="960")

    # Guardar el archivo XML en un archivo .mmpz comprimido
    tree = ET.ElementTree(root)
    content_file_path = "/home/osiris/Documentos/lmms/projects/content.xml"
    project_file_path = "/home/osiris/Documentos/lmms/projects/playa_al_atardecer.mmpz"

    # Escribir el XML en un archivo temporal antes de comprimirlo
    tree.write(content_file_path, encoding="utf-8", xml_declaration=True)

    # Crear el archivo .mmpz
    with zipfile.ZipFile(project_file_path, "w") as lmms_project:
        lmms_project.write(content_file_path, arcname=content_file_path)

    # Limpiar el archivo temporal
    os.remove(content_file_path)

    print(f"Archivo '{project_file_path}' generado exitosamente.")

# Ejecutar la función para crear el proyecto
create_lmms_project()

