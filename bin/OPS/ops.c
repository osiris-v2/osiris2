#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/wait.h>
#include <ctype.h>
#include <readline/readline.h>
#include <readline/history.h>
#include <signal.h>  // Necesario para SIGTERM
//#include "ops.h"

#define MAX_LINE_LENGTH 1024
#define MAX_ARGS 100
#define MAX_CDN_SIZE 100
#define MAX_VAR_NAME_LENGTH 64  // Longitud máxima para el nombre de variable
#define FILE_EXTENSION ".vars"
#define MAX_ARGS 100 // para ejecutar variables almacenadas como comandos


typedef struct {
    char *name;
    char *value;
} Variable;

typedef struct {
    Variable vars[MAX_CDN_SIZE];
    int count;
    int multiline_mode;  // Activar o desactivar el modo multilinea
} CDNStorage;

CDNStorage cdn_storage = { .count = 0, .multiline_mode = 0 };

void initialize_shell_environment() {
    // Inicializar variables de entorno o configuración si es necesario
}

char *read_command_line() {
    // Usar readline para leer la entrada del usuario
    char *line = readline("> ods>> ");
    if (!line) {
        perror("readline");
        exit(EXIT_FAILURE); // Salir si readline devuelve NULL (EOF)
    }
    // Agregar la línea al historial si no está vacía
    if (*line) {
        add_history(line);
    }
    return line;
}

char *read_multiline_input() {
    // Función para leer la entrada en modo multilinea
    char *input = NULL;
    size_t input_len = 0;
    char *line;
    int needs_newline = 0; // Flag to track if we need to add a newline after EOF

    printf("Entering multiline mode. Type 'EOF' on a new line to end.\n");

    while (1) {
        // Usar readline para obtener una línea de entrada
        line = readline(NULL);
        if (line == NULL) {
            perror("readline");
            exit(EXIT_FAILURE);
        }

        // Check if the input is exactly "EOF"
        if (strcmp(line, "EOF") == 0) {
            // Remove the trailing newline if it exists
            if (input_len > 0 && input[input_len - 1] == '\n') {
                input_len--; // Remove last newline
                input[input_len] = '\0'; // Null-terminate after removal
            }
            free(line);
            break;
        }

        size_t len = strlen(line);

        // Add newline if needed
        if (len > 0) {
            needs_newline = 1; // Indicate that we should add a newline later
        } else {
            needs_newline = 0; // No newline at the end
        }

        // Allocate or reallocate memory for input
        char *new_input = realloc(input, input_len + len + (needs_newline ? 1 : 0) + 1);
        if (!new_input) {
            perror("realloc");
            exit(EXIT_FAILURE);
        }
        input = new_input;

        // Copy the line into the new input, followed by a newline if needed
        memcpy(input + input_len, line, len);
        input_len += len;
        if (needs_newline) {
            input[input_len] = '\n'; // Add a newline
            input_len++;
        }
        input[input_len] = '\0'; // Null-terminate the string

        free(line);
    }

    return input;
}

char **parse_command_line(char *line) {
    char **args = malloc(MAX_ARGS * sizeof(char *));
    if (!args) {
        perror("malloc");
        exit(EXIT_FAILURE);
    }
    char *token = strtok(line, " ");
    int index = 0;
    while (token != NULL && index < MAX_ARGS - 1) {
        args[index++] = strdup(token);
        token = strtok(NULL, " ");
    }
    args[index] = NULL;
    return args;
}

void print_variable_value(const char *name) {
    for (int i = 0; i < cdn_storage.count; i++) {
        if (strcmp(cdn_storage.vars[i].name, name) == 0) {
            printf("%s\n", cdn_storage.vars[i].value);
            return;
        }
    }
    printf("Variable not found: %s\n", name);
}






