import asyncio
import websockets
import sys
import argparse
import logging
from datetime import datetime
from colorama import Fore, Style, init

# Inicializar colores
init(autoreset=True)

# Configuración de Logging profesional
logging.basicConfig(
    level=logging.INFO,
    format=f'{Fore.CYAN}%(asctime)s {Style.RESET_ALL}%(message)s',
    datefmt='%H:%M:%S'
)

class GoyCorpClient:
    def __init__(self, url, timeout, retry_limit, initial_msg=None):
        self.url = url
        self.timeout = timeout
        self.retry_limit = retry_limit
        self.initial_msg = " ".join(initial_msg) if initial_msg else None
        self.is_running = True
        self.retries = 0

    async def run(self):
        """Ciclo principal con lógica de reconexión."""
        while self.is_running and self.retries < self.retry_limit:
            try:
                async with websockets.connect(
                    self.url, 
                    open_timeout=self.timeout
                ) as ws:
                    self.retries = 0  # Reset al conectar con éxito
                    logging.info(f"{Fore.GREEN}✅ Conectado a {self.url}")

                    # Si se pasó un mensaje por argumentos al lanzar el script
                    if self.initial_msg:
                        logging.info(f"📤 Enviando mensaje inicial...")
                        await ws.send(self.initial_msg)
                        resp = await ws.recv()
                        print(f"{Fore.CYAN}📩 [Respuesta]: {Style.RESET_ALL}{resp}")
                        self.initial_msg = None # Solo se envía una vez

                    await self.handler(ws)

            except Exception as e:
                self.retries += 1
                logging.error(f"{Fore.RED}❌ Error ({self.retries}/{self.retry_limit}): {e}")
                if self.is_running and self.retries < self.retry_limit:
                    await asyncio.sleep(5)
                else:
                    self.is_running = False






    async def handler(self, ws):
        """Maneja la entrada/salida de datos gestionando el streaming."""
        loop = asyncio.get_event_loop()
        print(f"{Fore.YELLOW}Tip: '/help' para comandos internos o 'salir' para cerrar.")

        while True:
            try:
                prompt = f"{Fore.MAGENTA}GoyCorp@{datetime.now().strftime('%H:%M')} > {Style.RESET_ALL}"
                comando = await loop.run_in_executor(None, lambda: input(prompt))

                cmd_clean = comando.strip().lower()
                if cmd_clean in ['salir', 'exit', 'quit']:
                    self.is_running = False
                    return
                
                if cmd_clean == '/help':
                    self.show_help(); continue
                
                if cmd_clean == '/status':
                    print(f"{Fore.BLUE}--- Status ---\nURL: {self.url}\nLatencia: {ws.latency:.4f}s"); continue

                if not comando.strip():
                    continue

                # 1. Enviamos el comando
                await ws.send(comando)
                
                # 2. Recibimos el stream
                print(f"{Fore.CYAN}📩 [Servidor]: {Style.RESET_ALL}", end="", flush=True)
                
                # Leemos fragmentos hasta que el servidor deje de enviar o envíe un marcador de fin
                while True:
                    try:
                        # Ponemos un timeout corto para detectar el fin del stream si no hay marcador
                        fragmento = await asyncio.wait_for(ws.recv(), timeout=2.0)
                        print(fragmento, end="", flush=True)
                        
                        # Si tu servidor envía un JSON o un marcador específico (ej: [DONE]), rompe aquí:
                        # if "[DONE]" in fragmento: break 
                        
                    except asyncio.TimeoutError:
                        # Si pasan 2 segundos sin datos, asumimos que la respuesta terminó
                        break
                
                print("\n") # Nueva línea al terminar la respuesta completa

            except websockets.ConnectionClosed:
                logging.error("⚠️ Conexión perdida.")
                break






    def show_help(self):
        print(f"\n{Fore.YELLOW}Comandos GoyCorp:{Style.RESET_ALL}")
        print(" /help   - Esta ayuda")
        print(" /status - Info de conexión")
        print(" salir   - Cerrar programa\n")

def main(args=None):
    """Punto de entrada compatible con módulos y CLI."""
    parser = argparse.ArgumentParser(
        description="GoyCorp Client Full",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument("--url", default="ws://vtwitt.com:8081", help="URL del servidor")
    parser.add_argument("--timeout", type=int, default=10, help="Timeout de conexión")
    parser.add_argument("--retries", type=int, default=10, help="Límite de reintentos")
    
    # Aquí capturamos cualquier texto suelto después de los flags
    parser.add_argument("mensaje", nargs='*', help="Mensaje inicial directo")

    parsed_args = parser.parse_args(args)

    client = GoyCorpClient(
        url=parsed_args.url,
        timeout=parsed_args.timeout,
        retry_limit=parsed_args.retries,
        initial_msg=parsed_args.mensaje
    )

    try:
        asyncio.run(client.run())
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}👋 Sesión finalizada.")

if __name__ == "__main__":
    main()
