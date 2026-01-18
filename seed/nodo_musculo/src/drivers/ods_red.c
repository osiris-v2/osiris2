/* * PROYECTO OSIRIS - DRIVER DE RED (CONEXION CEREBRO SEMILLA)
 * SINTAXIS FGN | DUREZA 256
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <sys/socket.h>
#include "../../include/ods_protocol.h"

void ods_red_transmitir(const char *mensaje, unsigned int hash) {
    int sock = 0;
    struct sockaddr_in serv_addr;
    PaqueteSoberano pkg;

    // Alineacion de la estructura segun el Manifiesto
    memset(&pkg, 0, sizeof(PaqueteSoberano));
    pkg.magic = CABECERA_MAGICA;
    pkg.hash_verif = hash;
    pkg.longitud = strlen(mensaje);
    strncpy(pkg.data, mensaje, 4095);

    if ((sock = socket(AF_INET, SOCK_STREAM, 0)) < 0) {
        printf("[ERROR] Fallo en creacion de socket.\n");
        return;
    }

    serv_addr.sin_family = AF_INET;
    serv_addr.sin_port = htons(PUERTO_OSIRIS);

    if (inet_pton(AF_INET, "127.0.0.1", &serv_addr.sin_addr) <= 0) {
        close(sock);
        return;
    }

    // Intento de conexion al Cerebro Semilla
    if (connect(sock, (struct sockaddr *)&serv_addr, sizeof(serv_addr)) < 0) {
        printf("[SISTEMA] Cerebro Semilla no detectado. Modo Standalone activo.\n");
        close(sock);
        return;
    }

    // Envio de la rafaga blindada
    send(sock, &pkg, sizeof(PaqueteSoberano), 0);
    printf("[ENLACE] Rafaga entregada al Cerebro Semilla (Firma: %X)\n", hash);

    close(sock);
}