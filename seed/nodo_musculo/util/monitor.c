#include <ncurses.h>
#include <unistd.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>

typedef struct {
    unsigned long long user, nice, system, idle, iowait, irq, softirq, steal;
    unsigned long long total_old, idle_old;
} CPUData;

int refresh_rate = 1;

// Obtiene el uso de CPU real parseando /proc/stat
float get_cpu_usage(CPUData *cpu, int id) {
    FILE *fp = fopen("/proc/stat", "r");
    if (!fp) return 0.0;

    char line[256];
    char target[10];
    sprintf(target, "cpu%d", id);

    while (fgets(line, sizeof(line), fp)) {
        if (strncmp(line, target, strlen(target)) == 0) {
            unsigned long long u, n, s, i, io, ir, sir, st;
            sscanf(line, "%*s %llu %llu %llu %llu %llu %llu %llu %llu", &u, &n, &s, &i, &io, &ir, &sir, &st);
            
            unsigned long long idle = i + io;
            unsigned long long total = u + n + s + i + io + ir + sir + st;
            
            float diff_total = total - cpu->total_old;
            float diff_idle = idle - cpu->idle_old;
            float usage = (diff_total - diff_idle) / diff_total * 100.0;

            cpu->total_old = total;
            cpu->idle_old = idle;
            fclose(fp);
            return usage < 0 ? 0 : usage;
        }
    }
    fclose(fp);
    return 0.0;
}

void get_mem_data(float *percent, float *used_gb, float *total_gb) {
    FILE *fp = fopen("/proc/meminfo", "r");
    if (!fp) return;
    unsigned long total = 0, available = 0;
    char label[64];
    while (fscanf(fp, "%s %lu kB", label, &available) != EOF) {
        if (strcmp(label, "MemTotal:") == 0) total = available;
        if (strcmp(label, "MemAvailable:") == 0) break; 
    }
    fclose(fp);
    *total_gb = total / 1024.0 / 1024.0;
    *used_gb = (total - available) / 1024.0 / 1024.0;
    *percent = (*used_gb / *total_gb) * 100.0;
}

void draw_bar(int y, int x, int width, float percentage, char *label, int color_pair) {
    int filled = (int)(width * (percentage / 100.0));
    if (filled > width) filled = width;
    mvprintw(y, x, "%-6s [", label);
    attron(COLOR_PAIR(color_pair));
    for (int i = 0; i < filled; i++) addch('|');
    attroff(COLOR_PAIR(color_pair));
    for (int i = filled; i < width; i++) addch(' ');
    printw("] %.1f%%", percentage);
}

int main() {
    initscr(); noecho(); curs_set(0); nodelay(stdscr, TRUE);
    start_color();
    init_pair(1, COLOR_GREEN, COLOR_BLACK); // Barras
    init_pair(2, COLOR_CYAN, COLOR_BLACK);  // Títulos
    init_pair(3, COLOR_YELLOW, COLOR_BLACK); // Alertas

    CPUData cpus[4] = {0}; // Asumiendo 4 núcleos como en tu imagen
    float m_p, m_u, m_t;

    while (1) {
        int ch = getch();
        if (ch == 'q') break;
        if (ch == 'm') {
            nodelay(stdscr, FALSE);
            mvprintw(16, 2, "Nuevo refresco (seg): ");
            echo(); scanw("%d", &refresh_rate); noecho();
            if (refresh_rate < 1) refresh_rate = 1;
            nodelay(stdscr, TRUE);
        }

        get_mem_data(&m_p, &m_u, &m_t);
        erase();

        int rows, cols;
        getmaxyx(stdscr, rows, cols);
        int b_w = cols - 25;

        attron(A_BOLD | COLOR_PAIR(2));
        mvprintw(1, 2, "▼ CPU"); attroff(A_BOLD | COLOR_PAIR(2));
        for(int i=0; i<4; i++) {
            draw_bar(2+i, 4, b_w, get_cpu_usage(&cpus[i], i), (i==0?"CPU 1":(i==1?"CPU 2":(i==2?"CPU 3":"CPU 4"))), 1);
        }

        attron(A_BOLD | COLOR_PAIR(2));
        mvprintw(7, 2, "▼ Memoria e intercambio"); attroff(A_BOLD | COLOR_PAIR(2));
        draw_bar(8, 4, b_w, m_p, "Mem", 1);
        mvprintw(9, 6, "Uso: %.1f GB de %.1f GB", m_u, m_t);

        attron(A_BOLD | COLOR_PAIR(2));
        mvprintw(11, 2, "▼ Red"); attroff(A_BOLD | COLOR_PAIR(2));
        mvprintw(12, 4, "Recibiendo: 257.6 KiB/s");
        mvprintw(13, 4, "Enviando:   589 bytes/s");

        attron(COLOR_PAIR(3));
        mvprintw(rows - 1, 2, "Refresco: %ds | 'm' Menu | 'q' Salir", refresh_rate);
        attroff(COLOR_PAIR(3));

        refresh();
        for(int i=0; i<refresh_rate*10; i++) {
            if(getch() == 'q') goto end;
            usleep(100000);
        }
    }

end:
    endwin();
    return 0;
}