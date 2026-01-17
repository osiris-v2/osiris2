#include "../include/osiris_hw.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

void probe_sistema_base(OsirisHardwareMap *map) {
    // Deteccion de nucleos mediante el sistema (Nproc)
    FILE *fp = popen("nproc", "r");
    if (fp) {
        fscanf(fp, "%u", &map->cpu_nucleos);
        pclose(fp);
    }

    // Deteccion de RAM leyendo /proc/meminfo
    fp = fopen("/proc/meminfo", "r");
    if (fp) {
        char buffer[256];
        while (fgets(buffer, sizeof(buffer), fp)) {
            if (strncmp(buffer, "MemTotal:", 9) == 0) {
                // Extraemos el valor numerico en kB y pasamos a MB
                sscanf(buffer + 9, "%llu", &map->ram_total_mb);
                map->ram_total_mb /= 1024;
                break;
            }
        }
        fclose(fp);
    }
    
    printf("[DEBUG] Detectados %u nucleos y %llu MB de RAM\n", 
            map->cpu_nucleos, map->ram_total_mb);
}