// Función para dividir una cadena en argumentos respetando las comillas
int split_args(const char *cmd, char **argv) {
    const char *p = cmd;
    int i = 0;
    char *arg;
    int len;
    
    while (*p) {
        // Salto de espacios
        while (*p && isspace(*p)) {
            p++;
        }

        if (*p == '\0') {
            break;
        }

        // Aquí estamos comenzando a leer un nuevo argumento
        if (*p == '"' || *p == '\'' || *p == '`') {
            // Detectar el tipo de comillas
            char quote = *p;
            p++;
            arg = malloc(strlen(p) + 1); // Necesitamos memoria para el argumento

            if (arg == NULL) {
                perror("Error al asignar memoria para argumento");
                return -1;
            }

            len = 0;
            while (*p && *p != quote) {  // Leer hasta que encontremos la comilla correspondiente
                arg[len++] = *p++;
            }

            if (*p == quote) {
                p++;  // Salir de las comillas
            }

            arg[len] = '\0';  // Terminar el argumento
            argv[i++] = arg;

        } else {
            // Argumento sin comillas
            arg = malloc(strlen(p) + 1); // Necesitamos memoria para el argumento
            if (arg == NULL) {
                perror("Error al asignar memoria para argumento");
                return -1;
            }

            len = 0;
            while (*p && !isspace(*p)) { // Leer hasta el siguiente espacio
                arg[len++] = *p++;
            }

            arg[len] = '\0'; // Terminar el argumento
            argv[i++] = arg;
        }

        if (i >= MAX_ARGS) {
            printf("Demasiados argumentos\n");
            return -1;
        }
    }

    argv[i] = NULL;  // Terminar con NULL, como espera execvp
    return i;  // Devolvemos el número de argumentos
}

// Función para ejecutar el valor de la variable
void exec_variable_value(const char *name) {
    for (int i = 0; i < cdn_storage.count; i++) {
        if (strcmp(cdn_storage.vars[i].name, name) == 0) {
            // Crear una copia del valor porque strtok_r modifica la cadena
            char *cmd_copy = strdup(cdn_storage.vars[i].value);
            if (cmd_copy == NULL) {
                perror("Error duplicando la cadena del comando");
                return;
            }

            // Array de argumentos con un tamaño máximo
            char *argv[MAX_ARGS];
            int argc = split_args(cmd_copy, argv);

            if (argc == -1) {
                free(cmd_copy);
                return;  // Error en la tokenización
            }

            pid_t pid = fork();
            if (pid < 0) {
                perror("Error al hacer fork");
                free(cmd_copy);
                return;
            }

            if (pid == 0) { // Proceso hijo
                // Ejecutar el comando en el proceso hijo
                execvp(argv[0], argv);
                perror("Error al ejecutar el comando");
                free(cmd_copy);
                exit(EXIT_FAILURE);  // Si execvp falla, salir del proceso hijo
            } else { // Proceso padre
                // Esperar a que el proceso hijo termine
                int status;
                waitpid(pid, &status, 0);
                if (WIFEXITED(status)) {
                    printf("El proceso terminó con código de salida %d\n", WEXITSTATUS(status));
                } else {
                    printf("El proceso terminó con un error\n");
                }
            }

            // Liberar la memoria
            free(cmd_copy);
            return;
        }
    }

    // Si no se encuentra la variable
    printf("Variable not found: %s\n", name);
}





void print_variable_info(const char *name) {
    for (int i = 0; i < cdn_storage.count; i++) {
        if (strcmp(cdn_storage.vars[i].name, name) == 0) {
            printf("Valor: string\n");
            printf("Tamaño: %lu bytes\n", strlen(cdn_storage.vars[i].value) + 1);
            printf("Dirección en memoria: %p\n", (void *)cdn_storage.vars[i].value);
            printf("Tipo: string\n");
            return;
        }
    }
    printf("Variable not found: %s\n", name);
}

int is_valid_variable_name(const char *name) {
    if (strlen(name) > MAX_VAR_NAME_LENGTH) return 0;
    if (name[0] == '\0') return 0;
    if (!(isalpha(name[0]) || name[0] == '_' || isdigit(name[0]))) return 0;
    for (int i = 0; name[i] != '\0'; i++) {
        if (!(isalnum(name[i]) || name[i] == '_')) return 0;
    }
    return 1;
}

