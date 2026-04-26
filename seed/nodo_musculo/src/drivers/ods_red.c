/* * PROYECTO OSIRIS - DRIVER DE RED (CONEXION CEREBRO SEMILLA)
 * SINTAXIS FGN | DUREZA 256
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <sys/socket.h>
#include "ods_protocol.h"

void ods_red_transmitir(const char *mensaje, unsigned int hash) {
    int sock = 0;
    struct sockaddr_in serv_addr;
    PaqueteSoberano pkg;

    /* Verificacion de layout en runtime (debug) */
    if (__builtin_offsetof(PaqueteSoberano, data) != 14) {
        printf("[FATAL] PaqueteSoberano: layout incorrecto. Offset data=%zu esperado=14\n",
               __builtin_offsetof(PaqueteSoberano, data));
        return;
    }

    memset(&pkg, 0, sizeof(PaqueteSoberano));
    pkg.magic      = CABECERA_MAGICA;
    pkg.hash_verif = hash;
    pkg.longitud   = (uint64_t)strlen(mensaje);  /* cast explicito — longitud es u64 */
    strncpy((char*)pkg.data, mensaje, sizeof(pkg.data) - 1);
    pkg.data[sizeof(pkg.data) - 1] = '\0';

    if ((sock = socket(AF_INET, SOCK_STREAM, 0)) < 0) {
        printf("[ERROR] Fallo en creacion de socket.\n");
        return;
    }

    serv_addr.sin_family = AF_INET;
    // Si PUERTO_OSIRIS falla, aqui es donde debes forzar el numero (ej: htons(2000))
    serv_addr.sin_port = htons(PUERTO_OSIRIS); 

    if (inet_pton(AF_INET, "127.0.0.1", &serv_addr.sin_addr) <= 0) {
        printf("[ERROR] Direccion IP invalida.\n");
        close(sock);
        return;
    }

    // Intento de conexion al Cerebro Semilla
    if (connect(sock, (struct sockaddr *)&serv_addr, sizeof(serv_addr)) < 0) {
        // Añadimos el puerto al log para saber donde estamos fallando
        printf("[SISTEMA] Cerebro Semilla no detectado en puerto %d. Modo Standalone activo.\n", PUERTO_OSIRIS);
        close(sock);
        return;
    }

    // Envio de la rafaga blindada (Dureza 256)
    if (send(sock, &pkg, sizeof(PaqueteSoberano), 0) < 0) {
        printf("[ERROR] Error al entregar la rafaga.\n");
    } else {
        printf("[ENLACE] Rafaga entregada al Cerebro Semilla (Firma: %08X)\n", hash);
    }

    close(sock);
}