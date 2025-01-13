import subprocess
import shlex

def listar_audio():
    print("=== Dispositivos de Captura de Audio ===")
    result = subprocess.run(['pactl', 'list', 'sources', 'short'], stdout=subprocess.PIPE, text=True)
    audio_devices = result.stdout.strip().split('\n')
    for idx, device in enumerate(audio_devices, start=1):
        print(f"{idx}: {device}")
    return audio_devices

def listar_video():
    print("=== Dispositivos de Captura de Video ===")
    result = subprocess.run(['v4l2-ctl', '--list-devices'], stdout=subprocess.PIPE, text=True)
    video_devices = result.stdout.strip().split('\n\n')
    video_devices_cleaned = []
    for idx, device in enumerate(video_devices, start=1):
        lines = device.split('\n')
        name = lines[0].strip()
        path = lines[1].strip()
        print(f"{idx}: {name} ({path})")
        video_devices_cleaned.append(path)
    return video_devices_cleaned

def listar_pantallas():
    print("=== Pantallas Disponibles ===")
    result = subprocess.run(['xrandr', '--listmonitors'], stdout=subprocess.PIPE, text=True)
    lines = result.stdout.strip().split('\n')[1:]
    for idx, line in enumerate(lines, start=1):
        print(f"{idx}: {line.split()[-1]}")
    return [line.split()[-1] for line in lines]

def seleccionar_dispositivo(devices, tipo):
    count = len(devices)
    if count > 0:
        while True:
            try:
                seleccion = int(input(f"Seleccione el número del dispositivo de {tipo}: "))
                if 1 <= seleccion <= count:
                    return devices[seleccion - 1]
                else:
                    print(f"Opción no válida. Por favor, seleccione un número entre 1 y {count}.")
            except ValueError:
                print("Por favor, ingrese un número válido.")
    else:
        print(f"No hay dispositivos de {tipo} disponibles.")
        return ""

def main():
    audio_devices = listar_audio()
    audio_device = seleccionar_dispositivo(audio_devices, "audio").split()[1] if audio_devices else ""

    video_devices = listar_video()
    video_device = seleccionar_dispositivo(video_devices, "video") if video_devices else ""

    pantallas = listar_pantallas()
    display = seleccionar_dispositivo(pantallas, "pantalla") if pantallas else ":0.0"

    use_webcam = input("¿Desea usar la cámara web para la captura de video? (s/n): ").strip().lower() == 's'
    
    youtube_key = input("Ingrese su clave de transmisión de YouTube: ")

    if use_webcam:
        ffmpeg_command_video = (
            f"sudo -u osiris ffmpeg -y -re -f v4l2 -framerate 30 -video_size 1280x720 "
            f"-i /dev/video0 -f pulse -ac 2 -i \"{audio_device}\" -c:v libx264 -preset ultrafast "
            f"-tune zerolatency -b:v 1500k -maxrate 1500k -bufsize 3000k -g 60 -c:a aac -b:a 128k "
            f"-f flv rtmp://a.rtmp.youtube.com/live2/{youtube_key}"
        )
    else:
        ffmpeg_command_video = (
            f"sudo -u osiris ffmpeg -y -re -f v4l2 -framerate 30 -video_size 1280x720 "
            f"-i \"{video_device}\" -f pulse -ac 2 -i \"{audio_device}\" -c:v libx264 -preset ultrafast "
            f"-tune zerolatency -b:v 1500k -maxrate 1500k -bufsize 3000k -g 60 -c:a aac -b:a 128k "
            f"-f flv rtmp://a.rtmp.youtube.com/live2/{youtube_key}"
        )

    ffmpeg_command_screen = (
        f"sudo -u osiris ffmpeg -y -re -f x11grab -video_size 1280x720 -framerate 30 -i {display} "
        f"-f pulse -ac 2 -i \"{audio_device}\" -c:v libx264 -preset ultrafast -tune zerolatency "
        f"-b:v 1500k -maxrate 1500k -bufsize 3000k -g 60 -c:a aac -b:a 128k "
        f"-f flv rtmp://a.rtmp.youtube.com/live2/{youtube_key}"
    )

    print("=== Comando FFmpeg para Captura de Pantalla ===")
    print(ffmpeg_command_screen)
    if input("¿Desea ejecutar el comando de captura de pantalla? (s/n): ").strip().lower() == 's':
        subprocess.run(shlex.split(ffmpeg_command_screen))

    print("=== Comando FFmpeg para Captura de Video desde Cámara ===")
    print(ffmpeg_command_video)
    if input("¿Desea ejecutar el comando de captura de video? (s/n): ").strip().lower() == 's':
        subprocess.run(shlex.split(ffmpeg_command_video))

if __name__ == "__main__":
    main()