void save_variables_to_file(const char *filename) {
    // Añadir extensión .vars
    char *full_filename = malloc(strlen(filename) + strlen(FILE_EXTENSION) + 1);
    if (!full_filename) {
        perror("malloc");
        exit(EXIT_FAILURE);
    }
    sprintf(full_filename, "%s%s", filename, FILE_EXTENSION);

    // Verificar si el archivo ya existe
    if (access(full_filename, F_OK) != -1) {
        // Archivo existe, pedir confirmación para sobrescribir
        char response[10];
        printf("File '%s' already exists. Overwrite? (y/n): ", full_filename);
        if (fgets(response, sizeof(response), stdin) == NULL) {
            perror("fgets");
            free(full_filename);
            exit(EXIT_FAILURE);
        }
        response[strcspn(response, "\n")] = '\0'; // Remove newline character

        if (strcmp(response, "y") != 0) {
            printf("Operation cancelled.\n");
            free(full_filename);
            return;
        }
    }

    FILE *file = fopen(full_filename, "w");
    if (!file) {
        perror("fopen");
        free(full_filename);
        exit(EXIT_FAILURE);
    }

    for (int i = 0; i < cdn_storage.count; i++) {
        fprintf(file, "%s=", cdn_storage.vars[i].name);
        // Convertir saltos de línea en \\n
        char *ptr = cdn_storage.vars[i].value;
        while (*ptr) {
            if (*ptr == '\n') {
                fprintf(file, "\\n");
            } else {
                fputc(*ptr, file);
            }
            ptr++;
        }
        fprintf(file, "\n");
    }

    fclose(file);
    free(full_filename);
}

void replace_newlines(char *str) {
    char *src = str, *dst = str;
    while (*src) {
        if (*src == '\\' && *(src + 1) == 'n') {
            *dst++ = '\n';
            src += 2;
        } else {
            *dst++ = *src++;
        }
    }
    *dst = '\0';
}

void load_variables_from_file(const char *filename, const char *mode) {
    // Añadir extensión .vars
    char *full_filename = malloc(strlen(filename) + strlen(FILE_EXTENSION) + 1);
    if (!full_filename) {
        perror("malloc");
        exit(EXIT_FAILURE);
    }
    sprintf(full_filename, "%s%s", filename, FILE_EXTENSION);

    FILE *file = fopen(full_filename, "r");
    if (!file) {
        printf("File '%s' does not exist or cannot be opened.\n", full_filename);
        free(full_filename);
        return;
    }

    if (strcmp(mode, "load-") == 0) {
        // Eliminar todas las variables
        for (int i = 0; i < cdn_storage.count; i++) {
            free(cdn_storage.vars[i].name);
            free(cdn_storage.vars[i].value);
        }
        cdn_storage.count = 0;
    }

    char line[MAX_LINE_LENGTH];
    while (fgets(line, sizeof(line), file)) {
        char *name = strtok(line, "=");
        char *value = strtok(NULL, "\n");

        if (name && value) {
            replace_newlines(value);

            int found = 0;
            for (int i = 0; i < cdn_storage.count; i++) {
                if (strcmp(cdn_storage.vars[i].name, name) == 0) {
                    if (strcmp(mode, "load++") == 0) {
                        free(cdn_storage.vars[i].value);
                        cdn_storage.vars[i].value = strdup(value);
                    }
                    found = 1;
                    break;
                }
            }

            if (!found) {
                if (cdn_storage.count >= MAX_CDN_SIZE) {
                    printf("CDN storage full\n");
                    continue;
                }
                Variable *var = &cdn_storage.vars[cdn_storage.count++];
                var->name = strdup(name);
                var->value = strdup(value);
            }
        }
    }

    fclose(file);
    free(full_filename);
}

