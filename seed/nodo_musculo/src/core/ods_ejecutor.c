/* * PROYECTO OSIRIS - ODS EJECUTOR
 * SINTAXIS FGN | DUREZA 256 | NUCLEO INTEGRAL ESCALADO
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/wait.h>
#include <readline/readline.h>
#include <readline/history.h>
#include "../../include/ods_memoria.h"
#include "../../include/ods_ejecutor.h"

// Hash de integridad para validacion de rafagas (Dureza 256)
static unsigned int calcular_hash(const char *str) {
    unsigned int hash = 0;
    while (*str) hash = (hash << 5) + *str++;
    return hash;
}

// Tokenizador robusto con gestion de memoria segura
static char **tokenizar(char *linea) {
    char **args = malloc(MAX_ARGUMENTOS * sizeof(char *));
    if (!args) return NULL;
    int i = 0;
    char *copia = strdup(linea);
    char *token = strtok(copia, " ");
    while (token && i < MAX_ARGUMENTOS - 1) {
        args[i++] = strdup(token);
        token = strtok(NULL, " ");
    }
    args[i] = NULL;
    free(copia);
    return args;
}

// MODO MULTILINEA (#!) - Captura interactiva con cursor
static void comando_multiline(char *nombre) {
    printf("[MODO MULTILINEA] Escribe tu bloque. Finaliza con '.' en una linea nueva.\n");
    char buffer[8192] = {0};
    char *linea_input;
    
    while ((linea_input = readline("  .. ")) != NULL) {
        if (strcmp(linea_input, ".") == 0) {
            free(linea_input);
            break;
        }
        if (strlen(buffer) + strlen(linea_input) + 2 < 8192) {
            strcat(buffer, linea_input);
            strcat(buffer, "\n");
        }
        free(linea_input);
    }
    
    if (strlen(buffer) > 0) {
        ods_mem_guardar(nombre, buffer);
        printf("[OK] Bloque Uranio '%s' capturado exitosamente.\n", nombre);
    }
}

// TRANSMISION DE NODO (>) - Comunicacion entre estratos sin shell

// Declaracion externa del driver
extern void ods_red_transmitir(const char *mensaje, unsigned int hash);

static void transmitir_a_nodo(char *mensaje) {
    // Calculamos el hash antes de enviar para que el servidor pueda validar integridad
    unsigned int h = 0;
    char *p = mensaje;
    while (*p) h = (h << 5) + *p++;
    
    ods_red_transmitir(mensaje, h);
}

void ods_ejecutar_comando(char **args) {
    if (!args[0]) return;

    char prefijo = args[0][0];
    char *target = args[0] + 1;

    // 1. OPERADOR DE NODO (>) - Prioridad de enlace
    if (prefijo == '>') {
        transmitir_a_nodo(target);
        return;
    }

    // 2. MODO MULTILINEA (#!) 
    if (prefijo == '#' && args[0][1] == '!') {
        comando_multiline(args[0] + 2);
        return;
    }

    // 3. OPERADORES DE UN SOLO CARACTER ($, #, ~, @)
    if (prefijo == '~') {
        VariableODS *v = ods_mem_obtener(target);
        if (v) {
            printf("\n[INSPECCION ~ %s]\n", v->nombre);
            printf(" RAM: %p | LIM: %lu | HASH: %X\n", v->safe_ptr.ptr, v->safe_ptr.lim, v->safe_ptr.hash);
            printf("------------------------------------------\n");
        } else printf("[ERROR] Variable '%s' no encontrada en el Estrato.\n", target);
        return;
    }

    if (prefijo == '#') {
        VariableODS *v = ods_mem_obtener(target);
        if (v) {
            unsigned int h = calcular_hash(v->valor);
            if (h == v->safe_ptr.hash) printf("[OK] Integridad Confirmada: %X\n", h);
            else printf("[ALERTA] INTEGRIDAD VIOLADA EN RAM\n");
        } else printf("[ERROR] Variable '%s' no encontrada.\n", target);
        return;
    }

    if (prefijo == '$') {
        VariableODS *v = ods_mem_obtener(target);
        if (v) printf("%s\n", v->valor);
        else printf("[ERROR] No se puede visualizar '%s'.\n", target);
        return;
    }

    if (prefijo == '@') {
        VariableODS *v = ods_mem_obtener(target);
        if (v) {
            if (calcular_hash(v->valor) == v->safe_ptr.hash) {
                system(v->valor);
            } else printf("[BLOQUEO] Firma de seguridad invalida.\n");
        } else printf("[ERROR] No hay comando guardado en '%s'.\n", target);
        return;
    }

    // 4. COMANDOS DE CONTROL (mem, save, load)
    if (strcmp(args[0], "mem") == 0 && args[1]) {
        char *val = readline("Introduce Valor: ");
        if (val) {
            ods_mem_guardar(args[1], val);
            free(val);
        }
        return;
    }

    if (strcmp(args[0], "save") == 0 && args[1]) {
        char path[256];
        snprintf(path, sizeof(path), "%s.vars", args[1]);
        FILE *f = fopen(path, "w");
        if (f) {
            int total = ods_mem_total_activos();
            for (int i = 0; i < total; i++) {
                VariableODS *v = ods_mem_obtener_por_indice(i);
                if (v) fprintf(f, "%s=%s\n", v->nombre, v->valor);
            }
            fclose(f);
            printf("[SISTEMA] Persistencia finalizada en %s\n", path);
        }
        return;
    }

    if (strcmp(args[0], "load") == 0 && args[1]) {
        char path[256];
        snprintf(path, sizeof(path), "%s.vars", args[1]);
        FILE *f = fopen(path, "r");
        if (f) {
            char buffer_linea[1024];
            while (fgets(buffer_linea, sizeof(buffer_linea), f)) {
                char *k = strtok(buffer_linea, "=");
                char *v = strtok(NULL, "\n");
                if (k && v) ods_mem_guardar(k, v);
            }
            fclose(f);
            printf("[SISTEMA] Estrato Uranio restaurado desde %s\n", path);
        } else printf("[ERROR] No se pudo localizar el archivo %s\n", path);
        return;
    }

    // 5. FALLBACK AL KERNEL (Comandos de sistema local)
    pid_t pid = fork();
    if (pid == 0) {
        if (execvp(args[0], args) == -1) {
            printf("[ERROR] Comando o ráfaga no reconocida: %s\n", args[0]);
        }
        exit(EXIT_FAILURE);
    } else {
        wait(NULL);
    }
}

void ods_ejecutar_linea(char *linea) {
    if (!linea || *linea == '\0') return;
    char **args = tokenizar(linea);
    if (args) {
        ods_ejecutar_comando(args);
        for (int i = 0; args[i]; i++) free(args[i]);
        free(args);
    }
}