void process_mem_command(char **args) {
    if (args[0] == NULL) {
        printf("Usage: mem <var_name>\n");
        return;
    }

    if (!is_valid_variable_name(args[0])) {
        printf("Invalid variable name: %s\n", args[0]);
        return;
    }

    char *value;
    if (cdn_storage.multiline_mode) {
        // Read input in multiline mode if multiline mode is enabled
        value = read_multiline_input();
    } else {
        value = malloc(MAX_LINE_LENGTH);
        if (!value) {
            perror("malloc");
            exit(EXIT_FAILURE);
        }
        printf("Enter value for variable (Press Enter to finish):\n");
        if (fgets(value, MAX_LINE_LENGTH, stdin) == NULL) {
            perror("fgets");
            exit(EXIT_FAILURE);
        }
        value[strcspn(value, "\n")] = '\0'; // Remove newline character
    }

    for (int i = 0; i < cdn_storage.count; i++) {
        if (strcmp(cdn_storage.vars[i].name, args[0]) == 0) {
            free(cdn_storage.vars[i].value);
            cdn_storage.vars[i].value = value;
            printf("Variable updated: %s=%s\n", args[0], cdn_storage.vars[i].value);
            return;
        }
    }

    if (cdn_storage.count >= MAX_CDN_SIZE) {
        printf("CDN storage full\n");
        free(value);
        return;
    }

    Variable *var = &cdn_storage.vars[cdn_storage.count++];
    var->name = strdup(args[0]);
    var->value = value;
    printf("Variable stored: %s=%s\n", args[0], value);
}

void execute_command(char **args) {
    if (args[0] == NULL) {
        return;
    }

    else if (args[0][0] == '$') {
        print_variable_value(args[0] + 1);
        return;
    }
 
    else if (args[0][0] == '@') {
        exec_variable_value(args[0] + 1);
        return;
    }


    else if (args[0][0] == '~') {
        print_variable_info(args[0] + 1);
        return;
    }

    if (strcmp(args[0], "view") == 0) {
        if (args[1] != NULL && args[1][0] == '$') {
            print_variable_info(args[1] + 1);
        } else {
            printf("Usage: ver $variable\n");
        }
        return;
    }

    if (strcmp(args[0], "multiline") == 0) {
        cdn_storage.multiline_mode = !cdn_storage.multiline_mode;
        printf("Multiline mode %s\n", cdn_storage.multiline_mode ? "activated" : "deactivated");
        return;
    }

    if (strcmp(args[0], "save") == 0) {
        if (args[1] != NULL) {
            save_variables_to_file(args[1]);
        } else {
            printf("Usage: save <filename>\n");
        }
        return;
    }

    if (strcmp(args[0], "load+") == 0 || strcmp(args[0], "load++") == 0 || strcmp(args[0], "load-") == 0) {
        if (args[1] != NULL) {
            load_variables_from_file(args[1], args[0]);
        } else {
            printf("Usage: %s <filename>\n", args[0]);
        }
        return;
    }

    if (strcmp(args[0], "exit") == 0) {
        free(args);
        exit(EXIT_SUCCESS);
    } else if (strcmp(args[0], "echo") == 0) {
        for (int i = 1; args[i] != NULL; i++) {
            printf("%s ", args[i]);
        }
        printf("\n");
    } else if (strcmp(args[0], "pwd") == 0) {
        char cwd[MAX_LINE_LENGTH];
        if (getcwd(cwd, sizeof(cwd)) != NULL) {
            printf("%s\n", cwd);
        } else {
            perror("getcwd");
        }
    } else if (strcmp(args[0], "mem") == 0) {

      // No es necesario parsear en la función process_mem_command
       process_mem_command(args + 1); 
    } else {

        pid_t pid;
        int status;

        pid = fork();
        if (pid < 0) {
            perror("fork");
            exit(EXIT_FAILURE);
        } else if (pid == 0) {
            // Ejecución del proceso hijo
            execvp(args[0], args);  // execvp es correcto aquí
            perror("Error al ejecutar el comando");
            exit(EXIT_FAILURE);
        } else {
            // El proceso padre espera al proceso hijo
            do {
                waitpid(pid, &status, WUNTRACED);  // WUNTRACED para manejar señales
            } while (!WIFEXITED(status) && !WIFSIGNALED(status));
        }
    }
}

void cleanup_shell() {
    for (int i = 0; i < cdn_storage.count; i++) {
        free(cdn_storage.vars[i].name);
        free(cdn_storage.vars[i].value);
    }
}

int main() {
    initialize_shell_environment();

    while (1) {
        char *line = read_command_line();
        char **args = parse_command_line(line);
        execute_command(args);

        free(line);
        for (int i = 0; args[i] != NULL; i++) {
            free(args[i]);
        }
        free(args);
    }

    cleanup_shell();
    return EXIT_SUCCESS;
}
